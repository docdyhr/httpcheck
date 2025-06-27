"""TLD validation and management for httpcheck."""

import json
import os
from datetime import datetime
from urllib.parse import urlparse

import requests

from .common import InvalidTLDException


class TLDManager:
    """Manager for TLD (Top-Level Domain) operations with caching and auto-updates.

    This class handles TLD validation against the Public Suffix List with:
    - Memory caching for better performance
    - Disk-based caching for persistence between runs
    - Automatic updates of the TLD list
    - Flexible configuration options
    """

    # Singleton instance
    _instance = None

    # Default TLD source URL from Public Suffix List
    TLD_SOURCE_URL = "https://publicsuffix.org/list/public_suffix_list.dat"

    # Default cache settings
    DEFAULT_CACHE_PATH = os.path.join(os.path.expanduser("~"), ".httpcheck")
    DEFAULT_CACHE_FILE = "tld_cache.json"
    DEFAULT_CACHE_DAYS = 30

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of TLDManager exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        force_update=False,
        cache_days=None,
        verbose=False,
        warning_only=False,
    ):
        """Initialize the TLD manager.

        Args:
            force_update: Whether to force an update of the TLD list
            cache_days: Number of days to keep the cache valid (default: 30)
            verbose: Whether to print verbose output
            warning_only: If True, invalid TLDs will produce warnings instead of errors
        """
        # Skip initialization if already initialized (singleton pattern)
        if self._initialized:
            return

        self.verbose = verbose
        self.warning_only = warning_only
        self.cache_days = cache_days or self.DEFAULT_CACHE_DAYS
        self.cache_path = self.DEFAULT_CACHE_PATH
        self.cache_file = os.path.join(self.cache_path, self.DEFAULT_CACHE_FILE)
        self.tlds = set()  # Use a set for O(1) lookups
        self.update_time = None

        # Ensure cache directory exists
        os.makedirs(self.cache_path, exist_ok=True)

        # Load TLD data with optional update
        self._load_tld_data(force_update)
        self._initialized = True

    def _load_tld_data(self, force_update=False):
        """Load TLD data from cache or source file."""
        # Check if we need to update based on cache age or forced update
        if force_update or not self._load_from_cache():
            try:
                self._update_tld_list()
            except Exception as e:
                if self.verbose:
                    print(f"[-] Error updating TLD list: {str(e)}")
                # If update fails and we don't have a cache, try to load from local file
                if not self.tlds:
                    self._load_from_local_file()

    def _load_from_cache(self):
        """Load TLD data from the cache file if it exists and is not expired."""
        try:
            if not os.path.exists(self.cache_file):
                return False

            # Check if cache is expired
            cache_age = datetime.now() - datetime.fromtimestamp(
                os.path.getmtime(self.cache_file)
            )
            if cache_age.days > self.cache_days:
                if self.verbose:
                    print(
                        f"[*] TLD cache is {cache_age.days} days old (max: {self.cache_days}). Refreshing..."
                    )
                return False

            # Load cache from JSON
            with open(self.cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)
                self.tlds = set(cache_data["tlds"])
                self.update_time = datetime.fromisoformat(cache_data["update_time"])

            if self.verbose:
                print(
                    f"[*] Loaded {len(self.tlds)} TLDs from cache (last updated: {self.update_time})"
                )
            return True

        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            if self.verbose:
                print(f"[-] Error loading TLD cache: {str(e)}")
            return False

    def _save_to_cache(self):
        """Save TLD data to the cache file."""
        try:
            cache_data = {
                "tlds": list(self.tlds),
                "update_time": self.update_time.isoformat(),
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

            if self.verbose:
                print(f"[*] Saved {len(self.tlds)} TLDs to cache")

        except (OSError, TypeError, ValueError) as e:
            if self.verbose:
                print(f"[-] Error saving TLD cache: {str(e)}")

    def _update_tld_list(self):
        """Update the TLD list from the Public Suffix List."""
        if self.verbose:
            print("[*] Updating TLD list from Public Suffix List...")

        try:
            # Use requests instead of urllib for better error handling and timeouts
            response = requests.get(self.TLD_SOURCE_URL, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors

            # Process the TLD list
            tlds = set()
            for line in response.text.splitlines():
                line = line.strip()
                # Skip empty lines, comments, and private domains
                if not line or line.startswith("//") or line.startswith("*."):
                    continue
                tlds.add(line)

            # Update only if we got a non-empty list
            if tlds:
                self.tlds = tlds
                self.update_time = datetime.now()
                self._save_to_cache()

                if self.verbose:
                    print(f"[*] Updated TLD list with {len(self.tlds)} entries")
            else:
                raise ValueError("Downloaded TLD list is empty")

        except Exception as e:
            if self.verbose:
                print(f"[-] Failed to update TLD list: {str(e)}")
            raise

    def _load_from_local_file(self):
        """Fall back to loading TLDs from the local effective_tld_names.dat file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            tld_file = os.path.join(script_dir, "..", "effective_tld_names.dat")

            if not os.path.exists(tld_file):
                if self.verbose:
                    print(f"[-] Local TLD file not found: {tld_file}")
                return False

            tlds = set()
            with open(tld_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("//"):
                        tlds.add(line)

            self.tlds = tlds
            self.update_time = datetime.fromtimestamp(os.path.getmtime(tld_file))

            if self.verbose:
                print(
                    f"[*] Loaded {len(self.tlds)} TLDs from local file (last modified: {self.update_time})"
                )

            # Save to cache for future use
            self._save_to_cache()
            return True

        except Exception as e:
            if self.verbose:
                print(f"[-] Error loading local TLD file: {str(e)}")
            return False

    def validate_tld(self, url):
        """Validate that a URL has a valid top-level domain.

        Args:
            url: The URL to validate

        Returns:
            The valid TLD if found

        Raises:
            InvalidTLDException: If the TLD is invalid and warning_only is False
        """
        if not self.tlds:
            raise InvalidTLDException("TLD list is empty. Cannot validate TLDs.")

        parsed_url = urlparse(url)
        url_elements = parsed_url.netloc.split(".")

        for i in range(-len(url_elements), 0):
            last_i_elements = url_elements[i:]
            candidate = ".".join(last_i_elements)
            wildcard_candidate = ".".join(["*"] + last_i_elements[1:])
            exception_candidate = f"!{candidate}"

            if exception_candidate in self.tlds:
                return ".".join(url_elements[i:])
            if candidate in self.tlds or wildcard_candidate in self.tlds:
                return ".".join(url_elements[i - 1 :])

        error_msg = f"[-] Domain not in global list of TLDs: '{url}'"
        if self.warning_only:
            if self.verbose:
                print(f"[!] WARNING: {error_msg}")
            return None
        else:
            raise InvalidTLDException(error_msg)
