"""
Settings dialog for W4L.

Provides configuration options for audio settings, device selection, and other preferences.
"""

import logging
from typing import Optional
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

from ..audio.device_config import AudioDeviceManager


class W4LSettingsDialog(QDialog):
    """
    Settings dialog for W4L configuration.
    
    This is a placeholder that will be fully implemented in Phase 2.4.
    """
    
    def __init__(self, device_manager: AudioDeviceManager, parent=None):
        """
        Initialize the settings dialog.
        
        Args:
            device_manager: Audio device manager for configuration
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger("w4l.gui.settings_dialog")
        self.device_manager = device_manager
        
        self._setup_dialog()
        self._create_ui()
        
        self.logger.info("Settings dialog initialized")
    
    def _setup_dialog(self):
        """Set up dialog properties."""
        self.setWindowTitle("W4L Settings")
        self.setModal(True)
        self.resize(500, 400)
    
    def _create_ui(self):
        """Create the user interface (placeholder)."""
        layout = QVBoxLayout(self)
        
        # Placeholder content
        placeholder = QLabel("Settings dialog will be implemented in Phase 2.4")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        
        layout.addWidget(placeholder)
    
    def exec_(self):
        """Show the settings dialog."""
        self.logger.info("Opening settings dialog")
        return super().exec_() 