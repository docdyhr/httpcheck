import json
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, mock_open, patch

from httpcheck.common import InvalidTLDException
from httpcheck.tld_manager import TLDManager


class TestTLDManager(unittest.TestCase):

    def setUp(self):
        """Set up for the tests."""
        # We patch os.path.exists to avoid side effects from previous tests
        with patch("os.path.exists") as self.mock_exists:
            self.mock_exists.return_value = False
            TLDManager._instance = None  # Reset singleton
            self.tld_manager = TLDManager(verbose=True)

    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.getmtime")
    def test_update_tld_list_success(
        self, mock_getmtime, mock_open_file, mock_requests_get
    ):
        """Test the successful update of the TLD list."""
        # Mock the requests.get call
        mock_response = MagicMock()
        mock_response.text = "com\norg\nnet"
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        # Call the update method
        self.tld_manager._update_tld_list()

        # Assert that the TLD list is updated
        self.assertEqual(self.tld_manager.tlds, {"com", "org", "net"})
        mock_open_file.assert_called_with(
            self.tld_manager.cache_file, "w", encoding="utf-8"
        )

    @patch("requests.get")
    def test_update_tld_list_failure(self, mock_requests_get):
        """Test the failed update of the TLD list."""
        # Mock the requests.get call to raise an exception
        mock_requests_get.side_effect = Exception("Failed to fetch")

        # Call the update method and assert that it raises an exception
        with self.assertRaises(Exception):
            self.tld_manager._update_tld_list()

    @patch("builtins.open", new_callable=mock_open, read_data="com\norg\nnet")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_load_from_local_file_success(
        self, mock_getmtime, mock_exists, mock_open_file
    ):
        """Test loading TLDs from a local file successfully."""
        mock_exists.return_value = True
        mock_getmtime.return_value = datetime.now().timestamp()

        # Call the load from local file method
        self.tld_manager._load_from_local_file()

        # Assert that the TLD list is loaded
        self.assertEqual(self.tld_manager.tlds, {"com", "org", "net"})

    @patch("os.path.exists")
    def test_load_from_local_file_not_found(self, mock_exists):
        """Test loading TLDs from a non-existent local file."""
        mock_exists.return_value = False

        # Call the load from local file method
        result = self.tld_manager._load_from_local_file()

        # Assert that the method returns False
        self.assertFalse(result)

    def test_validate_tld_success(self):
        """Test successful TLD validation."""
        self.tld_manager.tlds = {"com", "org", "net"}
        self.assertEqual(
            self.tld_manager.validate_tld("http://example.com"), "example.com"
        )

    def test_validate_tld_failure(self):
        """Test failed TLD validation."""
        self.tld_manager.tlds = {"com", "org", "net"}
        with self.assertRaises(InvalidTLDException):
            self.tld_manager.validate_tld("http://example.invalid")

    def test_validate_tld_warning(self):
        """Test TLD validation with warning only."""
        self.tld_manager.tlds = {"com", "org", "net"}
        self.tld_manager.warning_only = True
        self.assertIsNone(self.tld_manager.validate_tld("http://example.invalid"))


if __name__ == "__main__":
    unittest.main()
