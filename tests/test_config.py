"""Tests for httpcheck/config.py — configuration file support."""

import pathlib
from unittest.mock import patch

import pytest

from httpcheck.config import (
    DEFAULT_CONFIG,
    _extract_cli_defaults,
    _headers_to_list,
    _merge_configs,
    _parse_toml_file,
    get_notifications_config,
    load_config,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_TOML = b"""
[defaults]
timeout = 10.0
"""

FULL_TOML = b"""
[defaults]
timeout = 10.0
retries = 5
follow_redirects = "never"
output_format = "json"
verify_ssl = false
workers = 20
retry_delay = 2.0
max_redirects = 5

[headers]
User-Agent = "mybot/1.0"
Accept = "application/json"

[notifications]
enabled = false
on_failure = true
sound = "Glass"
"""

INVALID_TOML = b"this is not [ valid toml"

UNKNOWN_KEYS_TOML = b"""
[defaults]
timeout = 3.0
unknown_key = "ignored"

[notifications]
enabled = true
bad_key = "also ignored"
"""


# ---------------------------------------------------------------------------
# _parse_toml_file
# ---------------------------------------------------------------------------


class TestParseTomlFile:
    def test_returns_dict_for_valid_file(self, tmp_path):
        p = tmp_path / ".httpcheck.toml"
        p.write_bytes(MINIMAL_TOML)
        result = _parse_toml_file(p)
        assert result == {"defaults": {"timeout": 10.0}}

    def test_returns_empty_for_missing_file(self, tmp_path):
        result = _parse_toml_file(tmp_path / "nonexistent.toml")
        assert result == {}

    def test_returns_empty_and_warns_for_invalid_toml(self, tmp_path):
        p = tmp_path / ".httpcheck.toml"
        p.write_bytes(INVALID_TOML)
        with pytest.warns(UserWarning, match="Could not parse"):
            result = _parse_toml_file(p)
        assert result == {}


# ---------------------------------------------------------------------------
# _merge_configs
# ---------------------------------------------------------------------------


class TestMergeConfigs:
    def test_project_overrides_user_per_key(self):
        user = {"defaults": {"timeout": 5.0, "retries": 2}}
        project = {"defaults": {"timeout": 15.0}}
        merged = _merge_configs(user, project)
        assert merged["defaults"]["timeout"] == 15.0
        assert merged["defaults"]["retries"] == 2

    def test_keys_only_in_user_are_preserved(self):
        user = {"defaults": {"retries": 3}}
        project = {"headers": {"User-Agent": "bot"}}
        merged = _merge_configs(user, project)
        assert merged["defaults"]["retries"] == 3
        assert merged["headers"]["User-Agent"] == "bot"

    def test_empty_base_returns_override(self):
        project = {"defaults": {"timeout": 8.0}}
        assert _merge_configs({}, project) == project

    def test_empty_override_returns_base(self):
        user = {"defaults": {"timeout": 8.0}}
        assert _merge_configs(user, {}) == user


# ---------------------------------------------------------------------------
# _headers_to_list
# ---------------------------------------------------------------------------


class TestHeadersToList:
    def test_converts_dict_to_name_value_strings(self):
        result = _headers_to_list({"User-Agent": "bot", "Accept": "text/html"})
        assert "User-Agent: bot" in result
        assert "Accept: text/html" in result

    def test_empty_dict_returns_empty_list(self):
        assert _headers_to_list({}) == []


# ---------------------------------------------------------------------------
# _extract_cli_defaults
# ---------------------------------------------------------------------------


class TestExtractCliDefaults:
    def test_extracts_all_supported_defaults_keys(self):
        raw = {
            "defaults": {
                "timeout": 10.0,
                "retries": 4,
                "follow_redirects": "never",
                "output_format": "json",
                "verify_ssl": False,
                "workers": 8,
                "retry_delay": 0.5,
                "max_redirects": 10,
            }
        }
        result = _extract_cli_defaults(raw)
        assert result["timeout"] == 10.0
        assert result["retries"] == 4
        assert result["follow_redirects"] == "never"
        assert result["output_format"] == "json"
        assert result["verify_ssl"] is False
        assert result["workers"] == 8
        assert result["retry_delay"] == 0.5
        assert result["max_redirects"] == 10

    def test_ignores_unknown_defaults_keys(self):
        raw = {"defaults": {"timeout": 3.0, "unknown": "value"}}
        with pytest.warns(UserWarning, match=r"\[defaults\].unknown"):
            result = _extract_cli_defaults(raw)
        assert "unknown" not in result

    def test_converts_headers_section(self):
        raw = {"headers": {"User-Agent": "mybot"}}
        result = _extract_cli_defaults(raw)
        assert result["headers"] == ["User-Agent: mybot"]

    def test_empty_raw_returns_empty(self):
        assert _extract_cli_defaults({}) == {}

    def test_missing_sections_skipped_gracefully(self):
        raw = {"defaults": {"timeout": 1.0}}
        result = _extract_cli_defaults(raw)
        assert "headers" not in result


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_returns_empty_when_no_files_exist(self, tmp_path):
        with (
            patch("httpcheck.config.pathlib.Path.home", return_value=tmp_path),
            patch("httpcheck.config.pathlib.Path.cwd", return_value=tmp_path),
        ):
            assert load_config() == {}

    def test_loads_user_config(self, tmp_path):
        (tmp_path / ".httpcheck.toml").write_bytes(MINIMAL_TOML)
        with (
            patch("httpcheck.config.pathlib.Path.home", return_value=tmp_path),
            patch(
                "httpcheck.config.pathlib.Path.cwd",
                return_value=pathlib.Path("/nonexistent_cwd_xyz"),
            ),
        ):
            result = load_config()
        assert result["timeout"] == 10.0

    def test_loads_project_config(self, tmp_path):
        (tmp_path / ".httpcheck.toml").write_bytes(MINIMAL_TOML)
        with (
            patch(
                "httpcheck.config.pathlib.Path.home",
                return_value=pathlib.Path("/nonexistent_home_xyz"),
            ),
            patch("httpcheck.config.pathlib.Path.cwd", return_value=tmp_path),
        ):
            result = load_config()
        assert result["timeout"] == 10.0

    def test_project_overrides_user(self, tmp_path):
        user_dir = tmp_path / "home"
        proj_dir = tmp_path / "proj"
        user_dir.mkdir()
        proj_dir.mkdir()
        (user_dir / ".httpcheck.toml").write_bytes(
            b"[defaults]\ntimeout = 5.0\nretries = 2\n"
        )
        (proj_dir / ".httpcheck.toml").write_bytes(b"[defaults]\ntimeout = 30.0\n")
        with (
            patch("httpcheck.config.pathlib.Path.home", return_value=user_dir),
            patch("httpcheck.config.pathlib.Path.cwd", return_value=proj_dir),
        ):
            result = load_config()
        assert result["timeout"] == 30.0
        assert result["retries"] == 2  # preserved from user config

    def test_full_config_loads_all_sections(self, tmp_path):
        (tmp_path / ".httpcheck.toml").write_bytes(FULL_TOML)
        with (
            patch("httpcheck.config.pathlib.Path.home", return_value=tmp_path),
            patch(
                "httpcheck.config.pathlib.Path.cwd",
                return_value=pathlib.Path("/nonexistent_cwd_xyz"),
            ),
        ):
            result = load_config()
        assert result["timeout"] == 10.0
        assert result["output_format"] == "json"
        assert result["verify_ssl"] is False
        assert "User-Agent: mybot/1.0" in result["headers"]
        assert "Accept: application/json" in result["headers"]

    def test_invalid_toml_falls_back_silently(self, tmp_path):
        (tmp_path / ".httpcheck.toml").write_bytes(INVALID_TOML)
        with (
            patch("httpcheck.config.pathlib.Path.home", return_value=tmp_path),
            patch(
                "httpcheck.config.pathlib.Path.cwd",
                return_value=pathlib.Path("/nonexistent_cwd_xyz"),
            ),
            pytest.warns(UserWarning, match="Could not parse"),
        ):
            result = load_config()
        assert result == {}

    def test_unknown_keys_ignored(self, tmp_path):
        (tmp_path / ".httpcheck.toml").write_bytes(UNKNOWN_KEYS_TOML)
        with (
            patch("httpcheck.config.pathlib.Path.home", return_value=tmp_path),
            patch(
                "httpcheck.config.pathlib.Path.cwd",
                return_value=pathlib.Path("/nonexistent_cwd_xyz"),
            ),
            pytest.warns(UserWarning),
        ):
            result = load_config()
        assert "unknown_key" not in result
        assert result["timeout"] == 3.0


# ---------------------------------------------------------------------------
# get_notifications_config
# ---------------------------------------------------------------------------


class TestGetNotificationsConfig:
    def test_extracts_notifications_from_raw(self):
        raw = {
            "notifications": {"enabled": False, "on_failure": True, "sound": "Glass"}
        }
        result = get_notifications_config(raw)
        assert result == {"enabled": False, "on_failure": True, "sound": "Glass"}

    def test_ignores_unknown_notification_keys(self):
        raw = {"notifications": {"enabled": True, "bad_key": "x"}}
        with pytest.warns(UserWarning, match=r"\[notifications\].bad_key"):
            result = get_notifications_config(raw)
        assert "bad_key" not in result

    def test_returns_empty_when_no_notifications_section(self):
        assert get_notifications_config({}) == {}

    def test_loads_from_files_when_raw_is_none(self, tmp_path):
        (tmp_path / ".httpcheck.toml").write_bytes(
            b"[notifications]\nenabled = false\n"
        )
        with (
            patch("httpcheck.config.pathlib.Path.home", return_value=tmp_path),
            patch(
                "httpcheck.config.pathlib.Path.cwd",
                return_value=pathlib.Path("/nonexistent_cwd_xyz"),
            ),
        ):
            result = get_notifications_config(None)
        assert result["enabled"] is False


# ---------------------------------------------------------------------------
# DEFAULT_CONFIG sanity check
# ---------------------------------------------------------------------------


def test_default_config_has_expected_keys():
    assert "timeout" in DEFAULT_CONFIG
    assert "retries" in DEFAULT_CONFIG
    assert "follow_redirects" in DEFAULT_CONFIG
    assert "output_format" in DEFAULT_CONFIG
    assert "verify_ssl" in DEFAULT_CONFIG
