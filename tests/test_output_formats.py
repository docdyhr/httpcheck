"""Test cases for JSON and CSV output formats."""

import csv
import io
import json

import pytest

from httpcheck.common import SiteStatus
from httpcheck.output_formatter import (
    format_csv,
    format_csv_list,
    format_json,
    format_json_list,
    print_format,
)


class TestJSONOutput:
    """Test cases for JSON output formatting."""

    def test_format_json_basic(self):
        """Test basic JSON output formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.234567,
            redirect_timing=[],
        )

        result = format_json(status, verbose=False)
        data = json.loads(result)

        assert data["domain"] == "example.com"
        assert data["status"] == "200"
        assert data["message"] == "OK"
        assert data["response_time"] == 1.235  # Rounded to 3 decimal places
        assert "redirect_chain" not in data  # Not included in non-verbose

    def test_format_json_verbose(self):
        """Test verbose JSON output formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[("http://example.com", 301), ("https://example.com", 200)],
            response_time=2.5,
            redirect_timing=[
                ("https://example.com", 301, 0.5),
                ("https://example.com", 200, 1.0),
            ],
        )

        result = format_json(status, verbose=True)
        data = json.loads(result)

        assert data["domain"] == "example.com"
        assert data["status"] == "200"
        assert data["message"] == "OK"
        assert data["response_time"] == 2.5

        # Check redirect chain
        assert len(data["redirect_chain"]) == 2
        assert data["redirect_chain"][0]["url"] == "http://example.com"
        assert data["redirect_chain"][0]["status"] == 301

        # Check redirect timing
        assert len(data["redirect_timing"]) == 2
        assert data["redirect_timing"][0]["time"] == 0.5

    def test_format_json_error_status(self):
        """Test JSON formatting for error status."""
        status = SiteStatus(
            domain="error.com",
            status="[timeout]",
            message="Request timed out",
            redirect_chain=[],
            response_time=0.0,
            redirect_timing=[],
        )

        result = format_json(status, verbose=False)
        data = json.loads(result)

        assert data["domain"] == "error.com"
        assert data["status"] == "[timeout]"
        assert data["message"] == "Request timed out"
        assert data["response_time"] == 0.0

    def test_format_json_list_multiple_sites(self):
        """Test JSON list formatting for multiple sites."""
        statuses = [
            SiteStatus(
                domain="example.com",
                status="200",
                message="OK",
                redirect_chain=[],
                response_time=1.5,
                redirect_timing=[],
            ),
            SiteStatus(
                domain="test.com",
                status="404",
                message="Not Found",
                redirect_chain=[],
                response_time=0.8,
                redirect_timing=[],
            ),
        ]

        result = format_json_list(statuses, verbose=False)
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["domain"] == "example.com"
        assert data[0]["status"] == "200"
        assert data[1]["domain"] == "test.com"
        assert data[1]["status"] == "404"

    def test_format_json_list_empty(self):
        """Test JSON list formatting with empty list."""
        result = format_json_list([], verbose=False)
        data = json.loads(result)
        assert data == []


class TestCSVOutput:
    """Test cases for CSV output formatting."""

    def test_format_csv_basic(self):
        """Test basic CSV output formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.234567,
            redirect_timing=[],
        )

        result = format_csv(status, verbose=False)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["domain"] == "example.com"
        assert rows[0]["status"] == "200"
        assert rows[0]["response_time"] == "1.235"

    def test_format_csv_verbose(self):
        """Test verbose CSV output formatting."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[("http://example.com", 301), ("https://example.com", 200)],
            response_time=2.5,
            redirect_timing=[],
        )

        result = format_csv(status, verbose=True)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        row = rows[0]
        assert row["domain"] == "example.com"
        assert row["status"] == "200"
        assert row["message"] == "OK"
        assert row["response_time"] == "2.5"
        assert row["redirect_count"] == "2"
        assert row["final_url"] == "https://example.com"

    def test_format_csv_no_redirects_verbose(self):
        """Test verbose CSV with no redirects."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.0,
            redirect_timing=[],
        )

        result = format_csv(status, verbose=True)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["redirect_count"] == "0"
        assert rows[0]["final_url"] == "example.com"

    def test_format_csv_list_multiple_sites(self):
        """Test CSV list formatting for multiple sites."""
        statuses = [
            SiteStatus(
                domain="example.com",
                status="200",
                message="OK",
                redirect_chain=[],
                response_time=1.5,
                redirect_timing=[],
            ),
            SiteStatus(
                domain="test.com",
                status="404",
                message="Not Found",
                redirect_chain=[],
                response_time=0.8,
                redirect_timing=[],
            ),
        ]

        result = format_csv_list(statuses, verbose=False)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["domain"] == "example.com"
        assert rows[0]["status"] == "200"
        assert rows[1]["domain"] == "test.com"
        assert rows[1]["status"] == "404"

    def test_format_csv_list_empty(self):
        """Test CSV list formatting with empty list."""
        result = format_csv_list([], verbose=False)
        assert result == ""

    def test_format_csv_list_verbose_headers(self):
        """Test CSV verbose headers are correct."""
        statuses = [
            SiteStatus(
                domain="example.com",
                status="200",
                message="OK",
                redirect_chain=[],
                response_time=1.0,
                redirect_timing=[],
            )
        ]

        result = format_csv_list(statuses, verbose=True)
        lines = result.split("\n")

        # Check header
        assert (
            lines[0].strip()
            == "domain,status,message,response_time,redirect_count,final_url"
        )


class TestOutputFormatIntegration:
    """Test integration with print_format function."""

    def test_print_format_json_output(self):
        """Test print_format with JSON output format."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.5,
            redirect_timing=[],
        )

        result = print_format(
            status, quiet=False, verbose=False, code=False, output_format="json"
        )

        # Should be valid JSON
        data = json.loads(result)
        assert data["domain"] == "example.com"
        assert data["status"] == "200"

    def test_print_format_csv_output(self):
        """Test print_format with CSV output format."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.5,
            redirect_timing=[],
        )

        result = print_format(
            status, quiet=False, verbose=False, code=False, output_format="csv"
        )

        # Should be valid CSV
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["domain"] == "example.com"

    def test_print_format_table_default(self):
        """Test print_format defaults to table format."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.5,
            redirect_timing=[],
        )

        result = print_format(
            status, quiet=False, verbose=False, code=False, output_format="table"
        )

        # Should contain tabulated output
        assert "example.com" in result
        assert "200" in result


class TestSpecialCases:
    """Test special cases and edge cases."""

    def test_json_special_characters(self):
        """Test JSON escaping of special characters."""
        status = SiteStatus(
            domain='example.com"test',
            status="200",
            message='OK with "quotes"',
            redirect_chain=[],
            response_time=1.0,
            redirect_timing=[],
        )

        result = format_json(status)
        data = json.loads(result)  # Should not raise
        assert 'example.com"test' in data["domain"]
        assert 'OK with "quotes"' in data["message"]

    def test_csv_comma_in_domain(self):
        """Test CSV handling of comma in domain."""
        status = SiteStatus(
            domain="example,test.com",
            status="200",
            message="OK, all good",
            redirect_chain=[],
            response_time=1.0,
            redirect_timing=[],
        )

        result = format_csv(status, verbose=True)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        assert rows[0]["domain"] == "example,test.com"
        assert rows[0]["message"] == "OK, all good"

    def test_json_with_null_redirect_chain(self):
        """Test JSON formatting when redirect_chain is None."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=None,
            response_time=1.0,
            redirect_timing=None,
        )

        # Should handle None gracefully
        result = format_json(status, verbose=True)
        data = json.loads(result)
        assert data["redirect_chain"] == []
        assert data["redirect_timing"] == []

    def test_csv_scientific_notation_time(self):
        """Test CSV handling of very small response times."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=0.0001234,
            redirect_timing=[],
        )

        result = format_csv(status)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)

        # Should be rounded to 3 decimal places
        assert rows[0]["response_time"] == "0.0"
