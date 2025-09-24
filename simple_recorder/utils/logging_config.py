"""
Module Description:
Logging utilities for configuring application-wide logging and severity levels.
"""

import logging
from enum import Enum


class LogSeverity(Enum):
    """
    Severity levels for UI/console messages.

    Mirrors standard logging levels for convenience.
    """
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure application-wide logging.

    Args:
        level (int): Logging level, defaults to logging.INFO.

    Returns:
        None
    """
    logging.basicConfig(level=level, format="%(levelname)s:%(message)s")
