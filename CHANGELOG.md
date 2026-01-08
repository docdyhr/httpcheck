# Changelog

All notable changes to httpcheck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.2] - 2026-01-08

### 🎉 Major Enhancement Release: Enterprise-Grade Improvements

This release transforms httpcheck into an enterprise-ready tool with comprehensive testing, professional documentation, structured logging, and performance monitoring.

### ✨ Added

#### Structured Logging System
- **New `httpcheck/logger.py` module** - Centralized logging configuration
- **Three new CLI flags**:
  - `--debug` - Enable debug logging with detailed execution flow
  - `--log-file FILE` - Write logs to file for monitoring and auditing
  - `--log-json` - Output logs in JSON format for ELK/Splunk integration
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **File logging support** - Write logs to disk for production monitoring
- **JSON logging format** - Machine-readable logs for aggregation systems
- **Quiet mode enhancement** - Now properly filters logs (ERROR+ only)

#### Comprehensive Testing
- **87 new CLI integration tests** - Complete coverage of CLI module
- **18 performance benchmark tests** - Baseline metrics for regression detection
- **3 performance threshold tests** - Automated performance gates for CI
- Test coverage increased from 73% to **88%**
- CLI module coverage increased from 22% to **94%**
- Total test count: 192 → **297 tests** (+105 tests, +55%)

#### Professional Documentation (Sphinx)
- **24 HTML documentation pages** with ReadTheDocs theme
- **Installation guide** - Multiple installation methods
- **Quick start tutorial** - Get started in 5 minutes
- **Complete usage guide** - Every CLI option documented with examples
- **15+ real-world examples**:
  - Basic health checks
  - Monitoring cron jobs
  - CI/CD integration (GitHub Actions, GitLab CI, Kubernetes)
  - Docker and Docker Compose deployments
  - Python API usage with code examples
  - Email alerting and database logging
- **Complete API reference** - Auto-generated from docstrings
- **Contributing guide** - Development setup and code standards
- **Search functionality** - Built-in documentation search

#### Performance Monitoring
- **pytest-benchmark integration** - Automated performance testing
- **Performance baselines established**:
  - URL validation: ~6μs (170,000 ops/sec)
  - Single site check: ~44μs (22,800 ops/sec)
  - File parsing: 85,700 URLs/sec
  - JSON output: 3,300 ops/sec
  - CSV output: 7,400 ops/sec
- **CI-ready threshold tests** - Fail build on performance regressions

### 🔧 Changed
- **Replaced all print() statements with structured logging** (13 → 0)
- **Enhanced error messages** with proper log levels
- **Improved CLI module organization** for better maintainability
- **Updated pyproject.toml** with pytest-benchmark dependency

### 📦 Package Improvements
- **Distribution packages built and validated**:
  - Source distribution: `httpcheck-1.4.2.tar.gz`
  - Wheel distribution: `httpcheck-1.4.2-py3-none-any.whl`
- **Ready for PyPI publication**
- **Documentation ready for ReadTheDocs hosting**

### 🎯 Quality Metrics
- **Test Coverage**: 88% (exceeds 70% target by 18%)
- **CLI Coverage**: 94% (exceeds 80% target by 14%)
- **Pylint Score**: 10.0/10 (maintained)
- **Security**: pip-audit clean (no vulnerabilities)
- **Total Tests**: 297 (from 192)
- **Documentation Pages**: 24 HTML pages

### 💡 Developer Experience
- **Complete API documentation** for library usage
- **Performance benchmarks** to prevent regressions
- **Contributing guide** with development workflow
- **Real-world examples** for common scenarios
- **CI-ready tests** for automated validation

### 🚀 Production Ready
This release makes httpcheck suitable for:
- **Enterprise monitoring** - Structured logging and alerting
- **DevOps automation** - CI/CD integration examples
- **Library usage** - Complete API documentation
- **Performance-critical applications** - Benchmarked and optimized

### 📝 Documentation
- Available at: `docs/_build/html/index.html`
- Ready for ReadTheDocs.io hosting
- Complete with search functionality
- Mobile-responsive design

---

## [1.4.1] - 2025-01-12

### 🔒 Security
- **CRITICAL**: Updated `requests` from 2.32.0 to 2.32.5 (fixes GHSA-9hjg-9r4m-mvj7)
- **CRITICAL**: Updated `urllib3` from 2.2.2 to 2.5.0 (fixes 2 security vulnerabilities)
- Updated `pip` to 25.3 (fixes GHSA-4xh5-x5gv-qwph)

### 🔧 Changed
- **Refactored main() entry point** - Moved from subprocess call to proper package function
  - Created new `httpcheck/cli.py` module with all CLI logic
  - Package now imports `main()` directly from `cli` module
  - Eliminates fragile subprocess dependency and improves performance
  - Maintains backward compatibility with existing `httpcheck.py` script
- **Improved package structure** - CLI logic now properly integrated into package

### ✨ Added
- **Type checking support** - Added mypy configuration to `pyproject.toml`
- **Pytest configuration** - Fixed asyncio deprecation warning with proper config

### 📦 Package Structure
- New `httpcheck/cli.py` - Complete CLI implementation (534 lines)
- Updated `httpcheck/__init__.py` - Now imports main from cli module
- Maintained `httpcheck.py` - Backward compatibility wrapper

## [1.4.0] - 2025-01-16

### 🎉 Major Release: Complete Architecture Modernization

This release transforms httpcheck from a monolithic script into a robust, modular Python package while maintaining 100% backward compatibility.

### ✨ Added
- **Complete modular architecture** - 8 specialized modules extracted from monolithic script
- **Comprehensive test suite** - 182 tests with 84% coverage
- **JSON and CSV output formats** - `--output json/csv` options
- **Custom HTTP headers** - `-H "Header: Value"` support (multiple allowed)
- **SSL verification control** - `--no-verify-ssl` option
- **Enhanced security validation** - Enterprise-grade input validation system
- **Package installation** - Proper Python package with `pip install -e .`

### 🔧 Changed
- **Architecture** - Reduced complexity from 1,151 lines to 807 lines across 8 modules
- **TLD caching** - Migrated from pickle to JSON for security
- **File processing** - Enhanced with size limits and injection protection
- **Error handling** - Improved error messages and retry logic

### 🔒 Security
- Fixed pickle deserialization vulnerability in TLD cache
- Added comprehensive input validation to prevent XSS and injection attacks
- Implemented DoS protection with file size and processing limits
- All dependencies audited with pip-audit (no vulnerabilities)

### 📦 Package Structure
- `httpcheck/__init__.py` - Package initialization and public API
- `httpcheck/common.py` - Shared utilities and constants
- `httpcheck/tld_manager.py` - TLD validation with JSON caching
- `httpcheck/file_handler.py` - File input with security validation
- `httpcheck/site_checker.py` - HTTP request handling and retry logic
- `httpcheck/output_formatter.py` - Multiple output formats
- `httpcheck/notification.py` - System notifications
- `httpcheck/validation.py` - Enhanced input validation & security

## [1.3.1] - 2024-06-27

### 🔒 Security
- **CRITICAL**: Replaced pickle with JSON for TLD cache serialization to eliminate security vulnerability
- Fixed potential code injection risk in cache deserialization

### ✨ Added
- Comprehensive unit test suite with pytest framework
- Basic test coverage for core functionality (URL validation, file parsing, TLD management)
- Modern `pyproject.toml` configuration with proper dependency management
- Separate optional dependency groups for macOS, development, and build tools

### 🔧 Changed
- **BREAKING**: TLD cache format changed from pickle (`.pickle`) to JSON (`.json`)
  - Existing pickle cache files will be automatically refreshed with JSON format
  - No user action required - migration is automatic
- Consolidated fragmented requirements files into clean dependency structure
- Improved error handling for JSON cache operations

### 🗑️ Removed
- Removed unused development dependencies from core requirements
- Eliminated redundant and outdated package versions
- Cleaned up duplicate and unnecessary imports

### 📦 Dependencies
**Runtime Dependencies (minimized):**
- `requests>=2.32.0` - HTTP client library
- `tabulate>=0.9.0` - Table formatting
- `tqdm>=4.67.0` - Progress bars

**Optional Dependencies:**
- `macos`: macOS menu bar app support (rumps, pyobjc-*)
- `dev`: Development tools (pytest, pylint, coverage)
- `build`: Build tools for macOS app (py2app)

### 🧪 Testing
- Added comprehensive test suite covering:
  - URL validation and normalization
  - File input parsing with comments
  - TLD cache management and JSON format
  - HTTP request mocking and error handling
  - Output formatting in different modes
- Configured pytest with coverage reporting (target >70%)

### 📚 Documentation
- Updated project documentation to reflect security improvements
- Added development workflow documentation
- Created comprehensive development plan for v1.4.0 refactoring
- Enhanced AI assistant guidance with current priorities

### 🏗️ Development
- Maintained pylint score of 10.0/10 throughout refactoring
- Established foundation for upcoming v1.4.0 modularization
- Improved code organization without breaking changes
- Enhanced error handling and user feedback

### 🔄 Migration Notes
- **TLD Cache**: Users with existing `.httpcheck/tld_cache.pickle` files will see automatic migration to `tld_cache.json` format on first run
- **Dependencies**: Users should update their installation:
  ```bash
  # For core functionality
  pip install httpcheck

  # For macOS menu bar app
  pip install httpcheck[macos]

  # For development
  pip install httpcheck[dev]
  ```

---

## [1.3.0] - 2025-04-29

### Added
- macOS menu bar application (onSite)
- Advanced redirect handling with multiple modes
- Comprehensive TLD validation with caching
- Threading support for parallel site checking
- File input with comment support
- Progress bars for multiple site checks
- Enhanced error handling and retry logic

### Changed
- Improved CLI argument structure
- Better output formatting options
- Enhanced notification system for macOS

---

## Previous Versions

See git history for changes in versions 1.0.0 through 1.2.x.

### Development Status

**Current**: v1.3.1 (Security and stability improvements)
**Next**: v1.4.0 (Major refactoring - modular architecture)
**Timeline**: See [ROADMAP.md](ROADMAP.md) for detailed development plan

For detailed development information, see:
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - Executive overview
- [DEVELOPMENT.md](DEVELOPMENT.md) - Technical implementation guide
- [TODO.md](TODO.md) - Current task priorities
- [ROADMAP.md](ROADMAP.md) - Long-term vision
