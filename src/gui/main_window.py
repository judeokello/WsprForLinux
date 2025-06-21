"""
Main application window for W4L.

Implements the primary GUI interface for audio recording and transcription.
"""

import sys
import logging
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap

from ..audio.buffer_manager import AudioBufferManager
from ..audio.device_config import AudioDeviceManager
from ..audio.memory_manager import MemoryMonitor


class W4LMainWindow(QMainWindow):
    """
    Main application window for W4L.
    
    Features:
    - Always on top, frameless window
    - Centered positioning
    - Waveform visualization area
    - Recording controls and status
    - Settings access via gear icon
    """
    
    def __init__(self, device_manager: Optional[AudioDeviceManager] = None):
        """
        Initialize the main window.
        
        Args:
            device_manager: Audio device manager for configuration
        """
        super().__init__()
        
        # Setup logging
        self.logger = logging.getLogger("w4l.gui.main_window")
        
        # Audio components
        self.device_manager = device_manager or AudioDeviceManager()
        self.memory_monitor = MemoryMonitor()
        self.buffer_manager = AudioBufferManager(self.device_manager, self.memory_monitor)
        
        # Window state
        self.is_recording = False
        self.is_dragging = False
        self.drag_position = QPoint()
        
        # Initialize UI
        self._setup_window_properties()
        self._create_ui()
        self._setup_connections()
        self._center_window()
        
        self.logger.info("Main window initialized")
    
    def _setup_window_properties(self):
        """Set up window properties (always on top, frameless)."""
        # Window flags for always on top and frameless
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |  # type: ignore
            Qt.FramelessWindowHint |   # type: ignore
            Qt.Tool                    # type: ignore
        )
        
        # Window properties
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # type: ignore
        self.setAttribute(Qt.WA_NoSystemBackground, True)  # type: ignore
        
        # Set window size
        self.resize(400, 300)
        
        # Set window title
        self.setWindowTitle("W4L - Whisper for Linux")
    
    def _create_ui(self):
        """Create the user interface components."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create title bar
        self._create_title_bar(main_layout)
        
        # Create main content area
        self._create_content_area(main_layout)
        
        # Create status bar
        self._create_status_bar(main_layout)
        
        # Apply styling
        self._apply_styling(central_widget)
    
    def _create_title_bar(self, parent_layout):
        """Create the title bar with drag functionality and settings button."""
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setObjectName("titleBar")
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        # Title label
        title_label = QLabel("W4L")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Settings button (gear icon)
        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setToolTip("Settings")
        self.settings_button.setFont(QFont("Arial", 12))
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(spacer)
        title_layout.addWidget(self.settings_button)
        
        parent_layout.addWidget(title_bar)
    
    def _create_content_area(self, parent_layout):
        """Create the main content area with waveform and controls."""
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setMinimumHeight(200)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)
        
        # Waveform area (placeholder for now)
        self.waveform_label = QLabel("Waveform visualization will appear here")
        self.waveform_label.setObjectName("waveformLabel")
        self.waveform_label.setAlignment(Qt.AlignCenter)  # type: ignore
        self.waveform_label.setMinimumHeight(120)
        self.waveform_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                border: 2px dashed #7f8c8d;
                border-radius: 8px;
                color: #bdc3c7;
                font-size: 12px;
            }
        """)
        
        # Instruction label
        self.instruction_label = QLabel("Press hotkey to start recording...")
        self.instruction_label.setObjectName("instructionLabel")
        self.instruction_label.setAlignment(Qt.AlignCenter)  # type: ignore
        self.instruction_label.setFont(QFont("Arial", 11))
        self.instruction_label.setStyleSheet("color: #2c3e50;")
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)  # type: ignore
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        content_layout.addWidget(self.waveform_label)
        content_layout.addWidget(self.instruction_label)
        content_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(content_frame)
    
    def _create_status_bar(self, parent_layout):
        """Create the status bar with recording controls."""
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_frame.setFixedHeight(50)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        # Recording button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setObjectName("recordButton")
        self.record_button.setFixedHeight(35)
        self.record_button.setFont(QFont("Arial", 10, QFont.Bold))
        
        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(35, 35)
        self.close_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.close_button.setToolTip("Close")
        
        status_layout.addWidget(self.record_button)
        status_layout.addStretch()
        status_layout.addWidget(self.close_button)
        
        parent_layout.addWidget(status_frame)
    
    def _apply_styling(self, widget):
        """Apply modern styling to the window."""
        widget.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            
            QFrame#titleBar {
                background-color: #3498db;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            
            QFrame#contentFrame {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
            }
            
            QFrame#statusFrame {
                background-color: #f8f9fa;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            
            QPushButton#settingsButton {
                background-color: transparent;
                border: none;
                color: #2c3e50;
                border-radius: 15px;
            }
            
            QPushButton#settingsButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            
            QPushButton#recordButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 17px;
                padding: 8px 16px;
            }
            
            QPushButton#recordButton:hover {
                background-color: #229954;
            }
            
            QPushButton#recordButton:pressed {
                background-color: #1e8449;
            }
            
            QPushButton#closeButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 17px;
            }
            
            QPushButton#closeButton:hover {
                background-color: #c0392b;
            }
        """)
    
    def _setup_connections(self):
        """Set up signal connections."""
        # Button connections
        self.settings_button.clicked.connect(self._open_settings)  # type: ignore
        self.record_button.clicked.connect(self._toggle_recording)  # type: ignore
        self.close_button.clicked.connect(self.close)  # type: ignore
        # No need to assign mouse event handlers; override them below
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:  # type: ignore
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if event.buttons() == Qt.LeftButton and self.is_dragging:  # type: ignore
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for window dragging."""
        if event.button() == Qt.LeftButton:  # type: ignore
            self.is_dragging = False
            event.accept()
    
    def _center_window(self):
        """Center the window on the screen."""
        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_geometry = screen.geometry()
            window_geometry = self.geometry()
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            self.move(x, y)
            self.logger.debug(f"Window centered at ({x}, {y})")
        else:
            self.logger.warning("No primary screen found; cannot center window.")
    
    def _open_settings(self):
        """Open the settings dialog."""
        self.logger.info("Opening settings dialog")
        # TODO: Implement settings dialog
        # from .settings_dialog import W4LSettingsDialog
        # dialog = W4LSettingsDialog(self.device_manager, self)
        # dialog.exec_()
        return None
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
        return None
    
    def _start_recording(self):
        """Start audio recording."""
        self.logger.info("Starting recording")
        
        # Start audio recording
        success = self.buffer_manager.start_recording()
        if not success:
            self.logger.error("Failed to start recording")
            self.status_label.setText("Recording failed")
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            return None
        
        # Update UI
        self.is_recording = True
        self.record_button.setText("Stop Recording")
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 17px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self.instruction_label.setText("Speak now... Press ESC to cancel or Enter to finish early")
        self.status_label.setText("Recording...")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # TODO: Start waveform updates
        # self._start_waveform_updates()
        return None
    
    def _stop_recording(self):
        """Stop audio recording."""
        self.logger.info("Stopping recording")
        
        # Stop audio recording
        self.buffer_manager.stop_recording()
        
        # Update UI
        self.is_recording = False
        self.record_button.setText("Start Recording")
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 17px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        self.instruction_label.setText("Press hotkey to start recording...")
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        # TODO: Stop waveform updates
        # self._stop_waveform_updates()
        return None
    
    def show_window(self):
        """Show the window and bring it to front."""
        self.show()
        self.raise_()
        self.activateWindow()
        self.logger.info("Window shown and activated")
    
    def hide_window(self):
        """Hide the window."""
        self.hide()
        self.logger.info("Window hidden")
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Window closing")
        
        # Stop recording if active
        if self.is_recording:
            self._stop_recording()
        
        # Cleanup audio resources
        self.buffer_manager.cleanup()
        
        event.accept()


def create_application() -> QApplication:
    """
    Create and configure the QApplication instance.
    
    Returns:
        QApplication: Configured application instance
    """
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("W4L")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("W4L")
    
    # Set application style
    app.setStyle("Fusion")
    
    return app


def main():
    """Main function to run the W4L GUI application."""
    # Create application
    app = create_application()
    
    # Create and show main window
    window = W4LMainWindow()
    window.show_window()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 