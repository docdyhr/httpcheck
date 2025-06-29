"""Test cases for the file_handler module."""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from httpcheck.file_handler import FileInputHandler, url_validation


class TestURLValidation:
    """Test cases for the url_validation function."""

    def test_url_validation_valid_urls(self):
        """Test validation of valid URLs."""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://subdomain.example.com",
            "https://example.com/path",
            "http://example.com:8080",
            "https://example.com/path?query=value",
            "http://192.168.1.1",
            "https://example.co.uk",
        ]

        for url in valid_urls:
            result = url_validation(url)
            assert result == url, f"URL validation failed for {url}"

    def test_url_validation_adds_protocol(self):
        """Test that url_validation adds http:// to URLs without protocol."""
        urls_without_protocol = [
            ("example.com", "http://example.com"),
            ("subdomain.example.com", "http://subdomain.example.com"),
            ("example.com/path", "http://example.com/path"),
            ("example.com:8080", "http://example.com:8080"),
            ("192.168.1.1", "http://192.168.1.1"),
        ]

        for url, expected in urls_without_protocol:
            result = url_validation(url)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_url_validation_invalid_urls(self):
        """Test validation of invalid URLs."""
        import argparse

        invalid_urls = [
            "not a url",
            "http://",
            "https://",
            "://example.com",
            "http//example.com",
            "https:/example.com",
            "example",
            "http://example",
            "https://example.",
            "",
            " ",
            "http:// example.com",  # Space in URL
        ]

        for url in invalid_urls:
            with pytest.raises(argparse.ArgumentTypeError):
                url_validation(url)

    def test_url_validation_ftp_protocol(self):
        """Test that FTP protocol is not accepted."""
        # FTP gets prepended with http:// making it invalid
        with pytest.raises(argparse.ArgumentTypeError):
            url_validation("ftp://example.com")


class TestFileInputHandler:
    """Test cases for the FileInputHandler class."""

    def test_file_parsing_basic(self):
        """Test basic file parsing with valid URLs."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com\n")
            f.write("https://google.com\n")
            f.write("http://github.com\n")
            f.write("\n")  # Empty line
            f.write("  example.org  \n")  # With whitespace
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            assert len(results) == 4
            assert results[0] == "http://example.com"
            assert results[1] == "https://google.com"
            assert results[2] == "http://github.com"
            assert results[3] == "http://example.org"

            # Check counters
            assert handler.valid_count == 4
            assert handler.empty_count == 1
            assert handler.comment_count == 0
            assert handler.error_count == 0
        finally:
            Path(temp_path).unlink()

    def test_file_parsing_with_comments(self):
        """Test file parsing with various comment styles."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("# This is a comment\n")
            f.write("example.com\n")
            f.write("// Another comment\n")
            f.write("google.com\n")
            f.write("# example.org # inline comment\n")
            f.write("github.com // inline comment\n")
            temp_path = f.name

        try:
            # Test with both comment styles
            handler = FileInputHandler(temp_path, comment_style="both")
            results = list(handler.parse())

            assert len(results) == 3
            assert results[0] == "http://example.com"
            assert results[1] == "http://google.com"
            assert results[2] == "http://github.com"
            assert (
                handler.comment_count == 4
            )  # "# example.org # inline comment" counts as comment

            # Test with hash comments only
            handler = FileInputHandler(temp_path, comment_style="hash")
            results = list(handler.parse())
            # "// Another comment" and "github.com // inline comment" are processed as URLs
            assert len(results) == 2  # example.com, google.com
            assert (
                handler.error_count == 2
            )  # "// Another comment" and "github.com // inline comment" are invalid

            # Test with slash comments only
            handler = FileInputHandler(temp_path, comment_style="slash")
            results = list(handler.parse())
            assert len(results) == 3  # example.com, google.com, github.com
            assert (
                handler.comment_count == 2
            )  # "// Another comment" and inline // comment
        finally:
            Path(temp_path).unlink()

    def test_file_parsing_inline_comments(self):
        """Test file parsing with inline comments."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com # Production server\n")
            f.write("staging.example.com // Staging server\n")
            f.write("test.example.com # Test server // Multiple comments\n")
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            assert len(results) == 3
            assert results[0] == "http://example.com"
            assert results[1] == "http://staging.example.com"
            assert results[2] == "http://test.example.com"
            assert handler.comment_count == 3
        finally:
            Path(temp_path).unlink()

    def test_file_parsing_with_errors(self):
        """Test file parsing with invalid URLs."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com\n")
            f.write("not a valid url\n")
            f.write("http://\n")
            f.write("google.com\n")
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            assert len(results) == 2
            assert results[0] == "http://example.com"
            assert results[1] == "http://google.com"
            assert handler.error_count == 2
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        handler = FileInputHandler("/non/existent/file.txt")

        # Should print error but not raise exception
        with patch("builtins.print") as mock_print:
            results = list(handler.parse())
            assert len(results) == 0
            assert mock_print.called
            assert "Error reading file" in str(mock_print.call_args)

    def test_file_parsing_verbose_mode(self):
        """Test file parsing with verbose output."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com\n")
            f.write("# Comment\n")
            f.write("\n")
            f.write("invalid url\n")
            temp_path = f.name

        try:
            # Capture print output
            with patch("builtins.print") as mock_print:
                handler = FileInputHandler(temp_path, verbose=True)
                list(handler.parse())  # Consume generator to trigger summary print

                # Should print summary
                assert mock_print.called
                call_args = str(mock_print.call_args_list)
                assert "Lines processed: 4" in call_args
                assert "Valid URLs: 1" in call_args
                assert "Comments: 1" in call_args
                assert "Empty lines: 1" in call_args
                assert "Errors: 1" in call_args
        finally:
            Path(temp_path).unlink()

    def test_file_parsing_special_cases(self):
        """Test file parsing with special cases."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("# Header comment\n")
            f.write("\n")
            f.write("   \n")  # Whitespace only
            f.write("example.com\n")
            f.write("EXAMPLE.COM\n")  # Uppercase
            f.write("example.com:443\n")  # With port
            f.write("example.com/path/to/page\n")  # With path
            f.write("example.com?query=value\n")  # With query
            f.write("http://example.com#anchor\n")  # With anchor
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            assert len(results) == 6  # URL with anchor now passes validation
            assert "http://example.com" in results
            assert "http://EXAMPLE.COM" in results
            assert "http://example.com:443" in results
            assert "http://example.com/path/to/page" in results
            assert "http://example.com?query=value" in results
            # "http://example.com#anchor" fails validation
        finally:
            Path(temp_path).unlink()

    def test_file_input_handler_attributes(self):
        """Test FileInputHandler attributes and initialization."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com\n")
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path, verbose=True, comment_style="hash")

            assert handler.file_path == temp_path
            assert handler.verbose is True
            assert handler.comment_style == "hash"
            assert handler.line_count == 0
            assert handler.valid_count == 0
            assert handler.comment_count == 0
            assert handler.empty_count == 0
            assert handler.error_count == 0

            # Process the file
            list(handler.parse())

            assert handler.line_count == 1
            assert handler.valid_count == 1
        finally:
            Path(temp_path).unlink()

    def test_empty_file(self):
        """Test handling of empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            assert len(results) == 0
            assert handler.line_count == 0
        finally:
            Path(temp_path).unlink()

    def test_file_with_only_comments(self):
        """Test file containing only comments."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("# Comment 1\n")
            f.write("// Comment 2\n")
            f.write("# Comment 3\n")
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            assert len(results) == 0
            assert handler.comment_count == 3
            assert handler.valid_count == 0
        finally:
            Path(temp_path).unlink()

    def test_mixed_comment_styles(self):
        """Test handling of mixed comment styles."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com # hash comment\n")
            f.write("google.com // slash comment\n")
            f.write("github.com # hash // mixed\n")
            temp_path = f.name

        try:
            # Test hash only
            handler = FileInputHandler(temp_path, comment_style="hash")
            results = list(handler.parse())
            assert len(results) == 2  # google.com is not parsed with hash-only style
            assert handler.comment_count == 2  # Only hash comments counted

            # Test slash only
            handler = FileInputHandler(temp_path, comment_style="slash")
            results = list(handler.parse())
            assert (
                len(results) == 1
            )  # Only google.com parsed (others have # which isn't stripped)
            assert (
                handler.comment_count == 2
            )  # "// slash comment" and "// mixed" counted

            # Test both
            handler = FileInputHandler(temp_path, comment_style="both")
            results = list(handler.parse())
            assert len(results) == 3
            assert handler.comment_count == 3  # All comments counted
        finally:
            Path(temp_path).unlink()

    def test_url_with_spaces(self):
        """Test handling of URLs with spaces."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com/path with spaces\n")
            f.write("  spaced.com  \n")
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            # Both URLs are now valid - spaces are handled by auto-fix
            assert len(results) == 2
            assert results[0] == "http://example.com/path with spaces"
            assert results[1] == "http://spaced.com"
            assert handler.error_count == 0
        finally:
            Path(temp_path).unlink()

    def test_error_printing_non_verbose(self):
        """Test that errors are not printed in non-verbose mode."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("invalid url\n")
            temp_path = f.name

        try:
            with patch("builtins.print") as mock_print:
                handler = FileInputHandler(temp_path, verbose=False)
                list(handler.parse())

                # Should not print error in non-verbose mode
                assert not mock_print.called
                assert handler.error_count == 1
        finally:
            Path(temp_path).unlink()

    def test_comment_after_empty_space(self):
        """Test comments after whitespace are handled correctly."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("example.com    # comment after spaces\n")
            f.write("google.com\t\t// comment after tabs\n")
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            results = list(handler.parse())

            assert len(results) == 2
            assert results[0] == "http://example.com"
            assert results[1] == "http://google.com"
            assert handler.comment_count == 2
        finally:
            Path(temp_path).unlink()
