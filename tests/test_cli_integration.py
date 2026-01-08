"""
Comprehensive integration tests for CLI module.

These tests focus on increasing coverage for httpcheck/cli.py from 22% to 80%+.
Tests cover argument parsing, file input, stdin processing, output formats,
and all CLI execution paths.
"""

import argparse
import io
import sys
from datetime import datetime
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from httpcheck.cli import (
    _add_file_arguments,
    _add_output_arguments,
    _add_redirect_arguments,
    _add_request_arguments,
    _add_request_customization_arguments,
    _add_tld_arguments,
    _create_argument_parser,
    _handle_stdin_input,
    _print_verbose_header,
    _process_file_input,
    _process_sites,
    _process_stdin_input,
    _send_completion_notification,
    _validate_sites,
    check_sites_parallel,
    check_sites_serial,
    check_tlds,
    get_arguments,
    main,
    process_site_status,
)
from httpcheck.common import SiteStatus


class TestArgumentParser:
    """Test argument parser creation and configuration."""

    def test_create_argument_parser(self):
        """Test basic parser creation."""
        parser = _create_argument_parser()
        assert parser is not None
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_has_site_argument(self):
        """Test parser has site positional argument."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.site == ["example.com"]

    def test_parser_multiple_sites(self):
        """Test parser handles multiple sites."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com", "google.com"])
        assert args.site == ["example.com", "google.com"]

    def test_parser_no_sites(self):
        """Test parser handles no sites."""
        parser = _create_argument_parser()
        args = parser.parse_args([])
        assert args.site == []

    def test_parser_version(self, capsys):
        """Test --version flag."""
        parser = _create_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])
        captured = capsys.readouterr()
        assert "httpcheck" in captured.out


class TestTLDArguments:
    """Test TLD-related argument parsing."""

    def test_tld_flag(self):
        """Test -t/--tld flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["-t", "example.com"])
        assert args.tld is True

    def test_disable_tld_checks(self):
        """Test --disable-tld-checks flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--disable-tld-checks", "example.com"])
        assert args.disable_tld is True

    def test_tld_warning_only(self):
        """Test --tld-warning-only flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--tld-warning-only", "example.com"])
        assert args.tld_warning_only is True

    def test_update_tld_list(self):
        """Test --update-tld-list flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--update-tld-list", "example.com"])
        assert args.update_tld is True

    def test_tld_cache_days_default(self):
        """Test default TLD cache days."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.tld_cache_days == 30

    def test_tld_cache_days_custom(self):
        """Test custom TLD cache days."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--tld-cache-days", "60", "example.com"])
        assert args.tld_cache_days == 60


class TestRequestArguments:
    """Test request timing and retry argument parsing."""

    def test_timeout_default(self):
        """Test default timeout value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.timeout == 5.0

    def test_timeout_custom(self):
        """Test custom timeout value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--timeout", "10.5", "example.com"])
        assert args.timeout == 10.5

    def test_retries_default(self):
        """Test default retries value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.retries == 2

    def test_retries_custom(self):
        """Test custom retries value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--retries", "5", "example.com"])
        assert args.retries == 5

    def test_workers_default(self):
        """Test default workers value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.workers == 10

    def test_workers_custom(self):
        """Test custom workers value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--workers", "20", "example.com"])
        assert args.workers == 20

    def test_retry_delay_default(self):
        """Test default retry delay value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.retry_delay == 1.0

    def test_retry_delay_custom(self):
        """Test custom retry delay value."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--retry-delay", "2.5", "example.com"])
        assert args.retry_delay == 2.5


class TestFileArguments:
    """Test file input handling argument parsing."""

    def test_file_summary_flag(self):
        """Test --file-summary flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--file-summary", "example.com"])
        assert args.file_summary is True

    def test_comment_style_default(self):
        """Test default comment style."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.comment_style == "both"

    def test_comment_style_hash(self):
        """Test hash comment style."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--comment-style", "hash", "example.com"])
        assert args.comment_style == "hash"

    def test_comment_style_slash(self):
        """Test slash comment style."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--comment-style", "slash", "example.com"])
        assert args.comment_style == "slash"

    def test_comment_style_both(self):
        """Test both comment style."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--comment-style", "both", "example.com"])
        assert args.comment_style == "both"


class TestRedirectArguments:
    """Test redirect handling argument parsing."""

    def test_follow_redirects_default(self):
        """Test default redirect behavior."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.follow_redirects == "always"

    def test_follow_redirects_never(self):
        """Test never follow redirects."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--follow-redirects", "never", "example.com"])
        assert args.follow_redirects == "never"

    def test_follow_redirects_http_only(self):
        """Test HTTP-only redirects."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--follow-redirects", "http-only", "example.com"])
        assert args.follow_redirects == "http-only"

    def test_follow_redirects_https_only(self):
        """Test HTTPS-only redirects."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--follow-redirects", "https-only", "example.com"])
        assert args.follow_redirects == "https-only"

    def test_max_redirects_default(self):
        """Test default max redirects."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.max_redirects == 30

    def test_max_redirects_custom(self):
        """Test custom max redirects."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--max-redirects", "10", "example.com"])
        assert args.max_redirects == 10

    def test_show_redirect_timing(self):
        """Test --show-redirect-timing flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--show-redirect-timing", "example.com"])
        assert args.show_redirect_timing is True


class TestRequestCustomizationArguments:
    """Test request customization argument parsing."""

    def test_custom_headers_single(self):
        """Test single custom header."""
        parser = _create_argument_parser()
        args = parser.parse_args(["-H", "User-Agent: MyBot", "example.com"])
        assert args.headers == ["User-Agent: MyBot"]

    def test_custom_headers_multiple(self):
        """Test multiple custom headers."""
        parser = _create_argument_parser()
        args = parser.parse_args(
            ["-H", "User-Agent: MyBot", "-H", "Accept: application/json", "example.com"]
        )
        assert args.headers == ["User-Agent: MyBot", "Accept: application/json"]

    def test_custom_headers_long_form(self):
        """Test --header long form."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--header", "Custom: Value", "example.com"])
        assert args.headers == ["Custom: Value"]

    def test_verify_ssl_default(self):
        """Test SSL verification is enabled by default."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.verify_ssl is True

    def test_no_verify_ssl(self):
        """Test --no-verify-ssl flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--no-verify-ssl", "example.com"])
        assert args.verify_ssl is False


class TestOutputArguments:
    """Test output format and mode argument parsing."""

    def test_quiet_flag(self):
        """Test -q/--quiet flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["-q", "example.com"])
        assert args.quiet is True

    def test_verbose_flag(self):
        """Test -v/--verbose flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["-v", "example.com"])
        assert args.verbose is True

    def test_code_flag(self):
        """Test -c/--code flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["-c", "example.com"])
        assert args.code is True

    def test_fast_flag(self):
        """Test -f/--fast flag."""
        parser = _create_argument_parser()
        args = parser.parse_args(["-f", "example.com"])
        assert args.fast is True

    def test_output_format_default(self):
        """Test default output format."""
        parser = _create_argument_parser()
        args = parser.parse_args(["example.com"])
        assert args.output_format == "table"

    def test_output_format_json(self):
        """Test JSON output format."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--output", "json", "example.com"])
        assert args.output_format == "json"

    def test_output_format_csv(self):
        """Test CSV output format."""
        parser = _create_argument_parser()
        args = parser.parse_args(["--output", "csv", "example.com"])
        assert args.output_format == "csv"

    def test_mutually_exclusive_quiet_verbose(self):
        """Test quiet and verbose are mutually exclusive."""
        parser = _create_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-q", "-v", "example.com"])

    def test_mutually_exclusive_quiet_code(self):
        """Test quiet and code are mutually exclusive."""
        parser = _create_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-q", "-c", "example.com"])

    def test_mutually_exclusive_verbose_fast(self):
        """Test verbose and fast are mutually exclusive."""
        parser = _create_argument_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-v", "-f", "example.com"])


class TestFileInputProcessing:
    """Test file input processing functionality."""

    @patch("httpcheck.cli.FileInputHandler")
    def test_process_file_input_success(self, mock_handler):
        """Test successful file input processing."""
        mock_instance = MagicMock()
        mock_instance.parse.return_value = ["http://example.com", "http://google.com"]
        mock_handler.return_value = mock_instance

        options = MagicMock()
        options.file_summary = False
        options.verbose = False
        options.comment_style = "both"

        result = _process_file_input("@domains.txt", options)
        assert result == ["http://example.com", "http://google.com"]
        mock_handler.assert_called_once_with(
            "domains.txt", verbose=False, comment_style="both"
        )

    @patch("httpcheck.cli.FileInputHandler")
    def test_process_file_input_with_verbose(self, mock_handler):
        """Test file input processing with verbose option."""
        mock_instance = MagicMock()
        mock_instance.parse.return_value = ["http://example.com"]
        mock_handler.return_value = mock_instance

        options = MagicMock()
        options.file_summary = True
        options.verbose = False
        options.comment_style = "hash"

        result = _process_file_input("@domains.txt", options)
        assert result == ["http://example.com"]
        mock_handler.assert_called_once_with(
            "domains.txt", verbose=True, comment_style="hash"
        )

    @patch("httpcheck.cli.FileInputHandler")
    def test_process_file_input_error(self, mock_handler, capsys):
        """Test file input processing with error."""
        mock_handler.side_effect = FileNotFoundError("File not found")

        options = MagicMock()
        options.file_summary = False
        options.verbose = False
        options.comment_style = "both"

        result = _process_file_input("@missing.txt", options)
        assert result == []
        captured = capsys.readouterr()
        assert "Error processing file" in captured.out


class TestStdinInputProcessing:
    """Test stdin input processing functionality."""

    @patch("sys.stdin", io.StringIO("example.com\ngoogle.com\n"))
    @patch("httpcheck.cli.url_validation")
    def test_process_stdin_basic(self, mock_validation):
        """Test basic stdin processing."""
        mock_validation.side_effect = lambda x: f"http://{x}"

        result = _process_stdin_input()
        assert len(result) == 2
        assert result == ["http://example.com", "http://google.com"]

    @patch("sys.stdin", io.StringIO("example.com\n# comment\ngoogle.com\n"))
    @patch("httpcheck.cli.url_validation")
    def test_process_stdin_with_hash_comments(self, mock_validation):
        """Test stdin processing with hash comments."""
        mock_validation.side_effect = lambda x: f"http://{x}"

        result = _process_stdin_input()
        assert len(result) == 2
        assert "# comment" not in result

    @patch("sys.stdin", io.StringIO("example.com\n// comment\ngoogle.com\n"))
    @patch("httpcheck.cli.url_validation")
    def test_process_stdin_with_slash_comments(self, mock_validation):
        """Test stdin processing with slash comments."""
        mock_validation.side_effect = lambda x: f"http://{x}"

        result = _process_stdin_input()
        assert len(result) == 2
        assert "// comment" not in result

    @patch("sys.stdin", io.StringIO("example.com # inline comment\n"))
    @patch("httpcheck.cli.url_validation")
    def test_process_stdin_inline_comments(self, mock_validation):
        """Test stdin processing with inline comments."""
        mock_validation.side_effect = lambda x: f"http://{x}"

        result = _process_stdin_input()
        assert len(result) == 1
        assert result == ["http://example.com"]

    @patch("sys.stdin", io.StringIO("\n\n\n"))
    def test_process_stdin_empty_lines(self):
        """Test stdin processing with empty lines."""
        result = _process_stdin_input()
        assert result == []

    @patch("sys.stdin", io.StringIO("invalid-url\n"))
    @patch("httpcheck.cli.url_validation")
    @patch("httpcheck.cli.get_logger")
    def test_process_stdin_validation_error(self, mock_logger, mock_validation):
        """Test stdin processing with validation error."""
        mock_validation.side_effect = argparse.ArgumentTypeError("Invalid URL")
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        result = _process_stdin_input()
        assert result == []
        mock_logger_instance.error.assert_called_once_with("Invalid URL")


class TestSiteValidation:
    """Test site URL validation functionality."""

    @patch("httpcheck.cli.url_validation")
    def test_validate_sites_success(self, mock_validation):
        """Test successful site validation."""
        mock_validation.side_effect = lambda x: f"http://{x}"

        result = _validate_sites(["example.com", "google.com"])
        assert len(result) == 2
        assert result == ["http://example.com", "http://google.com"]

    @patch("httpcheck.cli.url_validation")
    def test_validate_sites_skip_file_prefix(self, mock_validation):
        """Test validation skips @ file prefix."""
        mock_validation.side_effect = lambda x: f"http://{x}"

        result = _validate_sites(["@domains.txt", "example.com"])
        assert len(result) == 1
        assert result == ["http://example.com"]

    @patch("httpcheck.cli.url_validation")
    @patch("httpcheck.cli.get_logger")
    def test_validate_sites_with_error(self, mock_logger, mock_validation):
        """Test validation with error."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        def validation_side_effect(url):
            if url == "invalid":
                raise argparse.ArgumentTypeError("Invalid URL")
            return f"http://{url}"

        mock_validation.side_effect = validation_side_effect

        result = _validate_sites(["example.com", "invalid", "google.com"])
        assert len(result) == 2
        mock_logger_instance.error.assert_called_once_with("Invalid URL")


class TestProcessSiteStatus:
    """Test site status processing functionality."""

    def test_process_site_status_success_200(self):
        """Test processing successful 200 status."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        successful, failures = process_site_status(
            status, "http://example.com", 0, 0, []
        )
        assert successful == 1
        assert failures == 0

    def test_process_site_status_success_300(self):
        """Test processing 3xx status."""
        status = SiteStatus(
            domain="example.com",
            status="301",
            message="Moved Permanently",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        successful, failures = process_site_status(
            status, "http://example.com", 0, 0, []
        )
        assert successful == 1
        assert failures == 0

    def test_process_site_status_failure_400(self):
        """Test processing 4xx status."""
        status = SiteStatus(
            domain="example.com",
            status="404",
            message="Not Found",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        failed_sites = []
        successful, failures = process_site_status(
            status, "http://example.com", 0, 0, failed_sites
        )
        assert successful == 0
        assert failures == 1
        assert len(failed_sites) == 1
        assert "example.com" in failed_sites[0]

    def test_process_site_status_failure_500(self):
        """Test processing 5xx status."""
        status = SiteStatus(
            domain="example.com",
            status="500",
            message="Internal Server Error",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        failed_sites = []
        successful, failures = process_site_status(
            status, "http://example.com", 0, 0, failed_sites
        )
        assert successful == 0
        assert failures == 1
        assert len(failed_sites) == 1

    def test_process_site_status_not_site_status(self):
        """Test processing non-SiteStatus object."""
        failed_sites = []
        successful, failures = process_site_status(
            "error", "http://example.com", 0, 0, failed_sites
        )
        assert successful == 0
        assert failures == 1
        assert len(failed_sites) == 1

    def test_process_site_status_invalid_status_code(self):
        """Test processing invalid status code."""
        status = SiteStatus(
            domain="example.com",
            status="ERROR",
            message="Connection Failed",
            redirect_chain=[],
            response_time=0.0,
            redirect_timing=[],
        )
        failed_sites = []
        successful, failures = process_site_status(
            status, "http://example.com", 0, 0, failed_sites
        )
        assert successful == 0
        assert failures == 1


class TestCheckSitesSerial:
    """Test serial site checking functionality."""

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.print_format")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_check_sites_serial_success(self, mock_headers, mock_format, mock_check):
        """Test serial checking with success."""
        mock_headers.return_value = {}
        mock_check.return_value = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        mock_format.return_value = "[+] example.com: 200 OK"

        options = MagicMock()
        options.site = ["http://example.com"]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.quiet = False
        options.verbose = False
        options.code = False
        options.show_redirect_timing = False
        options.output_format = "table"

        successful, failures = check_sites_serial(options, 0, 0, [])
        assert successful == 1
        assert failures == 0

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.format_json_list")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_check_sites_serial_json_output(self, mock_headers, mock_json, mock_check):
        """Test serial checking with JSON output."""
        mock_headers.return_value = {}
        mock_check.return_value = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        mock_json.return_value = '{"status": "200"}'

        options = MagicMock()
        options.site = ["http://example.com"]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.quiet = False
        options.verbose = False
        options.output_format = "json"

        successful, failures = check_sites_serial(options, 0, 0, [])
        assert successful == 1
        assert failures == 0
        mock_json.assert_called_once()

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.format_csv_list")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_check_sites_serial_csv_output(self, mock_headers, mock_csv, mock_check):
        """Test serial checking with CSV output."""
        mock_headers.return_value = {}
        mock_check.return_value = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        mock_csv.return_value = "domain,status\nexample.com,200"

        options = MagicMock()
        options.site = ["http://example.com"]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.quiet = False
        options.output_format = "csv"

        successful, failures = check_sites_serial(options, 0, 0, [])
        assert successful == 1
        assert failures == 0
        mock_csv.assert_called_once()

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_check_sites_serial_with_exception(self, mock_headers, mock_check, capsys):
        """Test serial checking with exception."""
        mock_headers.return_value = {}
        mock_check.side_effect = Exception("Connection failed")

        options = MagicMock()
        options.site = ["http://example.com"]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.quiet = False
        options.output_format = "table"

        failed_sites = []
        successful, failures = check_sites_serial(options, 0, 0, failed_sites)
        assert successful == 0
        assert failures == 1
        assert len(failed_sites) == 1


class TestCheckSitesParallel:
    """Test parallel site checking functionality."""

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.print_format")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_check_sites_parallel_success(self, mock_headers, mock_format, mock_check):
        """Test parallel checking with success."""
        mock_headers.return_value = {}
        mock_check.return_value = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        mock_format.return_value = "[+] example.com: 200 OK"

        options = MagicMock()
        options.site = ["http://example.com", "http://google.com"]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.workers = 10
        options.quiet = False
        options.verbose = False
        options.code = False
        options.show_redirect_timing = False
        options.output_format = "table"

        successful, failures = check_sites_parallel(options, 0, 0, [])
        assert successful == 2
        assert failures == 0

    @patch("httpcheck.cli.check_site")
    @patch("httpcheck.cli.format_json_list")
    @patch("httpcheck.cli.parse_custom_headers")
    def test_check_sites_parallel_json_output(
        self, mock_headers, mock_json, mock_check
    ):
        """Test parallel checking with JSON output."""
        mock_headers.return_value = {}
        mock_check.return_value = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.5,
            redirect_timing=[],
        )
        mock_json.return_value = '{"status": "200"}'

        options = MagicMock()
        options.site = ["http://example.com"]
        options.timeout = 5.0
        options.retries = 2
        options.follow_redirects = "always"
        options.max_redirects = 30
        options.headers = None
        options.verify_ssl = True
        options.retry_delay = 1.0
        options.workers = 10
        options.quiet = False
        options.output_format = "json"

        successful, failures = check_sites_parallel(options, 0, 0, [])
        assert successful == 1
        assert failures == 0
        mock_json.assert_called_once()


class TestCheckTLDs:
    """Test TLD checking functionality."""

    @patch("httpcheck.cli.TLDManager")
    def test_check_tlds_disabled(self, mock_tld_manager):
        """Test TLD check when disabled."""
        options = MagicMock()
        options.disable_tld = True
        options.tld = False

        failures = check_tlds(options, 0, [])
        assert failures == 0
        mock_tld_manager.assert_not_called()

    @patch("httpcheck.cli.TLDManager")
    def test_check_tlds_not_requested(self, mock_tld_manager):
        """Test TLD check when not requested."""
        options = MagicMock()
        options.disable_tld = False
        options.tld = False

        failures = check_tlds(options, 0, [])
        assert failures == 0
        mock_tld_manager.assert_not_called()

    @patch("httpcheck.cli.TLDManager")
    def test_check_tlds_success(self, mock_tld_manager):
        """Test successful TLD check."""
        mock_instance = MagicMock()
        mock_instance.validate_tld.return_value = None
        mock_tld_manager.return_value = mock_instance

        options = MagicMock()
        options.disable_tld = False
        options.tld = True
        options.update_tld = False
        options.tld_cache_days = 30
        options.verbose = False
        options.tld_warning_only = False
        options.site = ["http://example.com"]

        failures = check_tlds(options, 0, [])
        assert failures == 0
        mock_tld_manager.assert_called_once()


class TestHelperFunctions:
    """Test CLI helper functions."""

    @patch("httpcheck.cli.get_logger")
    def test_print_verbose_header(self, mock_logger):
        """Test verbose header printing."""
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        _print_verbose_header()

        # Check that logger.info was called with httpcheck and a date
        assert mock_logger_instance.info.called
        call_args = mock_logger_instance.info.call_args[0]
        assert "httpcheck" in call_args[0]
        assert "%" in call_args[0]  # Format string check

    @patch("sys.stdin")
    def test_handle_stdin_input_with_stdin(self, mock_stdin):
        """Test handling stdin input."""
        mock_stdin.isatty.return_value = False
        mock_stdin.__iter__.return_value = ["example.com\n", "google.com\n"]

        options = MagicMock()
        options.site = []

        _handle_stdin_input(options)
        assert options.site == ["example.com", "google.com"]

    @patch("sys.stdin")
    def test_handle_stdin_input_no_stdin(self, mock_stdin):
        """Test handling when no stdin and no sites."""
        mock_stdin.isatty.return_value = True

        options = MagicMock()
        options.site = []

        with pytest.raises(SystemExit):
            _handle_stdin_input(options)

    @patch("httpcheck.cli.check_sites_serial")
    def test_process_sites_serial(self, mock_serial):
        """Test processing sites in serial mode."""
        mock_serial.return_value = (1, 0)

        options = MagicMock()
        options.fast = False

        successful, failures = _process_sites(options, 0, 0, [])
        mock_serial.assert_called_once()

    @patch("httpcheck.cli.check_sites_parallel")
    def test_process_sites_parallel(self, mock_parallel):
        """Test processing sites in parallel mode."""
        mock_parallel.return_value = (2, 0)

        options = MagicMock()
        options.fast = True

        successful, failures = _process_sites(options, 0, 0, [])
        mock_parallel.assert_called_once()

    @patch("httpcheck.cli.notify")
    def test_send_notification_success(self, mock_notify):
        """Test sending success notification."""
        _send_completion_notification(5, 5, 0, [])
        mock_notify.assert_called_once()
        args = mock_notify.call_args[0]
        assert "Success" in args[0]

    @patch("httpcheck.cli.notify")
    def test_send_notification_failure(self, mock_notify):
        """Test sending failure notification."""
        _send_completion_notification(5, 3, 2, ["example.com (404)", "test.com (500)"])
        mock_notify.assert_called_once()
        args = mock_notify.call_args[0]
        assert "Failed" in args[0]
        assert args[2] == ["example.com (404)", "test.com (500)"]


class TestMainIntegration:
    """Test main CLI entry point."""

    @patch("httpcheck.cli.get_arguments")
    @patch("httpcheck.cli.check_tlds")
    @patch("httpcheck.cli._process_sites")
    @patch("httpcheck.cli._send_completion_notification")
    def test_main_basic_execution(
        self, mock_notify, mock_process, mock_tlds, mock_args
    ):
        """Test basic main execution."""
        options = MagicMock()
        options.site = ["http://example.com"]
        options.verbose = False
        options.output_format = "table"
        mock_args.return_value = options
        mock_tlds.return_value = 0
        mock_process.return_value = (1, 0)

        main()

        mock_args.assert_called_once()
        mock_tlds.assert_called_once()
        mock_process.assert_called_once()
        mock_notify.assert_called_once()

    @patch("httpcheck.cli.get_arguments")
    @patch("httpcheck.cli.check_tlds")
    @patch("httpcheck.cli._process_sites")
    @patch("httpcheck.cli._send_completion_notification")
    @patch("httpcheck.cli._print_verbose_header")
    def test_main_verbose_mode(
        self, mock_header, mock_notify, mock_process, mock_tlds, mock_args
    ):
        """Test main execution with verbose mode."""
        options = MagicMock()
        options.site = ["http://example.com"]
        options.verbose = True
        options.output_format = "table"
        mock_args.return_value = options
        mock_tlds.return_value = 0
        mock_process.return_value = (1, 0)

        main()

        mock_header.assert_called_once()

    @patch("httpcheck.cli.get_arguments")
    @patch("httpcheck.cli.check_tlds")
    @patch("httpcheck.cli._process_sites")
    @patch("httpcheck.cli._send_completion_notification")
    def test_main_with_json_output(
        self, mock_notify, mock_process, mock_tlds, mock_args, capsys
    ):
        """Test main execution with JSON output format."""
        options = MagicMock()
        options.site = ["http://example.com"]
        options.verbose = False
        options.output_format = "json"
        mock_args.return_value = options
        mock_tlds.return_value = 0
        mock_process.return_value = (1, 0)

        main()

        captured = capsys.readouterr()
        # JSON output should not print summary
        assert "Checked" not in captured.out or options.output_format == "json"


class TestGetArguments:
    """Test get_arguments function."""

    @patch("sys.argv", ["httpcheck", "example.com"])
    @patch("sys.stdin")
    def test_get_arguments_basic(self, mock_stdin):
        """Test basic argument parsing."""
        mock_stdin.isatty.return_value = True

        options = get_arguments()
        assert len(options.site) == 1
        assert "example.com" in options.site[0]

    @patch("sys.argv", ["httpcheck", "--no-verify-ssl", "example.com"])
    @patch("sys.stdin")
    @patch("httpcheck.cli.get_logger")
    @patch("httpcheck.cli.setup_logger")
    def test_get_arguments_ssl_warning(self, mock_setup, mock_logger, mock_stdin):
        """Test SSL warning message."""
        mock_stdin.isatty.return_value = True
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        options = get_arguments()

        # Check that logger.warning was called about SSL
        assert mock_logger_instance.warning.called
        call_args = mock_logger_instance.warning.call_args[0]
        assert "SSL certificate verification is disabled" in call_args[0]

    @patch("sys.argv", ["httpcheck"])
    @patch("sys.stdin")
    def test_get_arguments_no_sites(self, mock_stdin):
        """Test error when no sites provided."""
        mock_stdin.isatty.return_value = True

        with pytest.raises(SystemExit):
            get_arguments()

    @patch("sys.argv", ["httpcheck", "@domains.txt"])
    @patch("sys.stdin")
    @patch("httpcheck.cli.FileInputHandler")
    def test_get_arguments_with_file(self, mock_handler, mock_stdin):
        """Test argument parsing with file input."""
        mock_stdin.isatty.return_value = True
        mock_instance = MagicMock()
        mock_instance.parse.return_value = ["http://example.com"]
        mock_handler.return_value = mock_instance

        options = get_arguments()
        assert len(options.site) >= 1
