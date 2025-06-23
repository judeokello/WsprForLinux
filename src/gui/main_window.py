import sys
import logging
from typing import Optional
import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QFont, QCloseEvent, QKeyEvent
from .waveform_widget import WaveformWidget
from config import ConfigManager
from audio.recorder import AudioRecorder
import os

class W4LMainWindow(QMainWindow):
    # Signal emitted when window is closed (but app continues running)
    window_closed = pyqtSignal()
    # Signal emitted when the settings button is clicked
    settings_requested = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.logger: Optional[logging.Logger] = None  # Will be set up by main application
        self.config_manager = config_manager
        
        # Audio Recorder setup
        self.recorder = self._setup_recorder()

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
        self.instruction_label = QLabel("Speak now... Press ESC to cancel or Enter to finish early")
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
        self.close_button.clicked.connect(self._close_application)
        
        status_layout.addWidget(self.record_button)
        status_layout.addStretch()
        status_layout.addWidget(self.close_button)
        
        # Add all components to main layout
        main_layout.addWidget(title_bar)
        main_layout.addWidget(content_frame)
        main_layout.addWidget(status_frame)
    
    def _center_window(self):
        """Center the window on the screen."""
        screen = QApplication.primaryScreen()
        if screen is None:
            # Fallback: use desktop widget or default position
            self.move(100, 100)
            return
            
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
    
    def _setup_recorder(self) -> Optional[AudioRecorder]:
        """Initialize the AudioRecorder based on current config."""
        try:
            device_id = self.config_manager.get_config_value('audio', 'device_id')
            if device_id is None:
                device_id = sd.default.device[0] # Fallback to default input device

            sample_rate = self.config_manager.get_config_value('audio', 'sample_rate', 16000)
            channels = self.config_manager.get_config_value('audio', 'channels', 1)
            
            recorder = AudioRecorder(device_id=device_id, sample_rate=sample_rate, channels=channels)
            # Connect the callback to update the waveform widget
            recorder.audio_chunk_callback = self.handle_audio_chunk
            return recorder
        except Exception as e:
            # Logger might not be initialized yet, so we print as a fallback
            print(f"ERROR: Failed to initialize audio recorder: {e}")
            if self.logger:
                self.logger.error(f"Failed to initialize audio recorder: {e}")
            return None

    def handle_audio_chunk(self, chunk: np.ndarray):
        """Callback to handle new audio data from the recorder."""
        self.waveform_widget.update_waveform(chunk)

    def _open_settings(self):
        """Emit a signal to request the settings dialog."""
        if self.logger:
            self.logger.info("Settings button clicked, emitting signal.")
        self.settings_requested.emit()
    
    def _toggle_recording(self):
        """Toggle recording state."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """Start the audio recording."""
        if not self.recorder:
            if self.logger:
                self.logger.error("Audio recorder not available.")
            return
            
        if self.is_recording:
            if self.logger:
                self.logger.warning("Recording is already in progress.")
            return

        # Ensure recordings directory exists in file-based mode
        capture_mode = self.config_manager.get_config_value('audio', 'capture_mode')
        if capture_mode == 'file_based':
            save_path = self.config_manager.get_config_value('audio', 'save_path')
            recordings_dir = os.path.join(save_path, 'W4L-Recordings')
            try:
                os.makedirs(recordings_dir, exist_ok=True)
                if self.logger:
                    self.logger.info(f"Ensured recordings directory exists: {recordings_dir}")
            except OSError as e:
                if self.logger:
                    self.logger.error(f"Failed to create recordings directory: {e}")

        # Ensure the recorder is ready
        self.recorder.start()
        
        # Set up silence detection callbacks
        self.recorder.set_silence_callbacks(
            on_silence_detected=self._on_silence_detected,
            on_speech_detected=self._on_speech_detected,
            on_noise_learned=self._on_noise_learned
        )
        
        self.is_recording = True
        self.waveform_widget.start_recording()
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
        if self.recorder:
            self.recorder.stop()
            
        self.waveform_widget.stop_recording()
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

    def _close_application(self):
        """Close the application."""
        if self.logger:
            self.logger.info("Close button clicked")
        # Hide the window instead of terminating the application
        self.hide()
        self.window_closed.emit()
    
    def closeEvent(self, event: QCloseEvent):
        """Handle the window close event."""
        if self.logger:
            self.logger.info("Window close event triggered")
        # Hide the window instead of terminating the application
        event.accept()
        self.hide()
        self.window_closed.emit()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            # ESC key: Abort recording and discard everything
            if self.logger:
                self.logger.info("ESC key pressed - aborting recording")
            self._abort_recording()
            event.accept()
            
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            # Enter key: Finish recording early, transcribe, and paste/save
            if self.logger:
                self.logger.info("Enter key pressed - finishing recording early")
            self._finish_recording_early()
            event.accept()
            
        else:
            # Let other keys be handled normally
            super().keyPressEvent(event)
    
    def _abort_recording(self):
        """Abort recording and discard everything."""
        if self.logger:
            self.logger.info("Aborting recording - discarding all data")
        
        # Stop recording if active
        if self.is_recording:
            self._stop_recording()
        
        # Reset UI state
        self._reset_ui_state()
        
        # Hide window (app continues running)
        self.hide()
        self.window_closed.emit()
    
    def _finish_recording_early(self):
        """Finish recording early, transcribe current audio, and paste/save text."""
        if self.logger:
            self.logger.info("Finishing recording early")
        
        # Stop recording if active
        if self.is_recording:
            self._stop_recording()
        
        # Get transcribed text from current audio buffer
        transcribed_text = self._get_transcribed_text()
        
        if transcribed_text:
            # Handle text output based on active cursor and capture mode
            self._handle_text_output(transcribed_text)
        else:
            if self.logger:
                self.logger.warning("No transcribed text available")
            # Show user feedback
            self.status_label.setText("No audio to transcribe")
            self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        
        # Reset UI state
        self._reset_ui_state()
        
        # Hide window (app continues running)
        self.hide()
        self.window_closed.emit()
    
    def _get_transcribed_text(self) -> str:
        """Get transcribed text from current audio buffer."""
        try:
            if not self.recorder:
                if self.logger:
                    self.logger.warning("No recorder available for transcription")
                return ""
            
            # Get audio data from recorder
            audio_data = self.recorder.get_audio_buffer()
            
            if audio_data is None or len(audio_data) == 0:
                if self.logger:
                    self.logger.warning("No audio data available for transcription")
                return ""
            
            # TODO: Implement actual transcription using Whisper
            # For now, return placeholder text
            # This will be implemented in Phase 4: Whisper Integration
            if self.logger:
                self.logger.info(f"Audio buffer contains {len(audio_data)} samples")
            
            # Placeholder: return sample text based on audio length
            audio_duration = len(audio_data) / 16000  # Assuming 16kHz sample rate
            if audio_duration < 0.5:
                return ""  # Too short to transcribe
            elif audio_duration < 2.0:
                return "Hello world"  # Short audio
            else:
                return "This is a sample transcription of the recorded audio. The actual Whisper integration will be implemented in Phase 4."
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting transcribed text: {e}")
            return ""
    
    def _handle_text_output(self, text: str):
        """Handle text output based on active cursor and capture mode."""
        try:
            # Check if there's an active cursor/application
            has_active_cursor = self._has_active_cursor()
            capture_mode = self.config_manager.get_config_value('audio', 'capture_mode', 'streaming')
            
            if has_active_cursor:
                # Try to paste to active cursor
                if self._paste_text_to_cursor(text):
                    if self.logger:
                        self.logger.info("Text pasted to active cursor successfully")
                    return
                else:
                    if self.logger:
                        self.logger.warning("Failed to paste to cursor, falling back to clipboard")
            
            # Fallback: copy to clipboard
            if self._copy_text_to_clipboard(text):
                if self.logger:
                    self.logger.info("Text copied to clipboard as fallback")
                
                # If in file-based mode and no active cursor, also save to file
                if capture_mode == 'file_based':
                    self._save_text_to_file(text)
            else:
                if self.logger:
                    self.logger.error("Failed to copy text to clipboard")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling text output: {e}")
    
    def _paste_text_to_cursor(self, text: str) -> bool:
        """Attempt to paste text to the active cursor position."""
        try:
            # TODO: Implement actual text pasting
            # This will use pyautogui, xdotool, or similar for Linux
            # For now, just copy to clipboard and simulate Ctrl+V
            
            # Copy text to clipboard first
            if not self._copy_text_to_clipboard(text):
                return False
            
            # TODO: Simulate Ctrl+V paste
            # import pyautogui
            # pyautogui.hotkey('ctrl', 'v')
            # Or use xdotool: subprocess.run(['xdotool', 'key', 'ctrl+v'])
            
            # For now, just return success (text is in clipboard)
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error pasting text to cursor: {e}")
            return False
    
    def _save_text_to_file(self, text: str) -> bool:
        """Save transcribed text to file in file-based capture mode."""
        try:
            save_path = self.config_manager.get_config_value('audio', 'save_path')
            if not save_path:
                if self.logger:
                    self.logger.warning("No save path configured for file-based mode")
                return False
            
            # Create transcriptions directory
            transcriptions_dir = os.path.join(save_path, 'W4L-Transcriptions')
            os.makedirs(transcriptions_dir, exist_ok=True)
            
            # Generate filename with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{timestamp}.txt"
            filepath = os.path.join(transcriptions_dir, filename)
            
            # Write text to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            if self.logger:
                self.logger.info(f"Text saved to file: {filepath}")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving text to file: {e}")
            return False
    
    def _reset_ui_state(self):
        """Reset UI to initial state."""
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
        self.waveform_widget.stop_recording()
    
    def _has_active_cursor(self) -> bool:
        """Check if there's an active cursor/application window."""
        try:
            # TODO: Implement proper active window detection
            # For now, we'll use a simple heuristic
            # This should be enhanced with proper window management detection
            
            # Check if there are any active windows (excluding our own)
            active_window = QApplication.activeWindow()
            if active_window and active_window != self:
                # If there's an active window other than ours, assume it has a cursor
                return True
            
            # Fallback: assume there's always a cursor for now
            # In a real implementation, this would check for:
            # - Active application window
            # - Text input focus
            # - Cursor position
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to detect active cursor: {e}")
            return False
    
    def _copy_text_to_clipboard(self, text: str) -> bool:
        """Copy text to the system clipboard."""
        # This method will be implemented in a later phase
        if self.logger:
            self.logger.info(f"Copying to clipboard (dummy): {text}")
        return True

    def _on_silence_detected(self):
        """Callback for when silence is detected."""
        if self.logger:
            self.logger.info("Silence detected, stopping recording.")
        if self.is_recording:
            self._stop_recording()

    def _on_speech_detected(self):
        """Callback for when speech is detected."""
        if self.logger:
            self.logger.info("Speech detected.")

    def _on_noise_learned(self, noise_level: float):
        """Callback for when noise level is learned."""
        if self.logger:
            self.logger.info(f"Noise level learned: {noise_level:.4f}")

    def reset_for_test(self):
        """Resets the window's state for a new test."""
        if self.recorder and self.is_recording:
            self.recorder.stop()
        
        # Re-create the recorder and silence detector
        self.recorder = self._setup_recorder()
        if self.recorder:
            self.recorder.set_silence_callbacks(
                on_silence_detected=self._on_silence_detected,
                on_speech_detected=self._on_speech_detected,
                on_noise_learned=self._on_noise_learned
            )
        
        self.is_recording = False
        self.waveform_widget.reset_plot()
        self._reset_ui_state()
        if self.logger:
            self.logger.info("W4LMainWindow reset for new test.")

if __name__ == '__main__':
    # This block is for direct testing of the main window
    app = QApplication(sys.argv)
    
    # Create a ConfigManager for testing
    from config import ConfigManager
    config_manager = ConfigManager()
    
    main_win = W4LMainWindow(config_manager)
    main_win.show()
    sys.exit(app.exec())