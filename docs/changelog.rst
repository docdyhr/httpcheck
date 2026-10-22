Changelog
=========

All notable changes to httpcheck are documented here. This page is a summary;
`CHANGELOG.md <https://github.com/docdyhr/httpcheck/blob/main/CHANGELOG.md>`_ in
the repository is the complete, authoritative list.

[1.5.1] - 2026-10-22
--------------------

Security
~~~~~~~~
- Installing httpcheck now requires patched versions of five packages that
  ``requests`` and ``httpx`` pull in: ``urllib3>=2.8.0``, ``certifi>=2026.10.19``,
  ``idna>=3.15``, ``anyio>=4.14.2`` and ``h11>=0.16.0``. An install into an
  existing environment can no longer keep vulnerable versions. No behaviour
  changes

[1.5.0] - 2026-10-17
--------------------

Added
~~~~~
- Configuration file support: ``~/.httpcheck.toml`` (user) and ``./.httpcheck.toml``
  (project). Defaults for timeout, retries, follow_redirects, output_format,
  verify_ssl, workers, retry_delay, max_redirects and custom headers. The project
  file overrides the user file; command-line flags always take precedence
- ``load_config()`` and ``DEFAULT_CONFIG`` are part of the public API
- Experimental ``--async`` mode using the httpx async client (cannot be combined
  with ``--fast``). In the benchmark it is not faster than ``-f`` at the same
  ``--workers``
- Python 3.13 and 3.14 support

Changed
~~~~~~~
- A site with no parseable hostname now reports the input as its domain instead of
  ``None``
- README and help text no longer claim a speedup for ``--async``

Fixed
~~~~~
- With ``--follow-redirects http-only`` or ``https-only``, retries now work. 1.4.3
  reported the site as failed without retrying
- TLD cache handling is sturdier: cache, local file and network fallbacks, and
  saving no longer fails when no update time is set

Removed
~~~~~~~
- **Python 3.9 support**: ``requires-python`` is now ``>=3.10``. pip on Python 3.9
  keeps installing 1.4.3

[1.4.3] - 2026-03-09
--------------------

Fixed
~~~~~
- Version bump to republish to PyPI after an environment policy update
- CI/CD pipeline: manual dispatch support and scoped security scanning

[1.4.2] - 2026-01-08
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
