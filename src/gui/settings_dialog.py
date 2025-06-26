#!/usr/bin/env python3
"""
Settings dialog for W4L.

Provides configuration options for audio settings, device selection, and other preferences.
"""

import logging
import os
import subprocess
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QSpinBox,
    QLineEdit, QPushButton, QDialogButtonBox, QWidget, QHBoxLayout,
    QFileDialog, QLabel, QTabWidget, QGroupBox, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from datetime import datetime

from audio.device_detector import AudioDeviceDetector, AudioDevice
from transcription.model_manager import ModelManager
from config import ConfigManager


class DownloadWorker(QObject):
    """Worker thread for downloading models."""
    finished = pyqtSignal()
    progress = pyqtSignal(int, int)
    error = pyqtSignal(str)
    verification_complete = pyqtSignal(bool)

    def __init__(self, model_manager: ModelManager, model_name: str, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.model_name = model_name
        self.logger = logging.getLogger("w4l.gui.download_worker")

    def run(self):
        try:
            self.logger.info(f"DownloadWorker: Starting download for {self.model_name}")
            self.model_manager.download_model(self.model_name, self.progress.emit)
            self.logger.info(f"DownloadWorker: Download and verification complete for {self.model_name}")
            self.verification_complete.emit(True)
        except Exception as e:
            self.logger.error(f"DownloadWorker: Error downloading {self.model_name}: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class ModelListItem(QWidget):
    """Custom widget for an item in the model list."""
    def __init__(self, model_info: dict, model_manager: ModelManager, parent_dialog, parent=None):
        super().__init__(parent)
        self.model_info = model_info
        self.model_manager = model_manager
        self.parent_dialog = parent_dialog

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.name_label = QLabel(self.model_info['name'])
        size_bytes = self.model_info.get('size_bytes', 0)
        if size_bytes:
            size_mb = size_bytes / (1024 * 1024)
            self.size_label = QLabel(f"{size_mb:.1f} MB")
        else:
            self.size_label = QLabel("Unknown")

        self.status_label = QLabel()
        self.action_button = QPushButton()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        
        layout.addWidget(self.name_label, 2)
        layout.addWidget(self.size_label, 1)
        layout.addStretch(1)
        layout.addWidget(self.status_label, 1)
        layout.addWidget(self.action_button, 1)
        layout.addWidget(self.progress_bar, 2)

        self.action_button.clicked.connect(self.handle_action_click)
        self.update_status()

    def update_status(self):
        is_downloaded = self.model_info.get('is_downloaded', False)
        is_verified = self.model_info.get('is_verified', False)

        if is_verified:
            self.status_label.setText("Downloaded")
            self.status_label.setStyleSheet("color: green;")
            self.status_label.setToolTip("Model is downloaded and verified.")
            self.action_button.setText("Delete")
            self.action_button.setEnabled(True)
            self.progress_bar.setVisible(False)
        elif is_downloaded and not is_verified:
            self.status_label.setText("Corrupted")
            self.status_label.setStyleSheet("color: orange;")
            self.status_label.setToolTip("Model file is present but failed verification. Please re-download.")
            self.action_button.setText("Delete")
            self.action_button.setEnabled(True)
            self.progress_bar.setVisible(False)
        else:
            self.status_label.setText("Not downloaded")
            self.status_label.setStyleSheet("color: #888;")
            self.status_label.setToolTip("Model is not downloaded.")
            self.action_button.setText("Download")
            self.action_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def handle_action_click(self):
        import logging
        logging.getLogger("w4l.gui.model_list_item").info(f"Action button clicked for model: {self.model_info['name']} (action: {self.action_button.text()})")
        if self.action_button.text() == "Download":
            self.parent_dialog.start_model_download(self)
        elif self.action_button.text() == "Delete":
            self.parent_dialog.delete_model(self)

    def download_started(self):
        self.action_button.setEnabled(False)
        self.status_label.setText("Downloading...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def download_progress(self, bytes_downloaded, total_bytes):
        if total_bytes > 0:
            percent = int((bytes_downloaded / total_bytes) * 100)
            self.progress_bar.setValue(percent)

    def download_finished(self, success, error_msg=None):
        self.progress_bar.setVisible(False)
        self.action_button.setEnabled(True)
        if success:
            self.model_info['is_downloaded'] = True
            self.model_info['is_verified'] = True
        else:
            self.model_info['is_downloaded'] = False
            self.model_info['is_verified'] = False
        self.update_status()
        if error_msg:
            self.status_label.setText("Error")
            self.setToolTip(error_msg)


class SettingsDialog(QDialog):
    """Settings dialog window."""
    
    def __init__(self, config_manager: ConfigManager, model_manager: ModelManager, metadata_updated_signal=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.model_manager = model_manager
        self.logger = logging.getLogger("w4l.gui.settings_dialog")
        self.download_threads = {}
        
        self.device_detector = AudioDeviceDetector()
        self.devices = []
        
        self.setWindowTitle("W4L Settings")
        self.setMinimumWidth(500)
        
        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        
        # --- Tab Widget ---
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Create tabs
        audio_tab = QWidget()
        model_tab = QWidget()
        silence_tab = QWidget()
        
        tab_widget.addTab(audio_tab, "Audio")
        tab_widget.addTab(model_tab, "Models")
        tab_widget.addTab(silence_tab, "Silence Detection")
        
        # --- Populate Audio Tab ---
        self.setup_audio_tab(audio_tab)
        
        # --- Populate Model Tab ---
        self.setup_model_tab(model_tab)
        
        # --- Populate Silence Detection Tab ---
        self.setup_silence_tab(silence_tab)

        # --- Common Buttons ---
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        main_layout.addWidget(self.button_box)
        
        # --- Connections ---
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        apply_button = self.button_box.button(QDialogButtonBox.StandardButton.Apply)
        if apply_button:
            apply_button.clicked.connect(self.apply_settings)
        
        self.load_settings()
        self.update_ui_visibility()

        # TODO: This blocks the UI thread because it makes network requests.
        # This should be moved to a background thread.
        self.populate_model_list()

        # Connect to metadata updated signal if provided
        if metadata_updated_signal is not None:
            metadata_updated_signal.connect(self._on_metadata_updated)

    def setup_audio_tab(self, tab):
        """Create and populate the Audio settings tab."""
        layout = QVBoxLayout(tab)
        
        # --- Audio Devices Group ---
        devices_group = QGroupBox("Audio Devices")
        devices_layout = QFormLayout(devices_group)
        
        self.audio_device_combo = QComboBox()
        devices_layout.addRow("Input Device:", self.audio_device_combo)
        
        # --- Capture Settings Group ---
        capture_group = QGroupBox("Capture Settings")
        capture_layout = QFormLayout(capture_group)

        self.capture_mode_combo = QComboBox()
        self.capture_mode_combo.addItem("Streaming", "streaming")
        self.capture_mode_combo.addItem("File-based", "file_based")

        # Widgets for the conditional "Save Audio To" section
        self.file_path_widget = QWidget()
        file_path_layout = QHBoxLayout(self.file_path_widget)
        file_path_layout.setContentsMargins(0, 0, 0, 0)
        self.file_path_edit = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        file_path_layout.addWidget(self.file_path_edit)
        file_path_layout.addWidget(self.browse_button)
        
        self.description_label = QLabel("Audio files will be saved in a 'W4L-Recordings' subfolder at this location.")
        self.description_label.setStyleSheet("font-size: 9pt; color: #666;")
        self.description_label.setWordWrap(True)

        self.buffer_size_spinbox = QSpinBox()
        self.buffer_size_spinbox.setRange(1, 30)
        self.buffer_size_spinbox.setSuffix(" seconds")
        
        self.save_path_label = QLabel("Save Audio To:")

        # Reorder the layout for better flow
        capture_layout.addRow("Audio Buffer Size:", self.buffer_size_spinbox)
        capture_layout.addRow("Capture Mode:", self.capture_mode_combo)
        capture_layout.addRow(self.save_path_label, self.file_path_widget)
        capture_layout.addRow(self.description_label)
        
        # --- Read-only Info Group ---
        info_group = QGroupBox("Technical Info (Read-only)")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Sample Rate:", QLabel("16000 Hz"))
        info_layout.addRow("Channels:", QLabel("1 (Mono)"))
        info_layout.addRow("Bit Depth:", QLabel("16-bit"))
        
        layout.addWidget(devices_group)
        layout.addWidget(capture_group)
        layout.addWidget(info_group)
        layout.addStretch()
        
        # --- Connections for this tab ---
        self.capture_mode_combo.currentIndexChanged.connect(self.update_ui_visibility)
        self.browse_button.clicked.connect(self.browse_for_directory)

    def setup_model_tab(self, tab):
        """Create and populate the Model settings tab."""
        layout = QVBoxLayout(tab)
        
        # Always refresh metadata from disk before showing the model list
        self.model_manager.metadata_manager.refresh_metadata(fetch_online=False)
        
        # --- Downloaded Models Group ---
        models_group = QGroupBox("Downloaded Models")
        models_layout = QVBoxLayout(models_group)
        
        # Add refresh button and last refreshed label
        refresh_layout = QHBoxLayout()
        self.refresh_models_button = QPushButton("Refresh models")
        self.last_refreshed_label = QLabel()
        refresh_layout.addWidget(self.refresh_models_button)
        refresh_layout.addWidget(self.last_refreshed_label)
        refresh_layout.addStretch(1)
        models_layout.addLayout(refresh_layout)
        
        self.model_list_widget = QListWidget()
        models_layout.addWidget(self.model_list_widget)
        
        # --- Model Path Group ---
        path_group = QGroupBox("Model Storage")
        path_layout = QFormLayout(path_group)
        
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setReadOnly(True)
        self.open_model_path_button = QPushButton("Open Folder")
        
        path_layout.addRow("Models Path:", self.model_path_edit)
        path_layout.addRow("", self.open_model_path_button)
        
        layout.addWidget(models_group)
        layout.addWidget(path_group)
        
        # --- Connections for this tab ---
        self.open_model_path_button.clicked.connect(self.open_model_directory)
        self.refresh_models_button.clicked.connect(self.handle_refresh_models)
        self.update_last_refreshed_label()

    def setup_silence_tab(self, tab):
        """Create and populate the Silence Detection settings tab."""
        layout = QVBoxLayout(tab)
        
        # --- Basic Settings Group ---
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout(basic_group)
        
        # Silence threshold (convert from float to percentage for UI)
        self.silence_threshold_spinbox = QSpinBox()
        self.silence_threshold_spinbox.setRange(1, 100)
        self.silence_threshold_spinbox.setSuffix("%")
        self.silence_threshold_spinbox.setToolTip("Threshold for detecting silence (higher = more sensitive)")
        
        # Silence duration
        self.silence_duration_spinbox = QSpinBox()
        self.silence_duration_spinbox.setRange(1, 30)
        self.silence_duration_spinbox.setSuffix(" seconds")
        self.silence_duration_spinbox.setToolTip("How long to wait in silence before stopping recording")
        
        # Detection strategy dropdown
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("Hybrid (Recommended)", "hybrid")
        self.strategy_combo.addItem("RMS Energy", "rms")
        self.strategy_combo.addItem("Spectral Analysis", "spectral")
        self.strategy_combo.addItem("Adaptive Noise Floor", "adaptive")
        self.strategy_combo.setToolTip("Method used to detect silence")
        
        basic_layout.addRow("Silence Threshold:", self.silence_threshold_spinbox)
        basic_layout.addRow("Silence Duration:", self.silence_duration_spinbox)
        basic_layout.addRow("Detection Strategy:", self.strategy_combo)
        
        # --- Adaptive Settings Group ---
        adaptive_group = QGroupBox("Adaptive Noise Detection")
        adaptive_layout = QFormLayout(adaptive_group)
        
        # Enable adaptive detection
        self.enable_adaptive_checkbox = QComboBox()
        self.enable_adaptive_checkbox.addItem("Enabled", True)
        self.enable_adaptive_checkbox.addItem("Disabled", False)
        self.enable_adaptive_checkbox.setToolTip("Learn and adapt to background noise like laptop fans")
        
        # Noise learning duration
        self.noise_learning_spinbox = QSpinBox()
        self.noise_learning_spinbox.setRange(1, 10)
        self.noise_learning_spinbox.setSuffix(" seconds")
        self.noise_learning_spinbox.setToolTip("Time to learn background noise when recording starts")
        
        # Noise margin
        self.noise_margin_spinbox = QSpinBox()
        self.noise_margin_spinbox.setRange(11, 30)
        self.noise_margin_spinbox.setSuffix("x")
        self.noise_margin_spinbox.setToolTip("Multiplier above learned noise floor (higher = less sensitive)")
        
        # Adaptation rate
        self.adaptation_rate_spinbox = QSpinBox()
        self.adaptation_rate_spinbox.setRange(1, 50)
        self.adaptation_rate_spinbox.setSuffix("%")
        self.adaptation_rate_spinbox.setToolTip("How quickly to adapt to new noise levels")
        
        adaptive_layout.addRow("Adaptive Detection:", self.enable_adaptive_checkbox)
        adaptive_layout.addRow("Learning Duration:", self.noise_learning_spinbox)
        adaptive_layout.addRow("Noise Margin:", self.noise_margin_spinbox)
        adaptive_layout.addRow("Adaptation Rate:", self.adaptation_rate_spinbox)
        
        # --- Advanced Settings Group ---
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Enable spectral detection
        self.enable_spectral_checkbox = QComboBox()
        self.enable_spectral_checkbox.addItem("Enabled", True)
        self.enable_spectral_checkbox.addItem("Disabled", False)
        self.enable_spectral_checkbox.setToolTip("Use frequency analysis for better detection")
        
        # Minimum speech duration
        self.min_speech_spinbox = QSpinBox()
        self.min_speech_spinbox.setRange(1, 20)
        self.min_speech_spinbox.setSuffix(" seconds")
        self.min_speech_spinbox.setToolTip("Minimum speech duration before silence detection activates")
        
        advanced_layout.addRow("Spectral Analysis:", self.enable_spectral_checkbox)
        advanced_layout.addRow("Min Speech Duration:", self.min_speech_spinbox)
        
        # --- Info Section ---
        info_label = QLabel(
            "💡 <b>How it works:</b><br>"
            "• <b>Learning Phase:</b> First few seconds learn your background noise (laptop fan, etc.)<br>"
            "• <b>Adaptive Threshold:</b> Sets detection level above your background noise<br>"
            "• <b>Speech Detection:</b> Triggers when you speak above the adaptive threshold<br>"
            "• <b>Silence Detection:</b> Triggers when audio returns to background noise level<br><br>"
            "🎧 <b>Perfect for:</b> Laptop fans, air conditioning, office noise, etc."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #f0f8ff; padding: 10px; border-radius: 5px;")
        
        # Add all groups to layout
        layout.addWidget(basic_group)
        layout.addWidget(adaptive_group)
        layout.addWidget(advanced_group)
        layout.addWidget(info_label)
        layout.addStretch()

    def load_settings(self):
        """Load settings from the config manager and populate the UI."""
        # Load audio settings
        self.devices = self.device_detector.get_input_devices()
        self.audio_device_combo.clear()
        for device in self.devices:
            self.audio_device_combo.addItem(device.name, device.device_id)
        
        device_id = self.config_manager.get_config_value('audio', 'device_id')
        index = self.audio_device_combo.findData(device_id)
        if index != -1:
            self.audio_device_combo.setCurrentIndex(index)
        
        capture_mode = self.config_manager.get_config_value('audio', 'capture_mode', 'streaming')
        index = self.capture_mode_combo.findData(capture_mode)
        if index != -1:
            self.capture_mode_combo.setCurrentIndex(index)
            
        save_path = self.config_manager.get_config_value('audio', 'save_path', os.path.expanduser("~"))
        self.file_path_edit.setText(save_path)

        buffer_size = self.config_manager.get_config_value('audio', 'buffer_size', 5)
        self.buffer_size_spinbox.setValue(buffer_size)
        
        # Load model info
        self.model_path_edit.setText(str(self.model_manager.models_path))
        
        # Load silence detection settings
        self.load_silence_settings()
    
    def load_silence_settings(self):
        """Load silence detection settings from config."""
        # Convert float threshold to percentage for UI
        threshold = self.config_manager.get_config_value('audio', 'silence_threshold', 0.01)
        threshold_percent = int(threshold * 1000)  # Convert 0.01 to 10%
        self.silence_threshold_spinbox.setValue(threshold_percent)
        
        # Load other settings
        silence_duration = self.config_manager.get_config_value('audio', 'silence_duration', 5.0)
        self.silence_duration_spinbox.setValue(int(silence_duration))
        
        strategy = self.config_manager.get_config_value('audio', 'silence_strategy', 'hybrid')
        index = self.strategy_combo.findData(strategy)
        if index != -1:
            self.strategy_combo.setCurrentIndex(index)
        
        # Adaptive settings
        enable_adaptive = self.config_manager.get_config_value('audio', 'enable_adaptive_detection', True)
        index = self.enable_adaptive_checkbox.findData(enable_adaptive)
        if index != -1:
            self.enable_adaptive_checkbox.setCurrentIndex(index)
        
        noise_learning = self.config_manager.get_config_value('audio', 'noise_learning_duration', 3.0)
        self.noise_learning_spinbox.setValue(int(noise_learning))
        
        noise_margin = self.config_manager.get_config_value('audio', 'noise_margin', 1.5)
        self.noise_margin_spinbox.setValue(int(noise_margin * 10))  # Convert 1.5 to 15
        
        adaptation_rate = self.config_manager.get_config_value('audio', 'adaptation_rate', 0.1)
        self.adaptation_rate_spinbox.setValue(int(adaptation_rate * 100))  # Convert 0.1 to 10
        
        # Advanced settings
        enable_spectral = self.config_manager.get_config_value('audio', 'enable_spectral_detection', True)
        index = self.enable_spectral_checkbox.findData(enable_spectral)
        if index != -1:
            self.enable_spectral_checkbox.setCurrentIndex(index)
        
        min_speech = self.config_manager.get_config_value('audio', 'min_speech_duration', 0.5)
        self.min_speech_spinbox.setValue(int(min_speech * 10))  # Convert 0.5 to 5
        
    def apply_settings(self):
        """Save the current settings to the ConfigManager."""
        self.logger.info("Applying settings...")
        
        selected_device_index = self.audio_device_combo.currentIndex()
        if selected_device_index != -1:
            selected_device = self.audio_device_combo.itemData(selected_device_index)
            self.config_manager.set_config_value('audio', 'device', selected_device.name)
            self.config_manager.set_config_value('audio', 'device_id', selected_device.device_id)

        self.config_manager.set_config_value('audio', 'capture_mode', self.capture_mode_combo.currentData())
        self.config_manager.set_config_value('audio', 'buffer_size', self.buffer_size_spinbox.value())
        self.config_manager.set_config_value('audio', 'save_path', self.file_path_edit.text())
        
        # Save silence detection settings
        self.save_silence_settings()
        
        self.logger.info("Settings applied and saved.")
        
    def save_silence_settings(self):
        """Save silence detection settings to config."""
        # Convert percentage back to float
        threshold_percent = self.silence_threshold_spinbox.value()
        threshold = threshold_percent / 1000.0  # Convert 10% back to 0.01
        self.config_manager.set_config_value('audio', 'silence_threshold', threshold)
        
        # Save other settings
        self.config_manager.set_config_value('audio', 'silence_duration', float(self.silence_duration_spinbox.value()))
        self.config_manager.set_config_value('audio', 'silence_strategy', self.strategy_combo.currentData())
        
        # Adaptive settings
        self.config_manager.set_config_value('audio', 'enable_adaptive_detection', self.enable_adaptive_checkbox.currentData())
        self.config_manager.set_config_value('audio', 'noise_learning_duration', float(self.noise_learning_spinbox.value()))
        
        noise_margin = self.noise_margin_spinbox.value() / 10.0  # Convert 15 back to 1.5
        self.config_manager.set_config_value('audio', 'noise_margin', noise_margin)
        
        adaptation_rate = self.adaptation_rate_spinbox.value() / 100.0  # Convert 10 back to 0.1
        self.config_manager.set_config_value('audio', 'adaptation_rate', adaptation_rate)
        
        # Advanced settings
        self.config_manager.set_config_value('audio', 'enable_spectral_detection', self.enable_spectral_checkbox.currentData())
        
        min_speech = self.min_speech_spinbox.value() / 10.0  # Convert 5 back to 0.5
        self.config_manager.set_config_value('audio', 'min_speech_duration', min_speech)

    def update_ui_visibility(self):
        """Show or hide settings based on other selections."""
        is_file_based = self.capture_mode_combo.currentData() == "file_based"
        self.save_path_label.setVisible(is_file_based)
        self.file_path_widget.setVisible(is_file_based)
        self.description_label.setVisible(is_file_based)

    def browse_for_directory(self):
        """Open a dialog to select a directory."""
        current_path = self.file_path_edit.text()
        
        # Expand user-specific part of the path (like '~')
        expanded_path = os.path.expanduser(current_path)

        # Check if the path exists, if not, fall back to home directory
        start_path = expanded_path if os.path.isdir(expanded_path) else os.path.expanduser("~")

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory for Recordings",
            start_path
        )
        if directory:
            self.file_path_edit.setText(directory)

    def open_model_directory(self):
        """Open the directory where models are stored."""
        path = self.model_path_edit.text()
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.logger.error(f"Could not open model directory '{path}': {e}")

    def populate_model_list(self):
        """Populate the list of models."""
        self.model_list_widget.clear()
        self.model_path_edit.setText(str(self.model_manager.models_path))
        
        # This can be slow and should be run in a background thread
        try:
            models = self.model_manager.list_models()
            for model_info in models:
                item = QListWidgetItem(self.model_list_widget)
                widget = ModelListItem(model_info, self.model_manager, self)
                item.setSizeHint(widget.sizeHint())
                self.model_list_widget.addItem(item)
                self.model_list_widget.setItemWidget(item, widget)
        except Exception as e:
            self.logger.error(f"Failed to populate model list: {e}")
            # Optionally, show an error message in the list
            self.model_list_widget.addItem("Error loading model list.")

    def start_model_download(self, item_widget: ModelListItem):
        self.logger.info(f"start_model_download called for model: {item_widget.model_info['name']}")
        model_name = item_widget.model_info['name']
        
        if model_name in self.download_threads and self.download_threads[model_name].isRunning():
            self.logger.warning(f"Download for {model_name} already in progress.")
            return

        thread = QThread()
        worker = DownloadWorker(self.model_manager, model_name)
        worker.moveToThread(thread)

        def on_finished(success, error_msg=None):
            self.logger.info(f"Download finished for {model_name}, success={success}, error={error_msg}")
            item_widget.download_finished(success, error_msg)
            if model_name in self.download_threads:
                del self.download_threads[model_name]
            self.populate_model_list()
            self.update_last_refreshed_label()
        
        def on_success(verified):
            self.logger.info(f"Download success for {model_name}, verified={verified}")
            on_finished(verified)

        def on_error(msg):
            self.logger.error(f"Download error for {model_name}: {msg}")
            on_finished(False, msg)
            QMessageBox.critical(self, "Model Download Error", f"Failed to download {model_name}: {msg}")

        # Connections
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        worker.progress.connect(item_widget.download_progress)
        worker.verification_complete.connect(on_success)
        worker.error.connect(on_error)

        thread.start()
        self.download_threads[model_name] = thread
        item_widget.download_started()
        self.logger.info(f"Download thread started for {model_name}")

    def delete_model(self, item_widget: ModelListItem):
        """Delete a model file and update metadata immediately."""
        model_info = item_widget.model_info
        file_path = model_info.get('filepath')
        model_name = model_info.get('name')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.logger.info(f"Deleted model: {file_path}")
                # Update metadata to not_downloaded and preserve history
                meta = self.model_manager.metadata_manager.data["models"].get(model_name)
                if meta:
                    now = datetime.utcnow().isoformat() + 'Z'
                    meta["status"] = "not_downloaded"
                    # Do not remove history
                    self.model_manager.metadata_manager.save_metadata()
                model_info['is_downloaded'] = False
                model_info['is_verified'] = False
                item_widget.update_status()
                self.populate_model_list()
                self.update_last_refreshed_label()
            except Exception as e:
                self.logger.error(f"Failed to delete model {file_path}: {e}")

    def accept(self):
        self.apply_settings()
        super().accept()

    def _on_metadata_updated(self):
        # Only refresh if dialog is visible
        if self.isVisible():
            self.logger.info("Model metadata updated, refreshing model list.")
            self.populate_model_list() 

    def handle_refresh_models(self):
        self.logger.info("Manual model metadata refresh triggered by user.")
        self.model_manager.metadata_manager.refresh_metadata(fetch_online=True)
        self.populate_model_list()
        self.update_last_refreshed_label()

    def update_last_refreshed_label(self):
        last_refreshed = self.model_manager.metadata_manager.data.get("last_refreshed")
        if last_refreshed:
            self.last_refreshed_label.setText(f"Last refreshed: {last_refreshed}")
        else:
            self.last_refreshed_label.setText("Last refreshed: unknown")

    def closeEvent(self, event):
        # Ensure all download threads are finished before closing
        self.logger.info("SettingsDialog: Closing, waiting for download threads to finish.")
        for model_name, thread in list(self.download_threads.items()):
            if thread.isRunning():
                self.logger.info(f"Waiting for download thread to finish: {model_name}")
                thread.quit()
                thread.wait()
        self.download_threads.clear()
        super().closeEvent(event) 