# Changelog

All notable changes to httpcheck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2025-06-27

### ✨ Added
- **Complete modular architecture**: Extracted 1,151-line monolithic file into 7 focused modules
- **httpcheck/ package structure** with proper separation of concerns:
  - `common.py`: Shared utilities, constants, and data structures
  - `tld_manager.py`: TLD validation with JSON caching system
  - `file_handler.py`: File input processing and URL validation
  - `site_checker.py`: Core HTTP checking functionality
  - `output_formatter.py`: Result formatting and display logic
  - `notification.py`: System notification handling
  - `__init__.py`: Package interface with backward compatibility
- **SiteStatus.final_url property** for better URL handling after redirects
- **Enhanced package imports** for better module accessibility

### 🔧 Changed
- **Maintained 100% backward compatibility** for CLI interface
- **Improved code organization** with clean module boundaries and minimal coupling
- **Enhanced test suite** to work with modular structure (52% coverage baseline)
- **Applied modern Python typing** using `list[T]` instead of `List[T]`
- **Applied consistent code formatting** via pre-commit hooks

### 🏗️ Technical Details
- All existing functionality preserved and rigorously tested
- Achieved pylint 10.0/10 score across all modules
- Foundation established for Phase 2 testing and quality improvements
- Proper error handling and comprehensive type hints maintained throughout

## [1.3.1] - 2025-06-27

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
