"""
Logging configuration for W4L.

Sets up logging for the application with appropriate levels and handlers.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, uses default location.
        console_output: Whether to output logs to console
    """
    # Create logger
    logger = logging.getLogger("w4l")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_dir = Path.home() / ".config" / "w4l" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / "w4l.log")
    
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If file logging fails, just log to console
        logger.warning(f"Failed to set up file logging: {e}")
    
    # Log startup message
    logger.info("W4L logging initialized")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"w4l.{name}")


def set_log_level(level: str) -> None:
    """
    Change the logging level for all W4L loggers.
    
    Args:
        level: New logging level
    """
    logger = logging.getLogger("w4l")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Update all child loggers
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.setLevel(logging.INFO)
        else:
            handler.setLevel(getattr(logging, level.upper())) 