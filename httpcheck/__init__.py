"""
httpcheck - HTTP status code checker with advanced features.

A Python CLI tool for checking HTTP status codes of websites with
threading, redirect handling, TLD validation, and system notifications.
"""

__version__ = "1.4.0"
__author__ = "Thomas Juul Dyhr"
__email__ = "thomas@dyhr.com"

# Make modules available for import
from . import (
    common,
    file_handler,
    notification,
    output_formatter,
    site_checker,
    tld_manager,
)
from .common import VERSION, SiteStatus
from .file_handler import FileInputHandler, url_validation
from .notification import notify
from .output_formatter import print_format

# Import main functions for backward compatibility
from .site_checker import check_site
from .tld_manager import InvalidTLDException, TLDManager

__all__ = [
    "check_site",
    "print_format",
    "TLDManager",
    "InvalidTLDException",
    "FileInputHandler",
    "url_validation",
    "notify",
    "SiteStatus",
    "VERSION",
    "common",
    "file_handler",
    "site_checker",
    "output_formatter",
    "tld_manager",
    "notification",
]
