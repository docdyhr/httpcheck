"""Test cases for the common module."""

import pytest

from httpcheck.common import VERSION, InvalidTLDException, SiteStatus


class TestSiteStatus:
    """Test cases for the SiteStatus class."""

    def test_site_status_creation_basic(self):
        """Test basic SiteStatus creation."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.5,
            redirect_timing=[],
        )

        assert status.domain == "example.com"
        assert status.status == "200"
        assert status.message == "OK"
        assert status.response_time == 1.5
        assert status.redirect_chain == []
        assert status.redirect_timing == []

    def test_site_status_final_url_no_redirects(self):
        """Test final_url property without redirects."""
        # Test with plain domain
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.0,
            redirect_timing=[],
        )
        assert status.final_url == "https://example.com"

        # Test with http:// prefix
        status = SiteStatus(
            domain="http://example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.0,
            redirect_timing=[],
        )
        assert status.final_url == "http://example.com"

        # Test with https:// prefix
        status = SiteStatus(
            domain="https://example.com",
            status="200",
            message="OK",
            redirect_chain=[],
            response_time=1.0,
            redirect_timing=[],
        )
        assert status.final_url == "https://example.com"

    def test_site_status_final_url_with_redirects(self):
        """Test final_url property with redirects."""
        status = SiteStatus(
            domain="example.com",
            status="200",
            message="OK",
            redirect_chain=[
                ("http://example.com", 301),
                ("https://example.com", 301),
                ("https://www.example.com", 200),
            ],
            response_time=2.0,
            redirect_timing=[
                ("https://example.com", 301, 0.5),
                ("https://www.example.com", 200, 0.5),
            ],
        )
        assert status.final_url == "https://www.example.com"

    def test_site_status_with_error(self):
        """Test SiteStatus with error."""
        status = SiteStatus(
            domain="invalid.example",
            status="Error",
            message="Connection timeout",
            redirect_chain=[],
            response_time=0.0,
            redirect_timing=[],
        )

        assert status.domain == "invalid.example"
        assert status.status == "Error"
        assert status.message == "Connection timeout"
        assert status.response_time == 0.0
        assert status.final_url == "https://invalid.example"

    def test_site_status_with_complex_redirects(self):
        """Test SiteStatus with complex redirect chains."""
        status = SiteStatus(
            domain="short.link",
            status="200",
            message="OK",
            redirect_chain=[
                ("http://short.link", 301),
                ("https://short.link", 302),
                ("https://example.com/page", 301),
                ("https://www.example.com/page", 200),
            ],
            response_time=3.5,
            redirect_timing=[
                ("https://short.link", 301, 0.5),
                ("https://example.com/page", 302, 0.8),
                ("https://www.example.com/page", 301, 0.7),
            ],
        )

        assert status.final_url == "https://www.example.com/page"
        assert len(status.redirect_chain) == 4
        assert status.redirect_chain[0][1] == 301
        assert status.redirect_chain[-1][1] == 200

    def test_site_status_minimal_creation(self):
        """Test SiteStatus creation with minimal fields."""
        # SiteStatus should work with just required fields
        status = SiteStatus(domain="example.com", status="200", message="OK")

        assert status.domain == "example.com"
        assert status.status == "200"
        assert status.message == "OK"
        assert status.redirect_chain == []
        assert status.response_time == 0.0
        assert status.redirect_timing == []


class TestInvalidTLDException:
    """Test cases for the InvalidTLDException class."""

    def test_invalid_tld_exception_creation(self):
        """Test InvalidTLDException creation."""
        exc = InvalidTLDException("Invalid TLD: .invalid")
        assert str(exc) == "Invalid TLD: .invalid"
        assert isinstance(exc, Exception)

    def test_invalid_tld_exception_raise(self):
        """Test raising InvalidTLDException."""
        with pytest.raises(InvalidTLDException) as exc_info:
            raise InvalidTLDException("example.invalid has an invalid TLD")

        assert "example.invalid has an invalid TLD" in str(exc_info.value)


class TestConstants:
    """Test cases for module constants."""

    def test_version_constant(self):
        """Test VERSION constant."""
        assert VERSION is not None
        assert isinstance(VERSION, str)
        # Version should follow semantic versioning
        assert VERSION.count(".") >= 1  # At least major.minor

        # Check version format
        parts = VERSION.split(".")
        for part in parts:
            # Allow for pre-release versions and digits
            assert part.isdigit() or "-" in part or part.isalnum()

    def test_status_codes(self):
        """Test STATUS_CODES constant."""
        from httpcheck.common import STATUS_CODES

        # Check if common HTTP status codes are defined
        assert "200" in STATUS_CODES
        assert STATUS_CODES["200"] == "OK"

        assert "404" in STATUS_CODES
        assert STATUS_CODES["404"] == "Not Found"

        assert "500" in STATUS_CODES
        assert STATUS_CODES["500"] == "Internal Server Error"

        # Check that all status codes are strings
        for code, message in STATUS_CODES.items():
            assert isinstance(code, str)
            assert isinstance(message, str)

    def test_module_exports(self):
        """Test that the module exports expected items."""
        from httpcheck import common

        # Check module attributes
        assert hasattr(common, "VERSION")
        assert hasattr(common, "SiteStatus")
        assert hasattr(common, "InvalidTLDException")
        assert hasattr(common, "STATUS_CODES")

        # Check that they are the expected types
        assert isinstance(common.VERSION, str)
        assert isinstance(common.STATUS_CODES, dict)
