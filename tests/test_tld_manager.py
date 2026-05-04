import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, mock_open, patch

from httpcheck.common import InvalidTLDException
from httpcheck.tld_manager import TLDManager


class TestTLDManager(unittest.TestCase):

    def setUp(self):
        """Set up for the tests."""
        with patch("os.path.exists") as self.mock_exists:
            self.mock_exists.return_value = False
            TLDManager._instance = None  # Reset singleton
            self.tld_manager = TLDManager(verbose=True)

    # ------------------------------------------------------------------
    # Update TLD list
    # ------------------------------------------------------------------

    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.getmtime")
    def test_update_tld_list_success(
        self, mock_getmtime, mock_open_file, mock_requests_get
    ):
        """Test the successful update of the TLD list."""
        mock_response = MagicMock()
        mock_response.text = "com\norg\nnet"
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        self.tld_manager._update_tld_list()

        self.assertEqual(self.tld_manager.tlds, {"com", "org", "net"})
        mock_open_file.assert_called_with(
            self.tld_manager.cache_file, "w", encoding="utf-8"
        )

    @patch("requests.get")
    def test_update_tld_list_failure(self, mock_requests_get):
        """Test the failed update of the TLD list."""
        mock_requests_get.side_effect = Exception("Failed to fetch")

        with self.assertRaises(Exception):
            self.tld_manager._update_tld_list()

    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.getmtime")
    def test_update_tld_list_skips_comments_and_wildcards(
        self, mock_getmtime, mock_open_file, mock_requests_get
    ):
        """Lines starting with // or *. are skipped during update."""
        mock_response = MagicMock()
        mock_response.text = "com\n// comment\n*.example\norg\n"
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        self.tld_manager._update_tld_list()

        self.assertIn("com", self.tld_manager.tlds)
        self.assertIn("org", self.tld_manager.tlds)
        self.assertNotIn("// comment", self.tld_manager.tlds)
        self.assertNotIn("*.example", self.tld_manager.tlds)

    @patch("requests.get")
    def test_update_tld_list_empty_response_raises(self, mock_requests_get):
        """An empty downloaded list raises ValueError."""
        mock_response = MagicMock()
        mock_response.text = "// only comment\n\n"
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        with self.assertRaises(ValueError):
            self.tld_manager._update_tld_list()

    # ------------------------------------------------------------------
    # Load from local file
    # ------------------------------------------------------------------

    @patch("builtins.open", new_callable=mock_open, read_data="com\norg\nnet")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_load_from_local_file_success(
        self, mock_getmtime, mock_exists, mock_open_file
    ):
        """Test loading TLDs from a local file successfully."""
        mock_exists.return_value = True
        mock_getmtime.return_value = datetime.now().timestamp()

        self.tld_manager._load_from_local_file()

        self.assertEqual(self.tld_manager.tlds, {"com", "org", "net"})

    @patch("os.path.exists")
    def test_load_from_local_file_not_found(self, mock_exists):
        """Test loading TLDs from a non-existent local file."""
        mock_exists.return_value = False

        result = self.tld_manager._load_from_local_file()

        self.assertFalse(result)

    @patch("builtins.open", new_callable=mock_open, read_data="com\n// comment\norg")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_load_from_local_file_skips_comments(
        self, mock_getmtime, mock_exists, mock_open_file
    ):
        """Comments are skipped when loading from local file."""
        mock_exists.return_value = True
        mock_getmtime.return_value = datetime.now().timestamp()

        self.tld_manager._load_from_local_file()

        self.assertIn("com", self.tld_manager.tlds)
        self.assertIn("org", self.tld_manager.tlds)
        self.assertNotIn("// comment", self.tld_manager.tlds)

    # ------------------------------------------------------------------
    # Load from cache
    # ------------------------------------------------------------------

    def test_load_from_cache_missing_file(self):
        """Returns False when cache file does not exist."""
        with patch("os.path.exists", return_value=False):
            result = self.tld_manager._load_from_cache()
        self.assertFalse(result)

    def test_load_from_cache_expired(self):
        """Returns False when cache is older than cache_days."""
        old_mtime = (datetime.now() - timedelta(days=60)).timestamp()
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=old_mtime),
        ):
            result = self.tld_manager._load_from_cache()
        self.assertFalse(result)

    def test_load_from_cache_success(self):
        """Loads TLDs from a valid, fresh cache file."""
        cache_data = {
            "tlds": ["com", "org", "net"],
            "update_time": datetime.now().isoformat(),
        }
        fresh_mtime = datetime.now().timestamp()
        mock_file = mock_open(read_data=json.dumps(cache_data))

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=fresh_mtime),
            patch("builtins.open", mock_file),
        ):
            result = self.tld_manager._load_from_cache()

        self.assertTrue(result)
        self.assertEqual(self.tld_manager.tlds, {"com", "org", "net"})

    def test_load_from_cache_corrupt_json(self):
        """Returns False when cache JSON is corrupt."""
        fresh_mtime = datetime.now().timestamp()
        mock_file = mock_open(read_data="not-valid-json{{{")

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=fresh_mtime),
            patch("builtins.open", mock_file),
        ):
            result = self.tld_manager._load_from_cache()

        self.assertFalse(result)

    def test_load_from_cache_with_timestamp_key(self):
        """Handles legacy cache files that use 'timestamp' instead of 'update_time'."""
        cache_data = {
            "tlds": ["com"],
            "timestamp": datetime.now().timestamp(),
        }
        fresh_mtime = datetime.now().timestamp()
        mock_file = mock_open(read_data=json.dumps(cache_data))

        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getmtime", return_value=fresh_mtime),
            patch("builtins.open", mock_file),
        ):
            result = self.tld_manager._load_from_cache()

        self.assertTrue(result)
        self.assertIsNotNone(self.tld_manager.update_time)

    # ------------------------------------------------------------------
    # Save to cache
    # ------------------------------------------------------------------

    def test_save_to_cache_success(self):
        """Saves TLDs to cache without raising."""
        self.tld_manager.tlds = {"com", "org"}
        self.tld_manager.update_time = datetime.now()

        with patch("builtins.open", mock_open()) as mock_file:
            self.tld_manager._save_to_cache()
            mock_file.assert_called_with(
                self.tld_manager.cache_file, "w", encoding="utf-8"
            )

    def test_save_to_cache_os_error(self):
        """OSError during save is caught and does not propagate."""
        self.tld_manager.tlds = {"com"}
        self.tld_manager.update_time = datetime.now()

        with patch("builtins.open", side_effect=OSError("permission denied")):
            # Should not raise
            self.tld_manager._save_to_cache()

    # ------------------------------------------------------------------
    # Validate TLD
    # ------------------------------------------------------------------

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

    def test_validate_tld_empty_list_raises(self):
        """validate_tld raises when the TLD set is empty."""
        self.tld_manager.tlds = set()
        with self.assertRaises(InvalidTLDException):
            self.tld_manager.validate_tld("http://example.com")

    def test_validate_tld_wildcard_match(self):
        """Wildcard TLD entry matches subdomains."""
        self.tld_manager.tlds = {"*.ck", "com"}
        # *.ck means any second-level is valid under .ck
        result = self.tld_manager.validate_tld("http://sub.ck")
        self.assertIsNotNone(result)

    def test_validate_tld_exception_candidate(self):
        """Exception candidate (! prefix) overrides wildcard."""
        # www.ck is excluded from *.ck by the public suffix list using !www.ck
        self.tld_manager.tlds = {"*.ck", "!www.ck", "com"}
        result = self.tld_manager.validate_tld("http://www.ck")
        self.assertIsNotNone(result)

    def test_validate_tld_subdomain(self):
        """Validates domain with multiple subdomains."""
        self.tld_manager.tlds = {"com"}
        result = self.tld_manager.validate_tld("http://sub.example.com")
        self.assertIsNotNone(result)

    def test_validate_tld_no_scheme(self):
        """Handles URLs without scheme."""
        self.tld_manager.tlds = {"com"}
        result = self.tld_manager.validate_tld("example.com")
        self.assertEqual(result, "example.com")

    # ------------------------------------------------------------------
    # Singleton behaviour
    # ------------------------------------------------------------------

    def test_singleton_same_instance(self):
        """Two instantiations with the same cache_dir return the same object."""
        TLDManager._instance = None
        with (
            patch("os.path.exists", return_value=False),
            patch("os.makedirs"),
            patch.object(TLDManager, "_load_tld_data"),
        ):
            inst1 = TLDManager(cache_dir="/fake/test_cache")
            inst2 = TLDManager(cache_dir="/fake/test_cache")
        self.assertIs(inst1, inst2)

    def test_singleton_new_instance_on_cache_dir_change(self):
        """A different cache_dir forces a new singleton instance."""
        TLDManager._instance = None
        with (
            patch("os.path.exists", return_value=False),
            patch("os.makedirs"),
            patch.object(TLDManager, "_load_tld_data"),
        ):
            inst1 = TLDManager(cache_dir="/fake/cache_a")
            inst2 = TLDManager(cache_dir="/fake/cache_b")
        self.assertIsNot(inst1, inst2)

    # ------------------------------------------------------------------
    # _load_tld_data silent exception fix
    # ------------------------------------------------------------------

    @patch("requests.get")
    def test_load_tld_data_logs_on_update_failure_after_local_load(
        self, mock_requests_get
    ):
        """When local file loads empty TLDs and network update fails, logs warning."""
        mock_requests_get.side_effect = Exception("network error")

        with patch("os.path.exists", return_value=False), patch("os.makedirs"):
            TLDManager._instance = None
            mgr = TLDManager.__new__(TLDManager)
            mgr._initialized = False
            mgr.verbose = True
            mgr.warning_only = False
            mgr.cache_days = 30
            mgr.cache_path = "/fake/test"
            mgr.cache_file = "/fake/test/tld_cache.json"
            mgr.tlds = set()
            mgr.update_time = None

        # Simulate: cache_loaded=False, local_loaded=True but tlds empty
        with (
            patch.object(mgr, "_load_from_cache", return_value=False),
            patch.object(mgr, "_load_from_local_file", return_value=True),
            patch.object(mgr, "_update_tld_list", side_effect=Exception("net fail")),
        ):
            # Should not raise; the bare except is now logged
            mgr._load_tld_data(force_update=False)


if __name__ == "__main__":
    unittest.main()
