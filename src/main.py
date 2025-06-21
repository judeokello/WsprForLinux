"""
Main application entry point for W4L.

This module contains the main application class and entry point.
"""

import sys
from typing import Optional
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal

from .config.settings import Settings
from .config.logging_config import setup_logging
from .utils.error_handler import ErrorHandler


class W4LApplication(QObject):
    """
    Main application class for W4L.
    
    Handles application lifecycle, initialization, and coordination
    between different modules.
    """
    
    # Signals
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    transcription_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, app: QApplication):
        """Initialize the W4L application."""
        super().__init__()
        self.app = app
        self.settings = Settings()
        self.error_handler = ErrorHandler()
        
        # Setup logging
        setup_logging()
        
        # Initialize modules (will be implemented in later phases)
        self._initialize_modules()
    
    def _initialize_modules(self) -> None:
        """Initialize all application modules."""
        # TODO: Initialize GUI, audio, transcription, and system modules
        # This will be implemented in later phases
        pass
    
    def start(self) -> None:
        """Start the W4L application."""
        try:
            # TODO: Start hotkey listener and system integration
            # This will be implemented in Phase 6
            pass
        except Exception as e:
            self.error_handler.handle_error(f"Failed to start application: {e}")
    
    def stop(self) -> None:
        """Stop the W4L application."""
        try:
            # TODO: Cleanup and shutdown
            # This will be implemented in later phases
            pass
        except Exception as e:
            self.error_handler.handle_error(f"Failed to stop application: {e}")


def main() -> int:
    """
    Main entry point for the W4L application.
    
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("W4L")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("W4L")
        
        w4l_app = W4LApplication(app)
        w4l_app.start()
        
        return app.exec_()
    
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 