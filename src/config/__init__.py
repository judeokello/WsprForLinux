"""
Config module for W4L.

Contains configuration management, constants, and logging setup.
"""

from .settings import Settings
from .logging_config import setup_logging, get_logger, set_log_level

__all__ = [
    'Settings',
    'setup_logging',
    'get_logger',
    'set_log_level'
] 