"""Performance regression tests for httpcheck.

These tests benchmark critical performance paths to prevent regressions.
Run with: pytest tests/test_performance.py --benchmark-only
"""

import io
from unittest.mock import MagicMock, patch

import pytest

from httpcheck.cli import check_sites_parallel, check_sites_serial
from httpcheck.common import SiteStatus
from httpcheck.file_handler import FileInputHandler, url_validation
from httpcheck.output_formatter import format_csv_list, format_json_list
from httpcheck.site_checker import check_site
from httpcheck.tld_manager import TLDManager


@pytest.fixture
def mock_successful_response():
    """Mock a successful HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_response.url = "https://example.com"
    mock_response.elapsed.total_seconds.return_value = 0.1
    mock_response.headers = {}
    return mock_response


class TestSiteCheckerPerformance:
    """Performance tests for site checking."""

    @patch("httpcheck.site_checker.requests.Session")
    def test_benchmark_single_site_check(
        self, mock_session, mock_successful_response, benchmark
    ):
        """Benchmark checking a single site."""
        mock_session.return_value.get.return_value = mock_successful_response

        result = benchmark(check_site, "https://example.com")

        assert isinstance(result, SiteStatus)
        assert result.status == "200"

    @patch("httpcheck.site_checker.requests.Session")
    def test_benchmark_site_check_with_retries(
        self, mock_session, mock_successful_response, benchmark
    ):
        """Benchmark site check with retry logic."""
        mock_session.return_value.get.return_value = mock_successful_response

        result = benchmark(
            check_site, "https://example.com", timeout=5.0, retries=3, retry_delay=0.1
        )

        assert isinstance(result, SiteStatus)


class TestFileHandlerPerformance:
    """Performance tests for file handling."""

    def test_benchmark_url_validation(self, benchmark):
        """Benchmark URL validation."""
        result = benchmark(url_validation, "https://example.com")
        assert result.startswith("http")

    def test_benchmark_file_parsing_small(self, benchmark, tmp_path):
        """Benchmark parsing a small file (10 URLs)."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("\n".join([f"example{i}.com" for i in range(10)]))

        def parse_file():
            handler = FileInputHandler(str(test_file))
            return list(handler.parse())

        result = benchmark(parse_file)
        assert len(result) == 10

    def test_benchmark_file_parsing_medium(self, benchmark, tmp_path):
        """Benchmark parsing a medium file (100 URLs)."""
        test_file = tmp_path / "medium.txt"
        test_file.write_text("\n".join([f"example{i}.com" for i in range(100)]))

        def parse_file():
            handler = FileInputHandler(str(test_file))
            return list(handler.parse())

        result = benchmark(parse_file)
        assert len(result) == 100

    def test_benchmark_file_parsing_with_comments(self, benchmark, tmp_path):
        """Benchmark parsing file with comments."""
        test_file = tmp_path / "commented.txt"
        content = []
        for i in range(50):
            content.append(f"# Comment {i}")
            content.append(f"example{i}.com")
        test_file.write_text("\n".join(content))

        def parse_file():
            handler = FileInputHandler(str(test_file))
            return list(handler.parse())

        result = benchmark(parse_file)
        assert len(result) == 50


class TestOutputFormatterPerformance:
    """Performance tests for output formatting."""

    @pytest.fixture
    def sample_statuses(self):
        """Create sample site statuses for testing."""
        return [
            SiteStatus(
                domain=f"example{i}.com",
                status="200",
                message="OK",
                redirect_chain=[],
                response_time=0.1 + (i * 0.01),
                redirect_timing=[],
            )
            for i in range(100)
        ]

    def test_benchmark_json_formatting(self, benchmark, sample_statuses):
        """Benchmark JSON output formatting."""
        result = benchmark(format_json_list, sample_statuses, verbose=False)
        assert '"domain"' in result

    def test_benchmark_json_formatting_verbose(self, benchmark, sample_statuses):
        """Benchmark verbose JSON output formatting."""
        result = benchmark(format_json_list, sample_statuses, verbose=True)
        assert '"response_time"' in result

    def test_benchmark_csv_formatting(self, benchmark, sample_statuses):
        """Benchmark CSV output formatting."""
        result = benchmark(format_csv_list, sample_statuses, verbose=False)
        assert "domain,status" in result

    def test_benchmark_csv_formatting_verbose(self, benchmark, sample_statuses):
        """Benchmark verbose CSV output formatting."""
        result = benchmark(format_csv_list, sample_statuses, verbose=True)
        assert "response_time" in result


class TestValidationPerformance:
    """Performance tests for validation."""

    def test_benchmark_url_validation(self, benchmark):
        """Benchmark URL validation."""
        result = benchmark(url_validation, "https://example.com")
        assert result.startswith("http")

    def test_benchmark_url_validation_with_protocol(self, benchmark):
        """Benchmark URL validation with different protocols."""
        result = benchmark(url_validation, "example.com")
        assert result.startswith("http")


class TestTLDManagerPerformance:
    """Performance tests for TLD management."""

    def test_benchmark_tld_validation(self, benchmark, tmp_path):
        """Benchmark TLD validation."""
        # Create a simple TLD cache file
        cache_file = tmp_path / "tld_cache.json"
        import json

        cache_file.write_text(
            json.dumps(
                {
                    "tlds": ["com", "org", "net"],
                    "timestamp": 0,  # Old timestamp to avoid refresh
                }
            )
        )

        # Initialize manager with cache
        manager = TLDManager(cache_dir=str(tmp_path), force_update=False)

        # Benchmark validation
        result = benchmark(manager.validate_tld, "example.com")
        assert result is None  # No exception means valid

    def test_benchmark_tld_manager_with_local_file(self, benchmark, tmp_path):
        """Benchmark TLD manager using local file."""
        # TLDManager will fall back to local file if cache doesn't exist
        manager = benchmark(TLDManager, cache_dir=str(tmp_path), force_update=False)
        assert manager is not None


class TestCLIPerformance:
    """Performance tests for CLI operations."""

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_benchmark_serial_checking_10_sites(
        self, mock_headers, mock_check, benchmark
    ):
        """Benchmark checking 10 sites serially."""
        mock_headers.return_value = {}
        mock_check.return_value = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.1,
            redirect_timing=[],
        )

        options = MagicMock()
        options.site = [f"http://example{i}.com" for i in range(10)]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.quiet = True  # Suppress output for benchmarking
        options.verbose = False
        options.code = False
        options.show_redirect_timing = False
        options.output_format = "table"

        successful, failures = benchmark(check_sites_serial, options, 0, 0, [])
        assert successful == 10

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_benchmark_parallel_checking_50_sites(
        self, mock_headers, mock_check, benchmark
    ):
        """Benchmark checking 50 sites in parallel."""
        mock_headers.return_value = {}
        mock_check.return_value = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.1,
            redirect_timing=[],
        )

        options = MagicMock()
        options.site = [f"http://example{i}.com" for i in range(50)]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.workers = 10
        options.quiet = True
        options.verbose = False
        options.code = False
        options.show_redirect_timing = False
        options.output_format = "table"

        successful, failures = benchmark(check_sites_parallel, options, 0, 0, [])
        assert successful == 50


class TestIntegrationPerformance:
    """End-to-end performance tests."""

    @patch("httpcheck.site_checker.requests.Session")
    def test_benchmark_end_to_end_workflow(
        self, mock_session, mock_successful_response, benchmark, tmp_path
    ):
        """Benchmark complete workflow: file → parse → check → format."""
        mock_session.return_value.get.return_value = mock_successful_response

        # Create test file
        test_file = tmp_path / "sites.txt"
        test_file.write_text("\n".join([f"example{i}.com" for i in range(20)]))

        def complete_workflow():
            # Parse file
            handler = FileInputHandler(str(test_file))
            urls = list(handler.parse())

            # Check sites
            results = [check_site(url, timeout=5.0) for url in urls]

            # Format output
            json_output = format_json_list(results, verbose=False)

            return json_output

        result = benchmark(complete_workflow)
        assert '"domain"' in result


# Performance thresholds (for CI failure detection)
# These can be adjusted based on baseline measurements


class TestPerformanceThresholds:
    """Tests that fail if performance degrades significantly."""

    @patch("httpcheck.site_checker.requests.Session")
    def test_single_site_check_performance(
        self, mock_session, mock_successful_response
    ):
        """Single site check should complete in <100ms (excluding network)."""
        mock_session.return_value.get.return_value = mock_successful_response

        import time

        start = time.time()
        result = check_site("https://example.com")
        duration = time.time() - start

        assert duration < 0.1, f"Single site check took {duration}s (threshold: 0.1s)"
        assert isinstance(result, SiteStatus)

    def test_url_validation_performance(self):
        """URL validation should complete in <1ms."""
        import time

        urls = [f"https://example{i}.com" for i in range(100)]

        start = time.time()
        for url in urls:
            url_validation(url)
        duration = time.time() - start

        avg_duration = duration / 100
        assert (
            avg_duration < 0.001
        ), f"URL validation took {avg_duration}s (threshold: 0.001s)"

    def test_file_parsing_performance(self, tmp_path):
        """File parsing should process >1000 lines/second."""
        test_file = tmp_path / "large.txt"
        test_file.write_text("\n".join([f"example{i}.com" for i in range(1000)]))

        import time

        start = time.time()
        handler = FileInputHandler(str(test_file))
        urls = list(handler.parse())
        duration = time.time() - start

        lines_per_second = 1000 / duration
        assert (
            lines_per_second > 1000
        ), f"File parsing: {lines_per_second:.0f} lines/s (threshold: 1000 lines/s)"
        assert len(urls) == 1000
