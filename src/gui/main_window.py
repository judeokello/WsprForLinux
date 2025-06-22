import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .waveform_widget import WaveformWidget

class W4LMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = None  # Will be set up by main application
        
        # Window state
        self.is_recording = False
        
        # Initialize UI
        self._setup_window_properties()
        self._create_ui()
        self._center_window()
        
        if self.logger:
            self.logger.info("Main window initialized")
    
    def _setup_window_properties(self):
        """Set up window properties (always on top, frameless)."""
        # Window flags for always on top and frameless
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        
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
        
        # Title bar
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background-color: #3498db; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel("W4L")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(30, 30)
        self.settings_button.setToolTip("Settings")
        self.settings_button.setFont(QFont("Arial", 12))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #2c3e50;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.settings_button.clicked.connect(self._open_settings)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(spacer)
        title_layout.addWidget(self.settings_button)
        
        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
            }
        """)
        content_frame.setMinimumHeight(200)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)
        
        # Waveform Widget
        self.waveform_widget = WaveformWidget()
        self.waveform_widget.setMinimumHeight(120)
        
        # Instruction label
        self.instruction_label = QLabel("Press hotkey to start recording...")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setFont(QFont("Arial", 11))
        self.instruction_label.setStyleSheet("color: #2c3e50;")
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        content_layout.addWidget(self.waveform_widget)
        content_layout.addWidget(self.instruction_label)
        content_layout.addWidget(self.status_label)
        
        # Status bar
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        status_frame.setFixedHeight(50)
        
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        # Recording button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setFixedHeight(35)
        self.record_button.setFont(QFont("Arial", 10, QFont.Weight.Bold))
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
        self.record_button.clicked.connect(self._toggle_recording)
        
        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(35, 35)
        self.close_button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.close_button.setToolTip("Close")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 17px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.close_button.clicked.connect(self.close)
        
        status_layout.addWidget(self.record_button)
        status_layout.addStretch()
        status_layout.addWidget(self.close_button)
        
        # Add all components to main layout
        main_layout.addWidget(title_bar)
        main_layout.addWidget(content_frame)
        main_layout.addWidget(status_frame)
    
    def _center_window(self):
        """Center the window on the screen."""
        screen = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        
        x = (screen.width() - window_geometry.width()) // 2
        y = (screen.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def _open_settings(self):
        """Open settings dialog."""
        if self.logger:
            self.logger.info("Settings button clicked")
        # TODO: Implement settings dialog
        print("Settings dialog not yet implemented")
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """Start recording."""
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
        self.status_label.setText("Recording...")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.instruction_label.setText("Recording in progress...")
        
        if self.logger:
            self.logger.info("Recording started")
    
    def _stop_recording(self):
        """Stop recording."""
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
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.instruction_label.setText("Press hotkey to start recording...")
        
        if self.logger:
            self.logger.info("Recording stopped")

if __name__ == '__main__':
    # This block is for direct testing of the main window
    app = QApplication(sys.argv)
    main_win = W4LMainWindow()
    main_win.show()
    sys.exit(app.exec()) 