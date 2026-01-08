API Overview
============

The httpcheck package provides a modular architecture with well-defined components for HTTP status checking.

Package Structure
-----------------

.. code-block:: text

   httpcheck/
   ├── __init__.py           # Package initialization and public API
   ├── cli.py                # Command-line interface
   ├── common.py             # Shared constants and types
   ├── file_handler.py       # File input processing
   ├── logger.py             # Logging configuration
   ├── notification.py       # System notifications
   ├── output_formatter.py   # Output formatting (table/JSON/CSV)
   ├── site_checker.py       # HTTP request handling
   ├── tld_manager.py        # TLD validation
   └── validation.py         # Input validation and security

Public API
----------

The main entry point for programmatic usage:

.. code-block:: python

   from httpcheck import main, check_site
   from httpcheck.common import SiteStatus

   # Check a site programmatically
   status = check_site("https://example.com")
   print(f"{status.domain}: {status.status}")

Module Documentation
--------------------

Core Modules
~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2

   cli
   core
   utilities

CLI Module
~~~~~~~~~~

The :mod:`httpcheck.cli` module provides the command-line interface.

Core Modules
~~~~~~~~~~~~

* :mod:`httpcheck.site_checker` - HTTP request handling and retry logic
* :mod:`httpcheck.common` - Shared types, constants, and utilities
* :mod:`httpcheck.logger` - Structured logging system

Utility Modules
~~~~~~~~~~~~~~~

* :mod:`httpcheck.file_handler` - File input with security validation
* :mod:`httpcheck.output_formatter` - Multiple output format support
* :mod:`httpcheck.tld_manager` - TLD validation with caching
* :mod:`httpcheck.validation` - Input validation and security
* :mod:`httpcheck.notification` - System notification support

Usage Examples
--------------

Programmatic Usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from httpcheck.site_checker import check_site

   # Basic usage
   status = check_site("https://google.com")
   print(f"Status: {status.status}")
   print(f"Response time: {status.response_time}s")

   # With custom options
   status = check_site(
       "https://example.com",
       timeout=10.0,
       retries=3,
       follow_redirects="always",
       custom_headers={"User-Agent": "MyBot/1.0"}
   )

File Processing
~~~~~~~~~~~~~~~

.. code-block:: python

   from httpcheck.file_handler import FileInputHandler

   handler = FileInputHandler("domains.txt", verbose=True)
   urls = list(handler.parse())

   for url in urls:
       print(url)

Output Formatting
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from httpcheck.output_formatter import format_json_list, format_csv_list
   from httpcheck.site_checker import check_site

   # Collect results
   results = [check_site(url) for url in ["google.com", "github.com"]]

   # Format as JSON
   json_output = format_json_list(results, verbose=True)
   print(json_output)

   # Format as CSV
   csv_output = format_csv_list(results, verbose=False)
   print(csv_output)

Logging Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from httpcheck.logger import setup_logger
   import logging

   # Configure logging
   logger = setup_logger(
       level=logging.DEBUG,
       log_file="/var/log/httpcheck.log",
       json_format=True
   )

   logger.info("Starting HTTP checks")
   logger.debug("Debug information")
