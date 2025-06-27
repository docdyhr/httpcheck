# Development Implementation Guide

## 🎯 Overview

This document provides detailed implementation guidance for developers working on httpcheck v1.4.0. It complements the high-level `DEVELOPMENT_PLAN.md` with specific technical instructions.

## 🚀 Phase 1: Foundation Stabilization (Weeks 1-3)

### Week 1: Security & Dependencies

#### Task 1.1: Replace Pickle with JSON (CRITICAL)
**Location**: `httpcheck.py` lines 600-800 (TLDManager class)

**Current Issue**:
```python
# SECURITY VULNERABILITY - httpcheck.py line ~650
with open(cache_file, 'wb') as f:
    pickle.dump(tld_data, f)
```

**Implementation**:
```python
# Replace with secure JSON caching
import json
from pathlib import Path

def _save_tld_cache(self, tld_data: set) -> None:
    """Save TLD data to JSON cache file."""
    cache_file = Path.home() / '.httpcheck_tld_cache.json'
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(list(tld_data), f, indent=2)
        self._cache_timestamp = time.time()
    except (OSError, json.JSONEncodeError) as e:
        print(f"Warning: Could not save TLD cache: {e}")

def _load_tld_cache(self) -> set:
    """Load TLD data from JSON cache file."""
    cache_file = Path.home() / '.httpcheck_tld_cache.json'
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            tld_list = json.load(f)
        return set(tld_list)
    except (OSError, json.JSONDecodeError, FileNotFoundError):
        return set()
```

#### Task 1.2: Consolidate Dependencies
**Goal**: Replace multiple requirements files with single `pyproject.toml`

**Current Files to Remove**:
- `requirements.txt`
- `requirements-core.txt`
- `requirements-macos.txt`

**New pyproject.toml**:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "httpcheck"
version = "1.4.0"
description = "HTTP status code checker with advanced features"
authors = [
    {name = "Thomas Juul Dyhr", email = "thomas@dyhr.com"},
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: System Administrators",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: System :: Monitoring",
    "Topic :: System :: Networking :: Monitoring",
]
dependencies = [
    "requests>=2.32.0",
    "tabulate>=0.9.0",
    "tqdm>=4.67.0",
]

[project.optional-dependencies]
macos = [
    "rumps>=0.4.0",
    "pyobjc-framework-Cocoa>=10.0",
]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.0",
    "pytest-cov>=4.0",
    "pylint>=3.1.0",
]

[project.urls]
"Homepage" = "https://github.com/docdyhr/httpcheck"
"Bug Tracker" = "https://github.com/docdyhr/httpcheck/issues"

[project.scripts]
httpcheck = "httpcheck:main"

[tool.pylint.main]
fail-under = 10.0

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
addopts = "--cov=httpcheck --cov-report=html --cov-report=term-missing --cov-fail-under=70"
```

#### Task 1.3: Dependency Audit
**Command**: `pip-audit` (install if needed)

**Check for**:
- Known security vulnerabilities
- Outdated packages with security patches
- Unused imports in code

### Week 2-3: Code Modularization

#### Module Extraction Order
1. `common.py` - Shared utilities (first, no dependencies)
2. `tld_manager.py` - TLD validation (depends on common)
3. `file_handler.py` - File processing (depends on common)
4. `site_checker.py` - HTTP logic (depends on common)
5. `output_formatter.py` - Result display (depends on common)
6. `notification.py` - System notifications (depends on common)

#### Task 2.1: Create Package Structure
```bash
mkdir httpcheck
touch httpcheck/__init__.py
```

**httpcheck/__init__.py**:
```python
"""
httpcheck - HTTP status code checker with advanced features.

A Python CLI tool for checking HTTP status codes of websites with
threading, redirect handling, TLD validation, and system notifications.
"""

__version__ = "1.4.0"
__author__ = "Thomas Juul Dyhr"
__email__ = "thomas@dyhr.com"

from .site_checker import check_site
from .output_formatter import print_format
from .tld_manager import TLDManager, InvalidTLDException
from .file_handler import FileInputHandler, url_validation
from .notification import notify
from .common import SiteStatus, VERSION

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
]
```

#### Task 2.2: Extract common.py
**Source**: httpcheck.py lines 30-100

```python
"""Common utilities and types for httpcheck."""

import json
from dataclasses import dataclass
from typing import List, Optional

VERSION = "1.4.0"

# HTTP status codes mapping
with open('http_status_codes.json', 'r') as f:
    STATUS_CODES = json.load(f)

@dataclass
class SiteStatus:
    """Represents the status of a website check."""
    domain: str
    status: str
    message: str
    response_time: float = 0.0
    redirect_chain: List[str] = None
    final_url: str = ""

    def __post_init__(self):
        if self.redirect_chain is None:
            self.redirect_chain = []

class InvalidTLDException(Exception):
    """Raised when a domain has an invalid TLD."""
    pass
```

#### Task 2.3: Extract tld_manager.py
**Source**: httpcheck.py lines 600-800

```python
"""TLD validation and management for httpcheck."""

import json
import time
from pathlib import Path
from typing import Set
import requests

class TLDManager:
    """Singleton class for managing TLD validation."""

    _instance = None
    _tld_list: Set[str] = set()
    _cache_timestamp: float = 0
    _cache_duration: int = 86400  # 24 hours

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._load_tld_list()
            self._initialized = True

    def _get_cache_file(self) -> Path:
        """Get the TLD cache file path."""
        return Path.home() / '.httpcheck_tld_cache.json'

    def _is_cache_valid(self) -> bool:
        """Check if the TLD cache is still valid."""
        if not self._tld_list:
            return False

        cache_age = time.time() - self._cache_timestamp
        return cache_age < self._cache_duration

    def _load_tld_cache(self) -> Set[str]:
        """Load TLD data from JSON cache file."""
        cache_file = self._get_cache_file()
        try:
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    tld_list = json.load(f)
                self._cache_timestamp = cache_file.stat().st_mtime
                return set(tld_list)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load TLD cache: {e}")
        return set()

    def _save_tld_cache(self, tld_data: Set[str]) -> None:
        """Save TLD data to JSON cache file."""
        cache_file = self._get_cache_file()
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(list(tld_data), f, indent=2)
            self._cache_timestamp = time.time()
        except (OSError, json.JSONEncodeError) as e:
            print(f"Warning: Could not save TLD cache: {e}")

    # ... rest of TLD manager implementation
```

## 🧪 Phase 2: Testing Framework (Weeks 4-6)

### Test Directory Structure
```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── test_common.py              # Test common utilities
├── test_tld_manager.py         # Test TLD validation
├── test_file_handler.py        # Test file processing
├── test_site_checker.py        # Test HTTP checking
├── test_output_formatter.py    # Test result formatting
├── test_notification.py        # Test notifications
├── test_integration.py         # End-to-end tests
└── fixtures/                   # Test data files
    ├── sample_domains.txt
    ├── invalid_domains.txt
    └── mock_responses.json
```

### Key Test Examples

#### conftest.py
```python
"""Shared test fixtures for httpcheck tests."""

import pytest
from unittest.mock import MagicMock
from httpcheck.common import SiteStatus

@pytest.fixture
def mock_response():
    """Mock HTTP response for testing."""
    response = MagicMock()
    response.status_code = 200
    response.url = "https://example.com"
    response.history = []
    response.elapsed.total_seconds.return_value = 0.5
    return response

@pytest.fixture
def sample_site_status():
    """Sample SiteStatus for testing."""
    return SiteStatus(
        domain="example.com",
        status="200",
        message="OK",
        response_time=0.5
    )
```

#### test_tld_manager.py
```python
"""Tests for TLD manager functionality."""

import pytest
from unittest.mock import patch, mock_open
from httpcheck.tld_manager import TLDManager

class TestTLDManager:
    """Test cases for TLD manager."""

    def test_singleton_pattern(self):
        """Test that TLDManager implements singleton pattern."""
        manager1 = TLDManager()
        manager2 = TLDManager()
        assert manager1 is manager2

    @patch("builtins.open", mock_open(read_data='["com", "org", "net"]'))
    def test_load_tld_cache(self):
        """Test loading TLD cache from JSON file."""
        manager = TLDManager()
        tld_set = manager._load_tld_cache()
        assert "com" in tld_set
        assert "org" in tld_set
        assert len(tld_set) == 3

    def test_invalid_tld_detection(self):
        """Test detection of invalid TLDs."""
        manager = TLDManager()
        # Test with mock TLD list
        manager._tld_list = {"com", "org", "net"}

        assert manager.is_valid_tld("example.com") is True
        assert manager.is_valid_tld("example.invalid") is False
```

## 🎯 Phase 3: Core Features (Weeks 7-10)

### JSON Output Implementation
**New CLI option**: `--output json`

```python
def format_json_output(results: List[SiteStatus]) -> str:
    """Format results as JSON."""
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_sites": len(results),
        "results": []
    }

    for result in results:
        output["results"].append({
            "domain": result.domain,
            "status": result.status,
            "message": result.message,
            "response_time": result.response_time,
            "final_url": result.final_url,
            "redirect_chain": result.redirect_chain
        })

    return json.dumps(output, indent=2)
```

### CSV Output Implementation
**New CLI option**: `--output csv`

```python
import csv
from io import StringIO

def format_csv_output(results: List[SiteStatus]) -> str:
    """Format results as CSV."""
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Domain", "Status", "Message", "Response Time",
        "Final URL", "Redirect Count"
    ])

    # Data rows
    for result in results:
        writer.writerow([
            result.domain,
            result.status,
            result.message,
            f"{result.response_time:.3f}",
            result.final_url,
            len(result.redirect_chain)
        ])

    return output.getvalue()
```

### Custom Headers Implementation
**New CLI option**: `-H, --header`

```python
def parse_headers(header_strings: List[str]) -> Dict[str, str]:
    """Parse header strings into dictionary."""
    headers = {}
    for header_str in header_strings:
        if ':' not in header_str:
            raise ValueError(f"Invalid header format: {header_str}")

        key, value = header_str.split(':', 1)
        headers[key.strip()] = value.strip()

    return headers

# Usage in site_checker.py
def check_site(url: str, custom_headers: Dict[str, str] = None) -> SiteStatus:
    """Check a single site with optional custom headers."""
    session = requests.Session()

    if custom_headers:
        session.headers.update(custom_headers)

    # ... rest of implementation
```

## 📊 Quality Assurance

### Pre-commit Checklist
```bash
# 1. Code quality
pylint --fail-under=10.0 httpcheck/

# 2. Type checking (if using mypy)
mypy httpcheck/

# 3. Tests
pytest tests/ -v

# 4. Coverage
pytest tests/ --cov=httpcheck --cov-fail-under=70

# 5. Smoke test
python3 -m httpcheck google.com
```

### Performance Benchmarks
Maintain performance during refactoring:

```bash
# Benchmark before refactoring
time python3 httpcheck.py @test_domains.txt

# Should not regress more than 10% after modularization
```

## 🔧 Migration Strategy

### Backward Compatibility Requirements
1. All existing CLI arguments must work unchanged
2. Output formats must remain identical (except new JSON/CSV)
3. File input format compatibility maintained
4. macOS notification behavior unchanged

### Rollback Plan
Each module extraction should be in a separate commit to allow selective rollback if issues arise.

### Testing During Migration
Run comprehensive tests after each module extraction:

```bash
# Test all CLI combinations
python3 httpcheck.py google.com
python3 httpcheck.py -v google.com
python3 httpcheck.py -q @domains.txt
python3 httpcheck.py -f @domains.txt
python3 httpcheck.py --tld google.com
```

This implementation guide ensures systematic, tested, and safe progression through the v1.4.0 development plan while maintaining code quality and backward compatibility.
