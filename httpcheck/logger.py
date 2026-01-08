"""Logging configuration for httpcheck.

This module provides a centralized logging system to replace print() statements
throughout the codebase, enabling proper log levels, file output, and
integration with log aggregation systems.
"""

import logging
import sys
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logger(
    name: str = "httpcheck",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = False,
    quiet: bool = False,
) -> logging.Logger:
    """Configure and return the httpcheck logger.

    Args:
        name: Logger name (default: "httpcheck")
        level: Logging level (default: INFO)
        log_file: Optional file path for log output
        json_format: If True, use JSON format for structured logging
        quiet: If True, only log ERROR and above to console

    Returns:
        Configured logger instance
    """
    global _logger  # pylint: disable=global-statement

    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR if quiet else level)

    if json_format:
        console_handler.setFormatter(_get_json_formatter())
    else:
        console_handler.setFormatter(_get_standard_formatter())

    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Log everything to file

        if json_format:
            file_handler.setFormatter(_get_json_formatter())
        else:
            file_handler.setFormatter(_get_detailed_formatter())

        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    _logger = logger
    return logger


def _get_standard_formatter() -> logging.Formatter:
    """Get standard console formatter."""
    return logging.Formatter(
        fmt="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _get_detailed_formatter() -> logging.Formatter:
    """Get detailed formatter for file output."""
    return logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _get_json_formatter() -> logging.Formatter:
    """Get JSON formatter for structured logging.

    Note: This is a simple implementation. For production use,
    consider using python-json-logger or structlog.
    """
    return logging.Formatter(
        fmt='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def get_logger(name: str = "httpcheck") -> logging.Logger:
    """Get the httpcheck logger instance.

    Args:
        name: Logger name (default: "httpcheck")

    Returns:
        Logger instance (creates default if not yet configured)
    """
    global _logger  # pylint: disable=global-statement

    if _logger is None:
        _logger = setup_logger(name)

    return _logger


def reset_logger() -> None:
    """Reset the logger instance (useful for testing)."""
    global _logger  # pylint: disable=global-statement
    if _logger is not None:
        for handler in _logger.handlers[:]:
            handler.close()
            _logger.removeHandler(handler)
        _logger = None


# Convenience functions for common log levels
def debug(message: str, *args, **kwargs) -> None:
    """Log a debug message."""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs) -> None:
    """Log an info message."""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs) -> None:
    """Log a warning message."""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs) -> None:
    """Log an error message."""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs) -> None:
    """Log a critical message."""
    get_logger().critical(message, *args, **kwargs)
