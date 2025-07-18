# Changelog

All notable changes to httpcheck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
