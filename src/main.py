#!/usr/bin/env python3
"""
Main application entry point for W4L (Whisper for Linux).

This application runs as a background service that can be activated via global hotkey.
When activated, it shows a GUI for voice recording and transcription.
"""

import sys
import os
import signal
import logging
import setproctitle
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from gui.main_window import W4LMainWindow
from config import ConfigManager

class W4LApplication(QObject):
    """Main application class that manages the system tray and GUI."""
    
    # Signal to show the main window
    show_window_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Set custom process name for better identification in htop/task manager
        setproctitle.setproctitle("w4l")
        
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("W4L - Whisper for Linux")
        self.app.setApplicationVersion("1.0.0")
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger("w4l.main")
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        self.logger.info("Configuration manager initialized")
        
        # Application state
        self.main_window = None
        self.system_tray = None
        self.is_initialized = False
        
        # Setup signal handlers for proper termination
        self._setup_signal_handlers()
        
        # Initialize components
        self._setup_system_tray()
        self._setup_main_window()
        
        # TODO: Setup global hotkey listener
        # self._setup_global_hotkey()
        
        self.logger.info("W4L application initialized")
    
    def _setup_logging(self):
        """Setup application logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('w4l.log')
            ]
        )
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for proper application termination."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully")
            # Force quit immediately, don't wait for GUI focus
            self.app.quit()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        # Connect Qt's aboutToQuit signal
        self.app.aboutToQuit.connect(self._on_about_to_quit)
    
    def _setup_system_tray(self):
        """Setup system tray icon and menu."""
        self.system_tray = QSystemTrayIcon()
        self.system_tray.setToolTip("W4L - Whisper for Linux")
        
        # TODO: Add proper icon
        # self.system_tray.setIcon(QIcon("path/to/icon.png"))
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show window action
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.system_tray.setContextMenu(tray_menu)
        self.system_tray.show()
        
        # Connect double-click to show window
        self.system_tray.activated.connect(self._on_tray_activated)
    
    def _setup_main_window(self):
        """Setup the main window."""
        self.main_window = W4LMainWindow(self.config_manager)
        self.main_window.logger = self.logger
        
        # Connect window closed signal
        self.main_window.window_closed.connect(self._on_window_closed)
        
        self.logger.info("Main window setup complete")
    
    def _on_tray_activated(self, reason):
        """Handle system tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window()
    
    def _on_window_closed(self):
        """Handle main window close event."""
        self.logger.info("Main window closed, application continues running in background")
        # TODO: Stop recording if active
        # TODO: Clean up any ongoing operations
    
    def show_main_window(self):
        """Show the main window."""
        if self.main_window and not self.main_window.isVisible():
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.logger.info("Main window shown")
        elif self.main_window and self.main_window.isVisible():
            # Window is already visible, just bring it to front
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.logger.info("Main window brought to front")
    
    def show_settings(self):
        """Show settings dialog."""
        self.logger.info("Settings requested")
        # TODO: Implement settings dialog
        QMessageBox.information(None, "Settings", "Settings dialog not yet implemented")
    
    def quit_application(self):
        """Quit the application completely."""
        self.logger.info("Application quit requested")
        
        # TODO: Clean up resources
        # - Stop any ongoing recording
        # - Save settings
        # - Clean up temporary files
        
        self.app.quit()
    
    def _on_about_to_quit(self):
        """Handle Qt application quit event."""
        self.logger.info("Qt application about to quit")
        # TODO: Clean up resources
        # - Stop any ongoing recording
        # - Save settings
        # - Clean up temporary files
    
    def run(self):
        """Run the application."""
        self.logger.info("Starting W4L application")
        
        # Show initial window for development/testing
        # In production, this would be hidden and only shown via hotkey
        self.show_main_window()
        
        # Run the application
        return self.app.exec()

def main():
    """Main entry point."""
    try:
        app = W4LApplication()
        return app.run()
    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 