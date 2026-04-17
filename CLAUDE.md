# CLAUDE.md - AI Assistant Guidance

This file provides comprehensive guidance for AI assistants working with the httpcheck codebase.

## 🎯 Project Overview

**httpcheck** is a Python CLI tool for HTTP status code checking with advanced
features including threading, redirect handling, TLD validation, and macOS
integration.

- **Current Version**: 1.4.3 (RELEASED ✅)
- **Target Version**: 1.5.0 (Configuration and Monitoring)
- **Architecture**: Fully modular (11 specialized modules)
- **Code Quality**: Maintains pylint 10.0/10 score
- **Test Coverage**: 88% (exceeding 70% target)
- **Security Status**: No known vulnerabilities

## 🛠️ Development Environment

### Setup Commands
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install as package (recommended)
pip install -e .

# Install with optional dependencies
pip install -e ".[macos]"  # macOS notifications
pip install -e ".[dev]"    # Development tools

# macOS users: Install for notifications
brew install terminal-notifier
```

### Running the Application
```bash
# Package command (recommended)
httpcheck https://example.com

# Multiple sites from file
httpcheck @examples/domains.txt

# Fast mode with threading
httpcheck -f @examples/domains.txt

# New output formats
httpcheck --output json https://example.com
httpcheck --output csv @examples/domains.txt

# Custom headers and SSL options
httpcheck -H "User-Agent: MyBot/1.0" --no-verify-ssl https://example.com

# Legacy script usage (still supported)
python3 httpcheck.py https://example.com
```

### Code Quality Standards
```bash
# Run pylint (MUST pass with score 10.0)
pylint --fail-under=10.0 httpcheck.py httpcheck/*.py

# Run comprehensive test suite
pytest tests/ --cov=httpcheck --cov-report=html --cov-fail-under=70

# Security audit
pip-audit
```

## 🏗️ Architecture & Implementation Guide

### ✅ Current Modular Structure (v1.4.3 - IMPLEMENTED)
```
httpcheck/
├── __init__.py             # Package initialization and public API
├── cli.py                  # Argument parser and main entry point
├── common.py               # Shared constants, types, utilities
├── tld_manager.py          # TLD validation with JSON caching
├── file_handler.py         # File input with security validation
├── site_checker.py         # HTTP request handling and retry logic
├── async_site_checker.py   # Async I/O for high-concurrency checks (httpx)
├── output_formatter.py     # Multiple output formats (table/JSON/CSV)
├── notification.py         # System notifications (macOS/Linux)
├── logger.py               # Centralized logging system
└── validation.py           # Enhanced input validation & security
```

### Repository Organization
```
httpcheck/
├── httpcheck/           # Main package source code
├── tests/              # Comprehensive test suite (182 tests)
├── examples/           # Example configuration and domain files
├── docs/               # Documentation
│   ├── development/    # Development guides and plans
│   ├── releases/       # Release notes and completion reports
│   └── archive/        # Historical development summaries
├── scripts/            # Utility scripts
├── images/             # Logo and graphics
└── *.md               # Core documentation (README, TODO, etc.)
```

### 🔧 Critical Implementation Details

#### ✅ Security Issues RESOLVED
1. **✅ COMPLETED**: Replaced `pickle` with `json` for TLD cache (security vulnerability)
2. **✅ COMPLETED**: Audited all external dependencies (pip-audit clean)
3. **✅ COMPLETED**: Enhanced input validation system
4. **✅ COMPLETED**: SSL certificate validation options implemented

#### Key Design Patterns
- **Singleton**: TLDManager for efficient TLD list management
- **Threading**: ThreadPoolExecutor for parallel site checking
- **Factory**: Output formatters for different formats (table, JSON, CSV)
- **Strategy**: Different redirect handling modes

#### Network Features
1. **Redirect Handling**: Four modes (always, never, http-only, https-only)
2. **TLD Validation**: Downloads from publicsuffix.org, cached locally with JSON
3. **File Input**: Supports `#` and `//` comments, security validation
4. **Error Handling**: Network, DNS, SSL, and timeout exceptions with retries
5. **Output Formats**: table (default), JSON, CSV with verbose options
6. **Request Customization**: Custom headers, SSL verification control
7. **Security Features**: Input validation, injection protection, DoS limits

### 📦 Dependencies Management

#### Dependencies (Consolidated) ✅
All dependencies are managed through `pyproject.toml`:
```toml
[project]
dependencies = [
    "requests>=2.32.0",
    "tabulate>=0.9.0",
    "tqdm>=4.67.0",
]

[project.optional-dependencies]
macos = [
    "rumps>=0.4.0",
    "pyobjc-framework-Cocoa>=10.0",
    "pyobjc-framework-Foundation>=10.0",
    "pyobjc-framework-AppKit>=10.0",
    "pyobjc-core>=10.0"
]
dev = ["pytest>=7.0", "pytest-mock>=3.0", "pytest-cov>=4.0", "pylint>=3.1.0"]
build = ["py2app>=0.28"]
```

## ✅ Testing Framework (IMPLEMENTED)

### Test Framework Setup
```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest tests/ --cov=httpcheck --cov-report=html --cov-fail-under=70
```

### ✅ Test Structure (IMPLEMENTED)
```
tests/
├── __init__.py
├── test_async_site_checker.py   # Async I/O module tests
├── test_cli_integration.py      # CLI argument parsing and integration
├── test_common.py               # Common utilities tests
├── test_file_handler.py         # File input and validation tests
├── test_httpcheck.py            # Main script integration tests
├── test_init.py                 # Package initialization tests
├── test_output_formats.py       # Output format tests (JSON/CSV/table)
├── test_performance.py          # Performance regression tests
├── test_request_customization.py # Custom headers and SSL tests
├── test_site_checker.py         # HTTP checking and retry tests
├── test_tld_manager.py          # TLD validation tests
└── test_validation.py           # Security validation tests
```

### Test Coverage Status
- **13 test modules** covering all functionality
- **88% code coverage** (exceeding 70% target)
- **Mock-based testing** for reliable, fast execution
- **Security validation tests** for injection protection

### Mock Strategy
- Mock all network requests (`requests.Session.get`)
- Mock file system operations
- Mock macOS notification system
- Use fixtures for common test data

## 🎯 Development Workflow

### Before Starting Any Work
1. **Read** `docs/development/DEVELOPMENT_PLAN.md` for phase details
2. **Check** `TODO.md` for prioritized tasks
3. **Review** current git status and branch
4. **Ensure** pylint score remains 10.0/10
5. **Run tests** to ensure clean starting state

### Code Modification Guidelines
1. **Backward Compatibility**: Never break existing CLI interface
2. **Test Coverage**: Maintain >70% coverage, aim for >80%
3. **Security First**: All inputs must be validated
4. **Documentation**: Update docstrings and help text
5. **Type Hints**: Use type annotations for all new code
6. **Modular Design**: Keep modules focused and single-purpose

### Quality Checkpoints
```bash
# Before each commit
pylint --fail-under=10.0 httpcheck.py
python3 httpcheck.py --help  # Verify CLI works
python3 httpcheck.py google.com  # Basic smoke test

# During refactoring
python3 -m pytest tests/ -v  # All tests pass
python3 httpcheck.py -f @domains.txt  # Threading works
```

## 🚀 Next Steps Priority (v1.5.0 Development)

### ✅ v1.4.x COMPLETED (through v1.4.3, March 2026)
- ✅ **Full modular architecture** (11 modules)
- ✅ **Comprehensive testing** (13 test modules, 88% coverage)
- ✅ **Enhanced security** (input validation, audit clean)
- ✅ **New output formats** (JSON, CSV)
- ✅ **Advanced request features** (custom headers, SSL control)
- ✅ **Package installation** (`pip install -e .`)
- ✅ **Repository organization** (docs/, examples/, tests/)
- ✅ **Async I/O** (`async_site_checker.py` with httpx)
- ✅ **Centralized logging** (`logger.py`)
- ✅ **Modular CLI** (`cli.py` entry point)

### 🎯 v1.5.0 Roadmap (Next 3 months)
1. **Configuration File Support** - User-defined defaults (~/.httpcheck.toml)
2. **Monitoring Mode** - Continuous site monitoring
3. **Enhanced UX** - Colored output, progress improvements

Refer to `docs/development/DEVELOPMENT_PLAN.md` for detailed implementation plans.
