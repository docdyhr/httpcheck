Changelog
=========

All notable changes to httpcheck are documented here.

[1.4.2] - Unreleased
--------------------

Added
~~~~~
- Structured logging system with debug, file, and JSON output
- New ``--debug`` flag for verbose logging
- New ``--log-file`` option to write logs to file
- New ``--log-json`` option for JSON-formatted logs
- Comprehensive CLI integration tests (87 new tests)

Changed
~~~~~~~
- Replaced all print() statements with structured logging
- Improved error messages with proper log levels
- Enhanced CLI module with better organization

Fixed
~~~~~
- Improved test coverage from 73% to 88%
- CLI module coverage increased from 22% to 94%

[1.4.1] - 2025-01-12
--------------------

Security
~~~~~~~~
- **CRITICAL**: Updated ``requests`` from 2.32.0 to 2.32.5
- **CRITICAL**: Updated ``urllib3`` from 2.2.2 to 2.5.0
- Updated ``pip`` to 25.3

Changed
~~~~~~~
- Refactored main() entry point - moved to proper package function
- Created new ``httpcheck/cli.py`` module with all CLI logic
- Improved package structure - CLI logic properly integrated
- Eliminated subprocess dependency

Added
~~~~~
- Type checking support with mypy configuration
- Pytest asyncio configuration fixes

[1.4.0] - 2025-01-16
--------------------

This major release transforms httpcheck from a monolithic script into a robust, modular Python package.

Added
~~~~~
- Complete modular architecture with 8 specialized modules
- Comprehensive test suite with 182 tests (84% coverage)
- JSON and CSV output formats (``--output json/csv``)
- Custom HTTP headers (``-H "Header: Value"``)
- SSL verification control (``--no-verify-ssl``)
- Enhanced security validation system
- Package installation via ``pip install -e .``

Changed
~~~~~~~
- Architecture: Reduced from 1,151 lines to 807 lines across 8 modules
- TLD caching: Migrated from pickle to JSON for security
- File processing: Enhanced with size limits and injection protection
- Error handling: Improved messages and retry logic

Security
~~~~~~~~
- Fixed pickle deserialization vulnerability in TLD cache
- Added comprehensive input validation (XSS, injection prevention)
- Implemented DoS protection with file size limits
- All dependencies audited (pip-audit clean)

Package Structure
~~~~~~~~~~~~~~~~~
- ``httpcheck/__init__.py`` - Package initialization
- ``httpcheck/common.py`` - Shared utilities
- ``httpcheck/tld_manager.py`` - TLD validation
- ``httpcheck/file_handler.py`` - File input processing
- ``httpcheck/site_checker.py`` - HTTP request handling
- ``httpcheck/output_formatter.py`` - Multiple output formats
- ``httpcheck/notification.py`` - System notifications
- ``httpcheck/validation.py`` - Input validation

[1.3.1] - 2024-06-27
--------------------

Security
~~~~~~~~
- **CRITICAL**: Replaced pickle with JSON for TLD cache
- Fixed potential code injection risk

Added
~~~~~
- Comprehensive unit test suite with pytest
- Modern ``pyproject.toml`` configuration
- Separate optional dependency groups

Changed
~~~~~~~
- **BREAKING**: TLD cache format changed from pickle to JSON
- Consolidated requirements into clean dependency structure
- Improved error handling for JSON cache operations

Removed
~~~~~~~
- Unused development dependencies
- Redundant package versions
- Duplicate imports

[1.3.0] - 2024-06-15
--------------------

Added
~~~~~
- Fast mode with threading support
- Progress bars for long-running checks
- Retry logic with configurable delays
- Enhanced redirect handling modes

Changed
~~~~~~~
- Improved performance for large site lists
- Better error messages
- Updated dependencies

[1.2.0] - 2024-05-20
--------------------

Added
~~~~~
- TLD validation against publicsuffix.org
- File input support with @ prefix
- Comment support in input files
- Verbose mode option

[1.1.0] - 2024-04-10
--------------------

Added
~~~~~
- Redirect following support
- Timeout configuration
- Basic error handling

[1.0.0] - 2024-03-01
--------------------

Initial release

- Basic HTTP status code checking
- Multiple site support
- Simple CLI interface
