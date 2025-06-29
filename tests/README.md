# httpcheck Test Suite

## Overview

The httpcheck test suite provides comprehensive coverage of all modules with 89.36% code coverage. Tests are organized by module for maintainability and clarity.

## Test Files

- `test_httpcheck.py` - Original test file containing legacy tests
- `test_common.py` - Tests for common utilities and data structures (11 tests)
- `test_file_handler.py` - Tests for file input handling and URL validation (18 tests)
- `test_site_checker.py` - Tests for HTTP checking functionality (20 tests)

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=httpcheck --cov-report=term-missing

# Run specific test file
pytest tests/test_file_handler.py

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Coverage Report
```
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
httpcheck/__init__.py              10      0   100%
httpcheck/common.py                20      0   100%
httpcheck/file_handler.py          71      2    97%   122-123
httpcheck/notification.py          25      0   100%
httpcheck/output_formatter.py      25      0   100%
httpcheck/site_checker.py          70      1    99%   159
httpcheck/tld_manager.py          136     35    74%   83, 92, 100, 112, 117-120, 133-137, 142, 165-167, 171, 182, 185-207, 234, 241
-------------------------------------------------------------
TOTAL                             357     38    89%
```

## Test Organization

### test_common.py
Tests for the common module including:
- SiteStatus data structure
- InvalidTLDException
- Module constants and exports

### test_file_handler.py
Tests for file input handling:
- URL validation with various formats
- File parsing with different comment styles
- Error handling for invalid inputs
- Edge cases (empty files, special characters)

### test_site_checker.py
Tests for HTTP checking functionality:
- Successful site checks
- Timeout and retry logic
- Redirect handling (always, never, http-only, https-only)
- Error scenarios (connection, timeout, HTTP errors)
- SSL error handling

## Writing New Tests

### Test Structure
```python
class TestFeatureName:
    """Test cases for specific feature."""

    def test_normal_case(self):
        """Test normal expected behavior."""
        result = function_under_test("input")
        assert result == "expected output"

    def test_edge_case(self):
        """Test edge cases and error conditions."""
        with pytest.raises(ExpectedException):
            function_under_test("invalid input")
```

### Mocking Guidelines
- Mock external dependencies (network calls, file I/O)
- Use `unittest.mock.patch` for dependency injection
- Ensure mocks have required attributes (e.g., `response.history = []`)

### Best Practices
1. One test per behavior
2. Descriptive test names
3. Arrange-Act-Assert pattern
4. Use temporary files for file operations
5. Mock datetime for time-dependent tests

## Known Issues and Limitations

### Coverage Gaps
- TLD manager update/download logic (requires network mocking)
- Some defensive code paths that are hard to trigger
- Platform-specific notification code

### Test Improvements Needed
1. Integration tests for full CLI workflows
2. Performance benchmarks
3. Property-based testing for URL validation
4. More comprehensive TLD manager testing

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Maintain or improve coverage
3. Follow existing test patterns
4. Update this README if needed

## CI/CD Integration

Tests run automatically on:
- Push to main branch
- Pull requests
- Weekly scheduled runs

GitHub Actions configuration ensures all tests pass before merging.
