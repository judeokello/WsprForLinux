"""
Error handling utilities for W4L.

Provides centralized error handling and user-friendly error messages.
"""

import logging
import sys
import traceback
from typing import Optional, Callable, Any
from PyQt5.QtCore import QObject, pyqtSignal


class ErrorHandler(QObject):
    """
    Centralized error handler for W4L.
    
    Provides consistent error handling across the application
    with user-friendly error messages and logging.
    """
    
    # Signals
    error_occurred = pyqtSignal(str)  # Error message
    warning_occurred = pyqtSignal(str)  # Warning message
    
    def __init__(self):
        """Initialize the error handler."""
        super().__init__()
        self.logger = logging.getLogger("w4l.error_handler")
        self._error_callbacks: list[Callable[[str], None]] = []
        self._warning_callbacks: list[Callable[[str], None]] = []
    
    def handle_error(
        self,
        error: str | Exception,
        context: Optional[str] = None,
        show_to_user: bool = True,
        log_level: str = "ERROR"
    ) -> None:
        """
        Handle an error with logging and optional user notification.
        
        Args:
            error: Error message or exception
            context: Additional context about where the error occurred
            show_to_user: Whether to show error to user
            log_level: Logging level for the error
        """
        # Convert exception to string if needed
        if isinstance(error, Exception):
            error_msg = str(error)
            error_details = traceback.format_exc()
        else:
            error_msg = str(error)
            error_details = None
        
        # Add context if provided
        if context:
            error_msg = f"[{context}] {error_msg}"
        
        # Log the error
        log_method = getattr(self.logger, log_level.lower())
        log_method(error_msg)
        
        if error_details:
            self.logger.debug(f"Error details: {error_details}")
        
        # Show to user if requested
        if show_to_user:
            self.error_occurred.emit(error_msg)
        
        # Call error callbacks
        for callback in self._error_callbacks:
            try:
                callback(error_msg)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
    
    def handle_warning(
        self,
        warning: str,
        context: Optional[str] = None,
        show_to_user: bool = False
    ) -> None:
        """
        Handle a warning with logging and optional user notification.
        
        Args:
            warning: Warning message
            context: Additional context about where the warning occurred
            show_to_user: Whether to show warning to user
        """
        # Add context if provided
        if context:
            warning_msg = f"[{context}] {warning}"
        else:
            warning_msg = warning
        
        # Log the warning
        self.logger.warning(warning_msg)
        
        # Show to user if requested
        if show_to_user:
            self.warning_occurred.emit(warning_msg)
        
        # Call warning callbacks
        for callback in self._warning_callbacks:
            try:
                callback(warning_msg)
            except Exception as e:
                self.logger.error(f"Error in warning callback: {e}")
    
    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        Add a callback function to be called when errors occur.
        
        Args:
            callback: Function to call with error message
        """
        self._error_callbacks.append(callback)
    
    def add_warning_callback(self, callback: Callable[[str], None]) -> None:
        """
        Add a callback function to be called when warnings occur.
        
        Args:
            callback: Function to call with warning message
        """
        self._warning_callbacks.append(callback)
    
    def handle_critical_error(self, error: str | Exception) -> None:
        """
        Handle a critical error that requires application shutdown.
        
        Args:
            error: Error message or exception
        """
        self.handle_error(error, context="CRITICAL", show_to_user=True, log_level="CRITICAL")
        
        # TODO: Implement graceful shutdown
        # For now, just exit
        sys.exit(1)
    
    def handle_audio_error(self, error: str | Exception) -> None:
        """
        Handle audio-related errors specifically.
        
        Args:
            error: Error message or exception
        """
        self.handle_error(error, context="AUDIO", show_to_user=True)
    
    def handle_transcription_error(self, error: str | Exception) -> None:
        """
        Handle transcription-related errors specifically.
        
        Args:
            error: Error message or exception
        """
        self.handle_error(error, context="TRANSCRIPTION", show_to_user=True)
    
    def handle_system_error(self, error: str | Exception) -> None:
        """
        Handle system integration errors specifically.
        
        Args:
            error: Error message or exception
        """
        self.handle_error(error, context="SYSTEM", show_to_user=True) 