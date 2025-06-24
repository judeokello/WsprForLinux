import sys
import logging
import psutil
import whisper
import gc
from typing import Optional
import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QLabel, QPushButton, QFrame, QSizePolicy, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QEvent, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QCloseEvent, QKeyEvent
from .waveform_widget import WaveformWidget
from config import ConfigManager
from transcription.model_manager import ModelManager
from audio.recorder import AudioRecorder
from audio.recording_state_machine import RecordingStateMachine, RecordingState, RecordingEvent
import os

MODEL_MEMORY_REQ = {
    'tiny': 1 * 1024**3,
    'base': 1 * 1024**3,
    'small': 2 * 1024**3,
    'medium': 5 * 1024**3,
    'large': 10 * 1024**3,
    'large-v1': 10 * 1024**3,
    'large-v2': 10 * 1024**3,
    'large-v3': 10 * 1024**3,
}

class ModelLoadWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, model_name, old_model, config_manager, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.old_model = old_model
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    def run(self):
        try:
            self.logger.info(f"ModelLoadWorker: Starting to load model '{self.model_name}'")
            
            # Unload old model
            if self.old_model:
                self.logger.debug("ModelLoadWorker: Unloading old model")
                del self.old_model
                gc.collect()

            # Load new model
            self.logger.info(f"ModelLoadWorker: Loading model '{self.model_name}' with whisper.load_model()")
            model = whisper.load_model(self.model_name)
            self.logger.info(f"ModelLoadWorker: Successfully loaded model '{self.model_name}'")
            
            # Update config
            self.logger.debug(f"ModelLoadWorker: Updating config to use model '{self.model_name}'")
            self.config_manager.set_config_value('transcription', 'model', self.model_name)
            
            self.finished.emit(model)
        except Exception as e:
            self.logger.error(f"ModelLoadWorker: Failed to load model '{self.model_name}': {e}")
            self.error.emit(str(e))

class W4LMainWindow(QMainWindow):
    # Signal emitted when window is closed (but app continues running)
    window_closed = pyqtSignal()
    # Signal emitted when the settings button is clicked
    settings_requested = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager, model_manager: ModelManager):
        super().__init__()
        self.logger: Optional[logging.Logger] = None  # Will be set up by main application
        self.config_manager = config_manager
        self.model_manager = model_manager
        self.whisper_model = None
        self.is_model_loading = False
        
        # Audio Recorder setup
        self.recorder = self._setup_recorder()
        
        # Recording State Machine setup
        self.state_machine = self._setup_state_machine()

        # Window state (deprecated - now managed by state machine)
        # self.is_recording = False
        
        # Initialize UI
        self._setup_window_properties()
        self._create_ui()
        self._populate_model_dropdown()
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
        
        # Add model selection dropdown
        self.model_combo = QComboBox()
        self.model_combo.setToolTip("Select transcription model")
        self.model_combo.currentIndexChanged.connect(self._on_model_selected)
        status_layout.addWidget(self.model_combo)
        
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
        status_layout.addWidget(self.model_combo)
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
    
    def _populate_model_dropdown(self):
        self.model_combo.clear()
        all_models = self.model_manager.list_models()
        available_models = [m for m in all_models if m.get('is_verified')]

        if self.logger:
            self.logger.debug(f"Found {len(all_models)} total models, {len(available_models)} verified models")
            for model in all_models:
                self.logger.debug(f"Model '{model['name']}': downloaded={model.get('is_downloaded')}, verified={model.get('is_verified')}")

        if not available_models:
            self.model_combo.addItem("No models found")
            self.model_combo.setEnabled(False)
            self.record_button.setEnabled(False)
            self.status_label.setText("No models available. Please go to Settings and download a model.")
            if self.logger:
                self.logger.warning("No verified models found - dropdown and recording disabled")
            return

        self.model_combo.setEnabled(True)
        self.record_button.setEnabled(True)
        for model in available_models:
            size_bytes = model.get('size_bytes', 0)
            if not size_bytes:
                size_str = 'Unknown size'
            else:
                size_mb = size_bytes / (1024 * 1024)
                size_str = f'{size_mb:.1f} MB'
            display_text = f"{model['name']} ({size_str})"
            self.model_combo.addItem(display_text, userData=model)
            if self.logger:
                self.logger.debug(f"Added model to dropdown: {display_text}")

        # Set current model from config
        current_model_name = self.config_manager.get_config_value('transcription', 'model', 'tiny')
        if self.logger:
            self.logger.debug(f"Current model from config: {current_model_name}")

        found_index = -1
        for i in range(self.model_combo.count()):
            model_data = self.model_combo.itemData(i)
            if model_data and model_data['name'] == current_model_name:
                found_index = i
                break

        if found_index != -1:
            self.model_combo.setCurrentIndex(found_index)
            if self.logger:
                self.logger.debug(f"Set dropdown to model at index {found_index}: {current_model_name}")
        else:
            if self.logger:
                self.logger.warning(f"Could not find model '{current_model_name}' in dropdown, will use first available model and update config")
            # If the configured model is not available, use the first available one
            if self.model_combo.count() > 0:
                self.model_combo.setCurrentIndex(0)
                first_model = self.model_combo.itemData(0)
                if first_model:
                    # Update config to match fallback
                    self.config_manager.set_config_value('transcription', 'model', first_model['name'])
                    if self.logger:
                        self.logger.info(f"Config updated to fallback model: {first_model['name']}")

    def _on_model_selected(self, index):
        if index == -1:
            return

        selected_model_data = self.model_combo.itemData(index)
        if not selected_model_data:
            if self.logger:
                self.logger.warning(f"No model data found for dropdown index {index}")
            return

        model_name = selected_model_data['name']
        if self.logger:
            self.logger.info(f"User selected model: {model_name}")

        self._load_whisper_model(model_name)

    def _load_whisper_model(self, model_name: str):
        if self.logger:
            self.logger.info(f"Request to load model: {model_name}")
        
        if self.is_model_loading:
            if self.logger:
                self.logger.warning("Model is already being loaded.")
            return

        # Find the base model name (e.g., 'tiny.en' -> 'tiny')
        base_model_name = model_name.split('.')[0]
        required_memory = MODEL_MEMORY_REQ.get(base_model_name, 1 * 1024**3) # Default to 1GB
        
        available_memory = psutil.virtual_memory().available

        if self.logger:
            self.logger.debug(f"Memory check for model '{model_name}': required={required_memory / 1024**3:.1f}GB, available={available_memory / 1024**3:.1f}GB")

        if available_memory < required_memory:
            msg = f"Not enough memory to load model '{model_name}'.\n" \
                  f"Required: {required_memory / 1024**3:.1f} GB\n" \
                  f"Available: {available_memory / 1024**3:.1f} GB"
            QMessageBox.warning(self, "Memory Error", msg)
            
            if self.logger:
                self.logger.warning(f"Insufficient memory to load model '{model_name}'")
            # TODO: Revert dropdown selection to the previously loaded model
            return

        self.is_model_loading = True
        self.model_combo.setEnabled(False)
        self.status_label.setText(f"Loading model: {model_name}...")
        
        if self.logger:
            self.logger.info(f"Starting model load for: {model_name}")
        
        thread = QThread()
        # Keep a reference to the thread to prevent it from being garbage collected
        self.load_thread = thread
        worker = ModelLoadWorker(model_name, self.whisper_model, self.config_manager)
        worker.moveToThread(thread)
        
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_model_load_finished)
        worker.error.connect(self._on_model_load_error)
        
        # Clean up the thread and worker
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        thread.start()

    def _on_model_load_finished(self, model):
        self.whisper_model = model
        self.is_model_loading = False
        self.model_combo.setEnabled(True)
        self.status_label.setText("Ready")
        if self.logger:
            model_name = self.config_manager.get_config_value('transcription', 'model')
            self.logger.info(f"Successfully loaded model: {model_name}")

    def _on_model_load_error(self, error_message):
        self.is_model_loading = False
        self.model_combo.setEnabled(True)
        self.status_label.setText("Error loading model")
        QMessageBox.critical(self, "Model Load Error", error_message)
        if self.logger:
            self.logger.error(f"Failed to load model: {error_message}")
        # TODO: Revert dropdown to previous model

    def _setup_recorder(self) -> Optional[AudioRecorder]:
        """Set up the audio recorder with configuration."""
        try:
            # Get device configuration
            device_id = self.config_manager.get_config_value('audio', 'device_id')
            sample_rate = self.config_manager.get_config_value('audio', 'sample_rate', 16000)
            channels = self.config_manager.get_config_value('audio', 'channels', 1)
            buffer_size = self.config_manager.get_config_value('audio', 'buffer_size', 5)
            
            # Create recorder
            recorder = AudioRecorder(
                device_id=device_id,
                sample_rate=sample_rate,
                channels=channels,
                blocksize=1024
            )
            
            # Set up callbacks
            recorder.audio_chunk_callback = self.handle_audio_chunk
            
            # Set up silence detection callbacks
            recorder.set_silence_callbacks(
                on_silence_detected=self._on_silence_detected,
                on_speech_detected=self._on_speech_detected,
                on_noise_learned=self._on_noise_learned
            )
            
            if self.logger:
                self.logger.info(f"Audio recorder initialized with device {device_id}")
            
            return recorder
            
        except Exception as e:
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
        if self.state_machine.get_state() == RecordingState.IDLE:
            self._start_recording()
        elif self.state_machine.get_state() == RecordingState.RECORDING:
            self._stop_recording()
    
    def _start_recording(self):
        """Start recording audio."""
        if not self.recorder:
            if self.logger:
                self.logger.error("No audio recorder available.")
            return
            
        if self.state_machine.get_state() != RecordingState.IDLE:
            if self.logger:
                self.logger.warning("Recording is already in progress.")
            return
        
        self.state_machine.handle_event(RecordingEvent.START_REQUESTED)
        
        if self.logger:
            self.logger.info("Recording started.")
    
    def _stop_recording(self):
        """Stop recording and process the audio."""
        if not self.recorder:
            if self.logger:
                self.logger.error("No audio recorder available.")
            return
        
        # Stop the waveform widget
        self.waveform_widget.stop_recording()
        self.state_machine.handle_event(RecordingEvent.STOP_REQUESTED)
        
        if self.logger:
            self.logger.info("Recording stopped.")

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
        if event.key() == Qt.Key.Key_Escape:
            if self.logger:
                self.logger.info("ESC key pressed - aborting recording")
            if self.state_machine.get_state() == RecordingState.RECORDING:
                self.state_machine.handle_event(RecordingEvent.ABORT_REQUESTED)
            event.accept()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.logger:
                self.logger.info("Enter key pressed - finishing recording early")
            if self.state_machine.get_state() == RecordingState.RECORDING:
                self.state_machine.handle_event(RecordingEvent.STOP_REQUESTED)
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def _abort_recording(self):
        """Abort recording and discard audio."""
        if not self.recorder:
            if self.logger:
                self.logger.error("No audio recorder available.")
            return
        
        # Stop the waveform widget
        self.waveform_widget.stop_recording()
        
        # Stop recording if active
        if self.state_machine.get_state() == RecordingState.RECORDING:
            self._stop_recording()
        
        # Clear any recorded audio
        if self.recorder:
            self.recorder.clear_audio_buffer()
        
        if self.logger:
            self.logger.info("Recording aborted.")
        
        # Reset UI state
        self._reset_ui_state()
        
        # Hide window (app continues running)
        self.hide()
        self.window_closed.emit()
    
    def _finish_recording_early(self):
        """Finish recording early and process the audio."""
        if not self.recorder:
            if self.logger:
                self.logger.error("No audio recorder available.")
            return
        
        # Stop recording if active
        if self.state_machine.get_state() == RecordingState.RECORDING:
            self._stop_recording()
        
        # Process the recorded audio
        text = self._get_transcribed_text()
        if text:
            self._handle_text_output(text)
        else:
            if self.logger:
                self.logger.warning("No text was transcribed.")
        
        if self.logger:
            self.logger.info("Recording finished early.")
        
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
        self.state_machine.reset_to_idle()
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
        """Handle silence detection event."""
        if self.logger:
            self.logger.info("Silence detected, stopping recording.")
        if self.state_machine.get_state() == RecordingState.RECORDING:
            self.state_machine.handle_event(RecordingEvent.SILENCE_DETECTED)

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
        if self.recorder and self.state_machine.get_state() == RecordingState.RECORDING:
            self.recorder.stop()
        
        # Reset the recorder
        if self.recorder:
            self.recorder.reset_silence_detection()
            self.recorder.clear_audio_buffer()
        
        self.state_machine.reset_to_idle()
        self.waveform_widget.reset_plot()
        self._reset_ui_state()
        if self.logger:
            self.logger.info("W4LMainWindow reset for new test.")

    def _setup_state_machine(self) -> RecordingStateMachine:
        """Set up the recording state machine with callbacks."""
        state_machine = RecordingStateMachine()
        
        # Connect state machine signals to UI updates
        state_machine.state_changed.connect(self._on_state_changed)
        state_machine.error_occurred.connect(self._on_state_machine_error)
        state_machine.recovery_attempted.connect(self._on_recovery_attempted)
        
        # Set up callbacks for external actions
        state_machine.on_start_recording = self._state_machine_start_recording
        state_machine.on_stop_recording = self._state_machine_stop_recording
        state_machine.on_abort_recording = self._state_machine_abort_recording
        state_machine.on_error = self._state_machine_handle_error
        state_machine.on_recovery = self._state_machine_attempt_recovery
        
        return state_machine
    
    def _on_state_changed(self, old_state: RecordingState, new_state: RecordingState, event: RecordingEvent):
        """Handle state machine state changes and update UI accordingly."""
        if self.logger:
            self.logger.info(f"State changed: {old_state.name} -> {new_state.name} (event: {event.name})")
        
        # Update UI based on new state
        if new_state == RecordingState.IDLE:
            self._update_ui_for_idle()
        elif new_state == RecordingState.RECORDING:
            self._update_ui_for_recording()
        elif new_state == RecordingState.STOPPING:
            self._update_ui_for_stopping()
        elif new_state == RecordingState.FINISHED:
            self._update_ui_for_finished()
        elif new_state == RecordingState.ABORTED:
            self._update_ui_for_aborted()
        elif new_state == RecordingState.ERROR:
            self._update_ui_for_error()
        elif new_state == RecordingState.RECOVERING:
            self._update_ui_for_recovering()
    
    def _on_state_machine_error(self, error_message: str):
        """Handle state machine errors."""
        if self.logger:
            self.logger.error(f"State machine error: {error_message}")
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def _on_recovery_attempted(self):
        """Handle recovery attempts."""
        if self.logger:
            self.logger.info("Recovery attempt started")
        self.status_label.setText("Recovering...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
    
    def _state_machine_start_recording(self):
        """Callback for state machine to start recording."""
        try:
            if self.recorder:
                self.recorder.start()
                self.recorder.start_silence_detection()
                if self.logger:
                    self.logger.info("Recording started via state machine")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error starting recording: {e}")
            self.state_machine.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _state_machine_stop_recording(self):
        """Callback for state machine to stop recording."""
        try:
            if self.recorder:
                self.recorder.stop()
                self.recorder.stop_silence_detection()
                if self.logger:
                    self.logger.info("Recording stopped via state machine")
                # Signal cleanup completion
                self.state_machine.handle_event(RecordingEvent.CLEANUP_COMPLETED)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping recording: {e}")
            self.state_machine.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _state_machine_abort_recording(self):
        """Callback for state machine to abort recording."""
        try:
            if self.recorder:
                self.recorder.stop()
                self.recorder.stop_silence_detection()
                self.recorder.clear_audio_buffer()  # Clear any recorded audio
                if self.logger:
                    self.logger.info("Recording aborted via state machine")
                # Don't call CLEANUP_COMPLETED - abort should stay in ABORTED state
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error aborting recording: {e}")
            self.state_machine.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _state_machine_handle_error(self, error: Exception):
        """Callback for state machine to handle errors."""
        if self.logger:
            self.logger.error(f"State machine error handler: {error}")
        self.status_label.setText(f"Error: {str(error)}")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def _state_machine_attempt_recovery(self):
        """Callback for state machine to attempt recovery."""
        try:
            if self.recorder:
                self.recorder.force_recovery()
                if self.logger:
                    self.logger.info("Recovery attempted via state machine")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Recovery failed: {e}")
            self.state_machine.handle_event(RecordingEvent.RECOVERY_FAILED, error=e)
    
    def _update_ui_for_idle(self):
        """Update UI for IDLE state."""
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
        self.instruction_label.setText("Click Start Recording to begin")
    
    def _update_ui_for_recording(self):
        """Update UI for RECORDING state."""
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
        self.instruction_label.setText("Speak now... Press ESC to cancel or Enter to finish early")
        # Start waveform recording
        self.waveform_widget.start_recording()
    
    def _update_ui_for_stopping(self):
        """Update UI for STOPPING state."""
        self.record_button.setEnabled(False)
        self.status_label.setText("Stopping...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        self.instruction_label.setText("Processing recording...")
    
    def _update_ui_for_finished(self):
        """Update UI for FINISHED state."""
        self.record_button.setEnabled(True)
        self.status_label.setText("Recording completed")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.instruction_label.setText("Recording saved successfully")
        # Reset to idle after a short delay
        QApplication.processEvents()
        self.state_machine.reset_to_idle()
    
    def _update_ui_for_aborted(self):
        """Update UI for ABORTED state."""
        self.record_button.setEnabled(True)
        self.status_label.setText("Recording cancelled")
        self.status_label.setStyleSheet("color: #95a5a6; font-weight: bold;")
        self.instruction_label.setText("Recording was cancelled")
        # Reset to idle after a short delay
        QApplication.processEvents()
        self.state_machine.reset_to_idle()
    
    def _update_ui_for_error(self):
        """Update UI for ERROR state."""
        self.record_button.setEnabled(True)
        self.status_label.setText("Error occurred")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.instruction_label.setText("An error occurred during recording")
    
    def _update_ui_for_recovering(self):
        """Update UI for RECOVERING state."""
        self.record_button.setEnabled(False)
        self.status_label.setText("Recovering...")
        self.status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        self.instruction_label.setText("Attempting to recover from error...")

if __name__ == '__main__':
    # This block is for direct testing of the main window
    app = QApplication(sys.argv)
    
    # Create a ConfigManager for testing
    from config import ConfigManager
    config_manager = ConfigManager()
    
    # Create a ModelManager for testing
    from transcription.model_manager import ModelManager
    model_manager = ModelManager()
    
    main_win = W4LMainWindow(config_manager, model_manager)
    main_win.show()
    sys.exit(app.exec())