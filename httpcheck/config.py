"""Configuration file support for httpcheck.

Loads user defaults from ~/.httpcheck.toml and/or ./httpcheck.toml.
Project-level config (./httpcheck.toml) takes precedence over user-level
(~/.httpcheck.toml). CLI flags always override both.
"""

import pathlib
import warnings
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

_CONFIG_FILENAME = ".httpcheck.toml"

DEFAULT_CONFIG: dict[str, Any] = {
    "timeout": 5.0,
    "retries": 2,
    "follow_redirects": "always",
    "output_format": "table",
    "verify_ssl": True,
}

_VALID_DEFAULTS_KEYS = {
    "timeout",
    "retries",
    "follow_redirects",
    "output_format",
    "verify_ssl",
    "workers",
    "retry_delay",
    "max_redirects",
}

_VALID_NOTIFICATIONS_KEYS = {"enabled", "on_failure", "sound"}


def _parse_toml_file(path: pathlib.Path) -> dict[str, Any]:
    """Parse a TOML file, returning empty dict on any error."""
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        return {}
    except Exception as exc:  # tomllib.TOMLDecodeError or other IO errors
        warnings.warn(
            f"Could not parse config file {path}: {exc}", UserWarning, stacklevel=3
        )
        return {}


def _merge_configs(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge two raw TOML dicts, with override taking precedence per section."""
    merged: dict[str, Any] = {}
    for section in set(list(base.keys()) + list(override.keys())):
        base_section = base.get(section, {})
        override_section = override.get(section, {})
        if isinstance(base_section, dict) and isinstance(override_section, dict):
            merged[section] = {**base_section, **override_section}
        else:
            merged[section] = override_section if section in override else base_section
    return merged


def _headers_to_list(headers_dict: dict[str, str]) -> list[str]:
    """Convert config [headers] dict to 'Name: Value' strings for argparse."""
    return [f"{name}: {value}" for name, value in headers_dict.items()]


def _extract_cli_defaults(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert raw TOML sections into a flat dict of argparse dest names."""
    result: dict[str, Any] = {}

    defaults = raw.get("defaults", {})
    for key, value in defaults.items():
        if key in _VALID_DEFAULTS_KEYS:
            result[key] = value
        else:
            warnings.warn(
                f"Unknown config key [defaults].{key} — ignored",
                UserWarning,
                stacklevel=3,
            )

    headers = raw.get("headers", {})
    if headers:
        result["headers"] = _headers_to_list(headers)

    return result


def load_config() -> dict[str, Any]:
    """Load and merge configuration from user and project config files.

    Search order (later entries win):
      1. ~/.httpcheck.toml  (user-level defaults)
      2. ./.httpcheck.toml  (project-level overrides)

    Returns a flat dict suitable for argparse.set_defaults().
    Returns an empty dict if no config files are found.
    """
    user_path = pathlib.Path.home() / _CONFIG_FILENAME
    project_path = pathlib.Path.cwd() / _CONFIG_FILENAME

    user_raw = _parse_toml_file(user_path)
    project_raw = _parse_toml_file(project_path)

    if not user_raw and not project_raw:
        return {}

    merged = _merge_configs(user_raw, project_raw)
    return _extract_cli_defaults(merged)


def get_notifications_config(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the [notifications] section from a raw config dict.

    Accepts an already-loaded raw dict to avoid re-reading files.
    Intended for use by the monitoring phase (Phase 3).
    """
    if raw is None:
        user_path = pathlib.Path.home() / _CONFIG_FILENAME
        project_path = pathlib.Path.cwd() / _CONFIG_FILENAME
        user_raw = _parse_toml_file(user_path)
        project_raw = _parse_toml_file(project_path)
        raw = _merge_configs(user_raw, project_raw)

    notifications = raw.get("notifications", {})
    result = {}
    for key, value in notifications.items():
        if key in _VALID_NOTIFICATIONS_KEYS:
            result[key] = value
        else:
            warnings.warn(
                f"Unknown config key [notifications].{key} — ignored",
                UserWarning,
                stacklevel=3,
            )
    return result
