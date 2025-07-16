"""
httpcheck - HTTP status code checker with advanced features.

A Python CLI tool for checking HTTP status codes of websites with
threading, redirect handling, TLD validation, and system notifications.
"""

__version__ = "1.4.0"
__author__ = "Thomas Juul Dyhr"
__email__ = "thomas@dyhr.com"

# Import specific items for public API
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


def main():
    """Main entry point for the httpcheck package."""
    import os
    import subprocess
    import sys

    # Get the directory containing this package
    package_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(package_dir)

    # Path to the main httpcheck.py script
    httpcheck_script = os.path.join(parent_dir, "httpcheck.py")

    if os.path.exists(httpcheck_script):
        # Run the script directly with subprocess to avoid import conflicts
        result = subprocess.run(
            [sys.executable, httpcheck_script] + sys.argv[1:], check=False, shell=False
        )
        sys.exit(result.returncode)
    else:
        print("Error: Could not find httpcheck main script", file=sys.stderr)
        sys.exit(1)
