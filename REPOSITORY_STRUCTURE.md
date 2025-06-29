# Repository Structure Documentation

This document describes the organization and structure of the httpcheck repository after the v1.4.0 release cleanup and reorganization.

## 📁 Root Directory Structure

```
httpcheck/
├── 📂 .github/              # GitHub-specific configuration
├── 📂 docs/                 # Documentation
├── 📂 examples/             # Example files and configurations
├── 📂 httpcheck/            # Main Python package
├── 📂 images/               # Logo and graphics
├── 📂 scripts/              # Utility scripts
├── 📂 tests/                # Test suite
├── 📄 .gitignore           # Git ignore rules
├── 📄 .pre-commit-config.yaml # Pre-commit hooks
├── 📄 .pylintrc            # Pylint configuration
├── 📄 CHANGELOG.md         # Version history
├── 📄 CLAUDE.md            # AI assistant guidance
├── 📄 LICENSE              # MIT license
├── 📄 README.md            # Main project documentation
├── 📄 ROADMAP.md           # Project roadmap
├── 📄 TODO.md              # Current task list
├── 📄 httpcheck.py         # Main CLI script (legacy entry point)
├── 📄 pyproject.toml       # Modern Python packaging configuration
└── 📄 effective_tld_names.dat # TLD validation data (auto-generated)
```

## 📂 Detailed Directory Breakdown

### `/httpcheck/` - Main Package
```
httpcheck/
├── __init__.py           # Package initialization and public API
├── common.py             # Shared utilities and constants
├── file_handler.py       # File input with security validation
├── notification.py       # System notifications (macOS/Linux)
├── output_formatter.py   # Multiple output formats (table/JSON/CSV)
├── site_checker.py       # HTTP request handling and retry logic
├── tld_manager.py        # TLD validation with JSON caching
└── validation.py         # Enhanced input validation & security
```

**Purpose**: Core package modules implementing all httpcheck functionality.
**Entry Point**: `pip install -e .` makes `httpcheck` command available.

### `/tests/` - Test Suite
```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── test_common.py                 # Common utilities tests
├── test_file_handler.py           # File input and validation tests
├── test_httpcheck.py              # Main script integration tests
├── test_output_formats.py         # Output format tests (JSON/CSV/table)
├── test_request_customization.py  # Custom headers and SSL tests
├── test_site_checker.py           # HTTP checking and retry tests
└── test_validation.py             # Security validation tests
```

**Coverage**: 182 test cases with 84% code coverage
**Running Tests**: `pytest tests/ --cov=httpcheck --cov-report=html`

### `/docs/` - Documentation
```
docs/
├── development/           # Development guides
│   ├── DEVELOPMENT.md     # Technical implementation guide
│   ├── DEVELOPMENT_PLAN.md # Executive overview and timeline
│   ├── LOGGING.md         # Logging and debugging guide
│   └── TESTING.md         # Testing framework documentation
├── releases/              # Release documentation
│   ├── CRITICAL_ITEMS_COMPLETION.md # v1.4.0 completion report
│   └── RELEASE_NOTES_v1.4.0.md      # v1.4.0 release notes
└── archive/               # Historical documentation
    ├── PHASE3_WEEK7-8_SUMMARY.md
    ├── WEEK1_COMPLETION_SUMMARY.md
    ├── WEEK4_COMPLETION_SUMMARY.md
    └── WEEK9-10_REQUEST_CUSTOMIZATION_SUMMARY.md
```

**Organization**:
- `development/` - Current development guides and plans
- `releases/` - Release notes and completion reports
- `archive/` - Historical development summaries

### `/examples/` - Example Files
```
examples/
├── config_example.json   # Example configuration file structure
├── domains.txt           # Sample domain list
├── more_domains.txt      # Extended domain examples
└── test_domains.txt      # Test domains for validation
```

**Usage**:
- `httpcheck @examples/domains.txt` - Process domain list from file
- Reference configurations and sample inputs

### `/scripts/` - Utility Scripts
```
scripts/
└── start_menubar.sh      # macOS menu bar app launcher
```

**Purpose**: Helper scripts for development and deployment

### `/images/` - Graphics and Assets
```
images/
└── onSiteLogo.png        # Project logo
```

**Usage**: Logo for README and documentation

## 🔧 Configuration Files

### `.gitignore`
Excludes development artifacts, cache files, and build outputs:
- Python cache files (`__pycache__/`, `*.pyc`)
- Build artifacts (`build/`, `dist/`, `*.egg-info/`)
- Test and coverage reports (`htmlcov/`, `.coverage`)
- IDE files (`.vscode/`, `.idea/`)
- Virtual environments (`.venv/`, `venv/`)

### `pyproject.toml`
Modern Python packaging configuration:
- Project metadata and dependencies
- Build system configuration
- Tool configurations (pytest, pylint)
- Entry points for CLI commands

### `.pylintrc`
Code quality standards:
- Enforces 10.0/10 score requirement
- Consistent coding style
- Security and best practices checks

## 📋 File Organization Principles

### Core Documentation (Root Level)
- `README.md` - Main project overview
- `CHANGELOG.md` - Version history
- `TODO.md` - Current development tasks
- `ROADMAP.md` - Long-term project vision
- `CLAUDE.md` - AI assistant guidance

### Development Files
- Source code in `/httpcheck/`
- Tests in `/tests/`
- Documentation in `/docs/`
- Examples in `/examples/`

### Legacy Support
- `httpcheck.py` - Original script (still functional)
- Maintained for backward compatibility
- Redirects to package-based implementation

## 🚀 Usage Patterns

### Development Workflow
```bash
# Clone and setup
git clone <repository>
cd httpcheck
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ --cov=httpcheck

# Code quality check
pylint httpcheck.py httpcheck/*.py

# Use application
httpcheck --help
httpcheck @examples/domains.txt
```

### File Input Examples
```bash
# Use example files
httpcheck @examples/domains.txt
httpcheck -f @examples/test_domains.txt

# Custom file with comments
httpcheck @my_sites.txt --comment-style both
```

### Output Format Examples
```bash
# JSON output
httpcheck --output json @examples/domains.txt

# CSV for spreadsheet analysis
httpcheck --output csv @examples/domains.txt > results.csv
```

## 🎯 Best Practices

### Adding New Features
1. **Source Code**: Add to appropriate module in `/httpcheck/`
2. **Tests**: Create corresponding tests in `/tests/`
3. **Documentation**: Update relevant files in `/docs/`
4. **Examples**: Add usage examples to `/examples/` if needed

### Documentation Updates
1. **Development**: Add to `/docs/development/`
2. **Releases**: Document in `/docs/releases/`
3. **Historical**: Archive old docs in `/docs/archive/`

### File Naming Conventions
- **Code**: Snake_case for Python files
- **Documentation**: UPPERCASE.md for major docs
- **Examples**: Descriptive lowercase names
- **Tests**: `test_` prefix for all test files

## 🔍 Repository Health

### Automated Checks
- **CI/CD**: GitHub Actions for testing
- **Code Quality**: Pylint enforcement
- **Security**: Automated dependency scanning
- **Pre-commit**: Code formatting and validation

### Maintenance
- **Dependencies**: Regular updates via pip-audit
- **Tests**: Continuous coverage monitoring
- **Documentation**: Keep in sync with code changes
- **Examples**: Validate example files regularly

This organization supports the v1.4.0 modular architecture while maintaining clear separation of concerns and ease of navigation for developers and users.
