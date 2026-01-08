"""Test cases for httpcheck package initialization."""

import unittest
from unittest.mock import MagicMock, patch


class TestInit(unittest.TestCase):
    """Test cases for the httpcheck package initialization."""

    def test_package_imports(self):
        """Test that package imports work correctly."""
        from httpcheck import (
            VERSION,
            InvalidTLDException,
            SiteStatus,
            TLDManager,
            check_site,
            format_csv,
            format_json,
            main,
            notify,
            print_format,
            url_validation,
        )

        # Verify key exports are available
        assert main is not None
        assert check_site is not None
        assert VERSION is not None
        assert SiteStatus is not None

    @patch("httpcheck.cli.get_arguments")
    @patch("httpcheck.cli.check_tlds")
    @patch("httpcheck.cli._process_sites")
    @patch("httpcheck.cli._send_completion_notification")
    def test_main_cli_integration(
        self, mock_notify, mock_process, mock_check_tlds, mock_get_args
    ):
        """Test that main() calls the CLI properly."""
        from httpcheck import main

        # Mock the command line arguments
        mock_options = MagicMock()
        mock_options.site = ["https://example.com"]
        mock_options.verbose = False
        mock_options.output_format = "table"
        mock_get_args.return_value = mock_options

        # Mock TLD checking
        mock_check_tlds.return_value = 0

        # Mock site processing
        mock_process.return_value = (1, 0)  # 1 successful, 0 failures

        # Call main - it should work without errors
        try:
            main()
        except SystemExit:
            pass  # Main doesn't call sys.exit in normal operation

        # Verify the flow was called
        mock_get_args.assert_called_once()
        mock_check_tlds.assert_called_once()
        mock_process.assert_called_once()

    def test_version_string(self):
        """Test that version is correctly set."""
        from httpcheck import VERSION, __version__

        assert VERSION == "1.4.2"
        assert __version__ == "1.4.2"

    def test_main_callable(self):
        """Test that main() function is callable."""
        from httpcheck import main

        assert callable(main)
        assert main.__module__ == "httpcheck.cli"


if __name__ == "__main__":
    unittest.main()
