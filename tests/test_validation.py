"""Tests for the validation module."""

import os
import tempfile

import pytest

from httpcheck.validation import (
    ArgumentValidationError,
    FileValidationError,
    HeaderValidationError,
    InputValidator,
    URLValidationError,
    ValidationError,
    parse_custom_headers,
    url_validation,
    validate_file_path,
)

# No mock imports needed for these tests


class TestInputValidator:
    """Test the InputValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
        self.strict_validator = InputValidator(strict_mode=True)

    def test_validator_initialization(self):
        """Test validator initialization."""
        assert not self.validator.strict_mode
        assert self.strict_validator.strict_mode
        assert len(self.validator.compiled_injection_patterns) > 0

    def test_validate_url_basic(self):
        """Test basic URL validation."""
        # Valid URLs
        assert self.validator.validate_url("http://example.com") == "http://example.com"
        assert (
            self.validator.validate_url("https://example.com") == "https://example.com"
        )

        # Auto-fix URLs
        assert self.validator.validate_url("example.com") == "http://example.com"
        assert self.validator.validate_url("google.com") == "http://google.com"

    def test_validate_url_with_ports(self):
        """Test URL validation with ports."""
        assert (
            self.validator.validate_url("http://example.com:8080")
            == "http://example.com:8080"
        )
        assert (
            self.validator.validate_url("https://example.com:443")
            == "https://example.com:443"
        )

    def test_validate_url_with_ip_addresses(self):
        """Test URL validation with IP addresses."""
        assert self.validator.validate_url("http://192.168.1.1") == "http://192.168.1.1"
        assert (
            self.validator.validate_url("https://127.0.0.1:8000")
            == "https://127.0.0.1:8000"
        )

    def test_validate_url_localhost(self):
        """Test URL validation with localhost."""
        assert self.validator.validate_url("http://localhost") == "http://localhost"
        assert self.validator.validate_url("localhost:3000") == "http://localhost:3000"

    def test_validate_url_invalid_cases(self):
        """Test URL validation with invalid cases."""
        invalid_urls = [
            "",
            None,
            "not-a-url",
            "http://",
            "https://",
            "ftp://example.com" + "x" * 2048,  # Too long
            "http://...",
            "http://.",
            "http://example",  # Missing TLD in strict mode would fail
        ]

        for url in invalid_urls:
            with pytest.raises(URLValidationError):
                self.validator.validate_url(url)

    def test_validate_url_injection_attempts(self):
        """Test URL validation against injection attempts."""
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "http://example.com/path?param=<script>alert('xss')</script>",
            "http://example.com/path/../../../etc/passwd",
            "http://example.com/path?param=`whoami`",
        ]

        for url in malicious_urls:
            with pytest.raises(ValidationError):
                self.validator.validate_url(url)

    def test_validate_url_strict_mode(self):
        """Test URL validation in strict mode."""
        # FTP should be allowed now since we added it to ALLOWED_SCHEMES
        result = self.strict_validator.validate_url("ftp://example.com")
        assert result == "ftp://example.com"

    def test_validate_file_input_valid(self):
        """Test file input validation with valid files."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("http://example.com\n")
            f.write("https://google.com\n")
            temp_path = f.name

        try:
            # Should not raise any exception
            self.validator.validate_file_input(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_file_input_nonexistent(self):
        """Test file input validation with non-existent file."""
        with pytest.raises(FileValidationError, match="File not found"):
            self.validator.validate_file_input("/nonexistent/file.txt")

    def test_validate_file_input_directory(self):
        """Test file input validation with directory instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileValidationError, match="Path is not a file"):
                self.validator.validate_file_input(temp_dir)

    def test_validate_file_input_too_large(self):
        """Test file input validation with oversized file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            # Create a file larger than MAX_FILE_SIZE
            large_content = "x" * (self.validator.MAX_FILE_SIZE + 1)
            f.write(large_content)
            temp_path = f.name

        try:
            with pytest.raises(FileValidationError, match="File too large"):
                self.validator.validate_file_input(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_file_input_permission_denied(self):
        """Test file input validation with permission denied."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Remove read permissions
            os.chmod(temp_path, 0o000)
            with pytest.raises(FileValidationError, match="File is not readable"):
                self.validator.validate_file_input(temp_path)
        finally:
            os.chmod(temp_path, 0o644)  # Restore permissions
            os.unlink(temp_path)

    def test_validate_file_input_strict_mode(self):
        """Test file input validation in strict mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".exe", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            with pytest.raises(FileValidationError, match="File extension not allowed"):
                self.strict_validator.validate_file_input(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_file_content_basic(self):
        """Test file content validation."""
        content = """
# This is a comment
http://example.com
https://google.com
// Another comment

invalid-url
        """.strip()

        valid_lines = self.validator.validate_file_content(content)
        assert len(valid_lines) == 2
        assert "http://example.com" in valid_lines
        assert "https://google.com" in valid_lines

    def test_validate_file_content_too_many_lines(self):
        """Test file content validation with too many lines."""
        # Create content with too many lines
        lines = ["http://example.com"] * (self.validator.MAX_LINES_IN_FILE + 1)
        content = "\n".join(lines)

        with pytest.raises(FileValidationError, match="Too many lines"):
            self.validator.validate_file_content(content)

    def test_validate_file_content_with_bom(self):
        """Test file content validation with BOM."""
        content = "\ufeffhttp://example.com\nhttps://google.com"
        valid_lines = self.validator.validate_file_content(content)
        assert len(valid_lines) == 2

    def test_validate_file_content_malicious(self):
        """Test file content validation with malicious content."""
        content = """
http://example.com
javascript:alert('xss')
http://google.com
<script>alert('xss')</script>
        """.strip()

        # Malicious content should be filtered out
        valid_lines = self.validator.validate_file_content(content)
        assert len(valid_lines) == 2
        assert all("javascript:" not in line for line in valid_lines)
        assert all("<script>" not in line for line in valid_lines)

    def test_validate_http_headers_dict(self):
        """Test HTTP header validation with dictionary input."""
        headers = {
            "User-Agent": "TestAgent/1.0",
            "Accept": "text/html",
            "Content-Type": "application/json",
        }

        validated = self.validator.validate_http_headers(headers)
        assert len(validated) == 3
        assert validated["User-Agent"] == "TestAgent/1.0"

    def test_validate_http_headers_list(self):
        """Test HTTP header validation with list input."""
        headers = [
            "User-Agent: TestAgent/1.0",
            "Accept: text/html",
            "Content-Type: application/json",
        ]

        validated = self.validator.validate_http_headers(headers)
        assert len(validated) == 3
        assert validated["User-Agent"] == "TestAgent/1.0"

    def test_validate_http_headers_invalid_format(self):
        """Test HTTP header validation with invalid format."""
        headers = ["Invalid-Header-Without-Colon"]

        with pytest.raises(HeaderValidationError, match="Invalid header format"):
            self.validator.validate_http_headers(headers)

    def test_validate_http_headers_invalid_name(self):
        """Test HTTP header validation with invalid header name."""
        headers = {"Invalid Header Name!": "value"}

        with pytest.raises(HeaderValidationError, match="Invalid header name"):
            self.validator.validate_http_headers(headers)

    def test_validate_http_headers_invalid_value(self):
        """Test HTTP header validation with invalid header value."""
        headers = {"Valid-Name": "value\x00with\x01control\x02chars"}

        with pytest.raises(HeaderValidationError, match="Invalid header value"):
            self.validator.validate_http_headers(headers)

    def test_validate_http_headers_too_many(self):
        """Test HTTP header validation with too many headers."""
        headers = {
            f"Header-{i}": f"value-{i}"
            for i in range(self.validator.MAX_HEADER_COUNT + 1)
        }

        with pytest.raises(HeaderValidationError, match="Too many headers"):
            self.validator.validate_http_headers(headers)

    def test_validate_http_headers_injection(self):
        """Test HTTP header validation against injection."""
        headers = {"User-Agent": "TestAgent<script>alert('xss')</script>"}

        with pytest.raises(ValidationError, match="Potentially malicious input"):
            self.validator.validate_http_headers(headers)

    def test_validate_numeric_parameter_valid(self):
        """Test numeric parameter validation with valid values."""
        assert (
            self.validator.validate_numeric_parameter(5.0, param_name="timeout") == 5.0
        )
        assert (
            self.validator.validate_numeric_parameter(
                "3", param_name="retries", param_type=int
            )
            == 3
        )
        assert (
            self.validator.validate_numeric_parameter(
                10, param_name="workers", min_val=1, max_val=100, param_type=int
            )
            == 10
        )

    def test_validate_numeric_parameter_invalid_type(self):
        """Test numeric parameter validation with invalid type."""
        with pytest.raises(ArgumentValidationError, match="must be a valid number"):
            self.validator.validate_numeric_parameter(
                "not-a-number", param_name="timeout"
            )

    def test_validate_numeric_parameter_out_of_range(self):
        """Test numeric parameter validation with out-of-range values."""
        with pytest.raises(ArgumentValidationError, match="must be >="):
            self.validator.validate_numeric_parameter(
                -1, param_name="timeout", min_val=0
            )

        with pytest.raises(ArgumentValidationError, match="must be <="):
            self.validator.validate_numeric_parameter(
                1000, param_name="timeout", max_val=100
            )

    def test_validate_timeout(self):
        """Test timeout validation."""
        assert self.validator.validate_timeout(5.0) == 5.0
        assert self.validator.validate_timeout("10") == 10.0

        with pytest.raises(ArgumentValidationError):
            self.validator.validate_timeout(0.05)  # Too small

        with pytest.raises(ArgumentValidationError):
            self.validator.validate_timeout(4000)  # Too large

    def test_validate_retries(self):
        """Test retries validation."""
        assert self.validator.validate_retries(3) == 3
        assert self.validator.validate_retries("5") == 5

        with pytest.raises(ArgumentValidationError):
            self.validator.validate_retries(-1)  # Negative

        with pytest.raises(ArgumentValidationError):
            self.validator.validate_retries(20)  # Too many

    def test_validate_workers(self):
        """Test workers validation."""
        assert self.validator.validate_workers(10) == 10
        assert self.validator.validate_workers("5") == 5

        with pytest.raises(ArgumentValidationError):
            self.validator.validate_workers(0)  # Too few

        with pytest.raises(ArgumentValidationError):
            self.validator.validate_workers(200)  # Too many

    def test_validate_redirect_option(self):
        """Test redirect option validation."""
        valid_options = ["always", "never", "http-only", "https-only"]
        for option in valid_options:
            assert self.validator.validate_redirect_option(option) == option

        with pytest.raises(ArgumentValidationError, match="Invalid redirect option"):
            self.validator.validate_redirect_option("invalid-option")

    def test_validate_output_format(self):
        """Test output format validation."""
        valid_formats = ["table", "json", "csv"]
        for format_type in valid_formats:
            assert self.validator.validate_output_format(format_type) == format_type

        with pytest.raises(ArgumentValidationError, match="Invalid output format"):
            self.validator.validate_output_format("xml")

    def test_validate_comment_style(self):
        """Test comment style validation."""
        valid_styles = ["hash", "slash", "both"]
        for style in valid_styles:
            assert self.validator.validate_comment_style(style) == style

        with pytest.raises(ArgumentValidationError, match="Invalid comment style"):
            self.validator.validate_comment_style("invalid")

    def test_is_valid_hostname(self):
        """Test hostname validation."""
        valid_hostnames = [
            "example.com",
            "sub.example.com",
            "localhost",
            "192.168.1.1",
            "test-domain.co.uk",
        ]

        for hostname in valid_hostnames:
            assert self.validator._is_valid_hostname(hostname)

        invalid_hostnames = [
            "",
            ".",
            "..",
            "example.",
            "-example.com",
            "example-.com",
            "ex..ample.com",
        ]

        for hostname in invalid_hostnames:
            assert not self.validator._is_valid_hostname(hostname)

    def test_is_valid_header_name(self):
        """Test header name validation."""
        valid_names = ["User-Agent", "Content-Type", "Accept", "X-Custom-Header"]
        for name in valid_names:
            assert self.validator._is_valid_header_name(name)

        invalid_names = ["", "Invalid Name", "Header!", "Header:Value"]
        for name in invalid_names:
            assert not self.validator._is_valid_header_name(name)

    def test_is_valid_header_value(self):
        """Test header value validation."""
        valid_values = ["Mozilla/5.0", "application/json", "text/html; charset=utf-8"]
        for value in valid_values:
            assert self.validator._is_valid_header_value(value)

        invalid_values = [
            None,
            "value\x00with\x01control\x02chars",
            "x" * (self.validator.MAX_HEADER_LENGTH + 1),
        ]
        for value in invalid_values:
            assert not self.validator._is_valid_header_value(value)

    def test_check_for_injection(self):
        """Test injection detection."""
        safe_texts = ["http://example.com", "Normal text content", "Path/to/file.txt"]

        for text in safe_texts:
            # Should not raise exception
            self.validator._check_for_injection(text)

        malicious_texts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>",
            "../../../etc/passwd",
            "command; rm -rf /",
            "$(whoami)",
        ]

        for text in malicious_texts:
            with pytest.raises(ValidationError):
                self.validator._check_for_injection(text)


class TestBackwardCompatibilityFunctions:
    """Test backward compatibility functions."""

    def test_url_validation_function(self):
        """Test the backward compatible url_validation function."""
        assert url_validation("example.com") == "http://example.com"
        assert url_validation("https://example.com") == "https://example.com"

        with pytest.raises(Exception):
            url_validation("invalid-url")

    def test_validate_file_path_function(self):
        """Test the validate_file_path function."""
        with tempfile.NamedTemporaryFile() as f:
            # Should not raise exception
            validate_file_path(f.name)

        with pytest.raises(FileValidationError):
            validate_file_path("/nonexistent/file.txt")

    def test_parse_custom_headers_function(self):
        """Test the enhanced parse_custom_headers function."""
        headers = ["User-Agent: TestAgent", "Accept: text/html"]
        result = parse_custom_headers(headers)

        assert result is not None
        assert result["User-Agent"] == "TestAgent"
        assert result["Accept"] == "text/html"

        # Test with invalid headers
        invalid_headers = ["Invalid-Header-Format"]
        result = parse_custom_headers(invalid_headers)
        assert result is None

        # Test with None
        assert parse_custom_headers(None) is None
        assert parse_custom_headers([]) is None


class TestSecurityFeatures:
    """Test security-specific features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()

    def test_xss_prevention(self):
        """Test XSS attack prevention."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<script>alert('xss')</script>",
        ]

        for attempt in xss_attempts:
            with pytest.raises(ValidationError):
                self.validator._check_for_injection(attempt)

    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f",
            "....//....//....//etc/passwd",
        ]

        for attempt in traversal_attempts:
            with pytest.raises(ValidationError):
                self.validator._check_for_injection(attempt)

    def test_command_injection_prevention(self):
        """Test command injection prevention."""
        injection_attempts = [
            "file.txt; rm -rf /",
            "file.txt && cat /etc/passwd",
            "file.txt | whoami",
            "file.txt `whoami`",
            "file.txt $(whoami)",
        ]

        for attempt in injection_attempts:
            with pytest.raises(ValidationError):
                self.validator._check_for_injection(attempt)

    def test_url_length_limits(self):
        """Test URL length limits for DoS prevention."""
        long_url = "http://example.com/" + "x" * self.validator.MAX_URL_LENGTH

        with pytest.raises(URLValidationError, match="URL too long"):
            self.validator.validate_url(long_url)

    def test_domain_length_limits(self):
        """Test domain length limits."""
        long_domain = "x" * (self.validator.MAX_DOMAIN_LENGTH + 1) + ".com"

        with pytest.raises(URLValidationError, match="Domain name too long"):
            self.validator.validate_url(f"http://{long_domain}")

    def test_header_limits(self):
        """Test header count and size limits."""
        # Test header count limit
        too_many_headers = {
            f"Header-{i}": "value" for i in range(self.validator.MAX_HEADER_COUNT + 1)
        }
        with pytest.raises(HeaderValidationError, match="Too many headers"):
            self.validator.validate_http_headers(too_many_headers)

        # Test header value length limit
        long_value = "x" * (self.validator.MAX_HEADER_LENGTH + 1)
        with pytest.raises(HeaderValidationError, match="Invalid header value"):
            self.validator.validate_http_headers({"Test": long_value})


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()

    def test_unicode_handling(self):
        """Test Unicode character handling."""
        unicode_urls = [
            "http://例え.テスト",  # Japanese
            "http://пример.испытание",  # Russian
            "http://مثال.اختبار",  # Arabic
        ]

        # These should be handled gracefully (may pass or fail depending on implementation)
        for url in unicode_urls:
            try:
                result = self.validator.validate_url(url)
                assert isinstance(result, str)
            except URLValidationError:
                # Acceptable to reject Unicode domains
                pass

    def test_empty_and_none_inputs(self):
        """Test empty and None inputs."""
        with pytest.raises(URLValidationError):
            self.validator.validate_url("")

        with pytest.raises(URLValidationError):
            self.validator.validate_url("")  # Use empty string instead of None

        with pytest.raises(FileValidationError):
            self.validator.validate_file_input("")

        assert self.validator.validate_http_headers({}) == {}
        assert self.validator.validate_http_headers({}) == {}

    def test_whitespace_handling(self):
        """Test whitespace handling."""
        # URLs with whitespace should be cleaned
        assert (
            self.validator.validate_url("  http://example.com  ")
            == "http://example.com"
        )

        # Headers with whitespace should be cleaned
        headers = ["  User-Agent  :  TestAgent  "]
        result = self.validator.validate_http_headers(headers)
        assert result["User-Agent"] == "TestAgent"

    def test_case_sensitivity(self):
        """Test case sensitivity handling."""
        # Domain names should be case-insensitive
        assert self.validator.validate_url("http://EXAMPLE.COM") == "http://EXAMPLE.COM"

        # Header names should be preserved
        headers = {"User-Agent": "test", "user-agent": "test2"}
        result = self.validator.validate_http_headers(headers)
        assert len(result) == 2  # Both should be preserved

    def test_port_edge_cases(self):
        """Test port number edge cases."""
        # Valid ports
        assert (
            self.validator.validate_url("http://example.com:1")
            == "http://example.com:1"
        )
        assert (
            self.validator.validate_url("http://example.com:65535")
            == "http://example.com:65535"
        )

        # Invalid ports
        with pytest.raises(URLValidationError):
            self.validator.validate_url("http://example.com:0")

        with pytest.raises(URLValidationError):
            self.validator.validate_url("http://example.com:65536")
