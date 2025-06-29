# Testing Guide for httpcheck

## Overview

This document provides comprehensive guidance for testing the httpcheck project. The test suite ensures code quality, prevents regressions, and validates functionality across all modules.

## Test Structure

```
tests/
├── __init__.py
├── test_httpcheck.py          # Original test file (legacy)
├── test_common.py             # Tests for common utilities
├── test_file_handler.py       # Tests for file input handling
└── test_site_checker.py       # Tests for HTTP checking functionality
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=httpcheck --cov-report=term-missing

# Run specific test file
pytest tests/test_file_handler.py

# Run specific test class or method
pytest tests/test_file_handler.py::TestURLValidation
pytest tests/test_file_handler.py::TestURLValidation::test_url_validation_valid_urls

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

### Coverage Requirements
- **Minimum Coverage**: 70%
- **Current Coverage**: 89.36%
- **Target Coverage**: 90%+

## Writing Tests

### Test Organization

1. **One test file per module**: Each module in `httpcheck/` should have a corresponding test file
2. **Use test classes**: Group related tests in classes for better organization
3. **Clear naming**: Use descriptive test names that explain what is being tested

### Test Structure Example

```python
"""Test cases for the module_name module."""

import pytest
from unittest.mock import Mock, patch

from httpcheck.module_name import function_to_test


class TestFunctionName:
    """Test cases for function_to_test."""

    def test_normal_behavior(self):
        """Test function with normal inputs."""
        result = function_to_test("normal input")
        assert result == "expected output"

    def test_edge_case(self):
        """Test function with edge case inputs."""
        with pytest.raises(ValueError):
            function_to_test("invalid input")

    def test_with_mock(self):
        """Test function with mocked dependencies."""
        with patch('httpcheck.module_name.dependency') as mock_dep:
            mock_dep.return_value = "mocked value"
            result = function_to_test("input")
            assert result == "expected with mock"
            mock_dep.assert_called_once_with("input")
```

### Testing Best Practices

1. **Test One Thing**: Each test should verify a single behavior
2. **Use Descriptive Names**: Test names should explain what they test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use Fixtures**: For reusable test data
5. **Mock External Dependencies**: Don't make real network calls or file I/O
6. **Test Edge Cases**: Empty inputs, None values, extreme values
7. **Test Error Conditions**: Ensure proper error handling

## Module-Specific Testing Guidelines

### Testing `common.py`
- Test data structures (SiteStatus)
- Test exception classes
- Verify constants and enums
- Test property methods

### Testing `file_handler.py`
- Use temporary files for testing
- Test various file formats and encodings
- Test comment parsing modes
- Verify error handling for missing/invalid files
- Test URL validation regex patterns

### Testing `site_checker.py`
- Mock `requests.Session` for HTTP calls
- Test all redirect modes (always, never, http-only, https-only)
- Mock datetime for timing tests
- Test retry logic with failures
- Test various HTTP status codes

### Testing `tld_manager.py`
- Mock file I/O for cache operations
- Mock network calls for TLD updates
- Test singleton pattern
- Test cache expiration logic
- Mock datetime for time-based tests

### Testing `notification.py`
- Mock subprocess calls
- Test platform detection
- Mock system commands (terminal-notifier)
- Test error handling

### Testing `output_formatter.py`
- Capture stdout for output testing
- Test all output formats (normal, quiet, verbose, code-only)
- Test with various SiteStatus inputs
- Verify table formatting

## Common Test Patterns

### Mocking HTTP Requests
```python
with patch('httpcheck.site_checker.requests.Session') as mock_session_class:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.history = []

    mock_session = Mock()
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session

    result = check_site("https://example.com")
    assert result.status == "200"
```

### Testing File Operations
```python
import tempfile

def test_file_parsing():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("example.com\n")
        f.write("google.com\n")
        temp_path = f.name

    try:
        handler = FileInputHandler(temp_path)
        results = list(handler.parse())
        assert len(results) == 2
    finally:
        Path(temp_path).unlink()
```

### Mocking Datetime
```python
with patch('httpcheck.module_name.datetime') as mock_datetime:
    mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)
    result = function_with_timing()
    assert result.timestamp == "2024-01-01 10:00:00"
```

### Capturing Output
```python
from unittest.mock import patch

def test_output():
    with patch('builtins.print') as mock_print:
        function_that_prints("input")
        mock_print.assert_called_with("expected output")
```

## Coverage Analysis

### Understanding Coverage Reports

```
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
httpcheck/__init__.py              10      0   100%
httpcheck/common.py                20      0   100%
httpcheck/file_handler.py          71      2    97%   122-123
```

- **Stmts**: Total number of executable statements
- **Miss**: Number of statements not executed by tests
- **Cover**: Percentage of statements covered
- **Missing**: Line numbers of uncovered statements

### Improving Coverage

1. **Identify gaps**: Look at the "Missing" column
2. **Understand why**: Some code may be defensive or unreachable
3. **Add targeted tests**: Write tests for uncovered scenarios
4. **Mock difficult cases**: For network errors, timeouts, etc.

## Test Data

### Sample Test Files

Create reusable test data in `tests/fixtures/`:
- `valid_domains.txt`: List of valid domains
- `invalid_urls.txt`: Invalid URL examples
- `mixed_comments.txt`: File with various comment styles

### Test Constants

Define in test files:
```python
VALID_URLS = [
    "http://example.com",
    "https://example.com",
    "http://subdomain.example.com",
]

INVALID_URLS = [
    "not a url",
    "http://",
    "",
]
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to main/master branch
- Pull requests
- Scheduled (weekly security scans)

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

This runs tests before each commit.

## Debugging Tests

### Common Issues

1. **Import Errors**: Ensure httpcheck is installed in editable mode: `pip install -e .`
2. **Mock Not Working**: Check mock patch path matches actual import
3. **Flaky Tests**: Look for time-dependent or order-dependent code
4. **Coverage Not Updating**: Delete `.coverage` file and re-run

### Debugging Commands

```bash
# Run with pdb on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Run specific test with full output
pytest -vvs tests/test_file.py::test_name

# Generate HTML coverage report
pytest --cov=httpcheck --cov-report=html
open htmlcov/index.html
```

## Performance Testing

### Basic Benchmarking
```python
import time

def test_performance():
    start = time.time()
    result = function_to_test(large_input)
    duration = time.time() - start
    assert duration < 1.0  # Should complete in under 1 second
```

### Using pytest-benchmark
```bash
pip install pytest-benchmark
```

```python
def test_performance(benchmark):
    result = benchmark(function_to_test, "input")
    assert result == "expected"
```

## Future Testing Improvements

1. **Property-based testing**: Use hypothesis for fuzzing
2. **Integration tests**: Test full CLI workflows
3. **Performance benchmarks**: Track performance over time
4. **Mutation testing**: Verify test effectiveness
5. **Contract testing**: For API compatibility

## Contributing Tests

When adding new features:
1. Write tests first (TDD)
2. Ensure all edge cases are covered
3. Update this documentation
4. Maintain or improve coverage
5. Follow existing patterns

## Test Review Checklist

- [ ] Tests pass locally
- [ ] Coverage meets minimum (70%)
- [ ] No hardcoded paths or values
- [ ] Mocks are properly configured
- [ ] Tests are independent (no shared state)
- [ ] Edge cases are tested
- [ ] Error conditions are tested
- [ ] Documentation is updated
