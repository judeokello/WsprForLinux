#!/usr/bin/env python3
"""
Settings dialog for W4L.

Provides configuration options for audio settings, device selection, and other preferences.
"""

import logging
import os
import subprocess
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QSpinBox,
    QLineEdit, QPushButton, QDialogButtonBox, QWidget, QHBoxLayout,
    QFileDialog, QLabel, QTabWidget, QGroupBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt

from audio.device_detector import AudioDeviceDetector, AudioDevice


class SettingsDialog(QDialog):
    """Settings dialog window."""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = logging.getLogger("w4l.gui.settings_dialog")
        
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
        
        # --- Downloaded Models Group ---
        models_group = QGroupBox("Downloaded Models")
        models_layout = QVBoxLayout(models_group)
        
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
        """Load settings from ConfigManager and populate UI fields."""
        self.logger.info("Loading settings into dialog.")
        
        # Load available audio devices
        self.devices = self.device_detector.get_input_devices()
        self.audio_device_combo.clear()
        for device in self.devices:
            self.audio_device_combo.addItem(device.name, userData=device)

        # Load and set current values from config
        current_device_name = self.config_manager.get_config_value('audio', 'device')
        if current_device_name:
            index = self.audio_device_combo.findText(current_device_name)
            if index != -1:
                self.audio_device_combo.setCurrentIndex(index)

        capture_mode = self.config_manager.get_config_value('audio', 'capture_mode', 'streaming')
        index = self.capture_mode_combo.findData(capture_mode)
        if index != -1:
            self.capture_mode_combo.setCurrentIndex(index)
        
        buffer_size = self.config_manager.get_config_value('audio', 'buffer_size', 5)
        self.buffer_size_spinbox.setValue(buffer_size)
        
        save_path = self.config_manager.get_config_value('audio', 'save_path', os.path.expanduser('~/Documents'))
        self.file_path_edit.setText(save_path)
        
        # Load model settings
        self.load_model_info()
        
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
        """Open the directory where Whisper models are stored."""
        path = os.path.expanduser("~/.cache/whisper")
        if os.path.exists(path):
            try:
                subprocess.run(['xdg-open', path], check=True)
                self.logger.info(f"Opened model directory: {path}")
            except (FileNotFoundError, subprocess.SubprocessError) as e:
                self.logger.error(f"Failed to open model directory with xdg-open: {e}")
        else:
            self.logger.warning(f"Whisper model directory does not exist: {path}")

    def load_model_info(self):
        """Load and display information about downloaded Whisper models."""
        whisper_cache_path = os.path.expanduser("~/.cache/whisper")
        self.model_path_edit.setText(whisper_cache_path)
        self.model_list_widget.clear()

        if not os.path.exists(whisper_cache_path):
            self.model_list_widget.addItem("Model directory not found.")
            return

        models = []
        for filename in os.listdir(whisper_cache_path):
            if filename.endswith(".pt"):
                file_path = os.path.join(whisper_cache_path, filename)
                size_bytes = os.path.getsize(file_path)
                models.append({'name': filename, 'size': size_bytes})

        if not models:
            self.model_list_widget.addItem("No downloaded models found.")
            return
            
        # Sort models by size (smallest first)
        models.sort(key=lambda m: m['size'])
        
        for model in models:
            size_mb = model['size'] / (1024 * 1024)
            item_text = f"{model['name']} ({size_mb:.1f} MB)"
            self.model_list_widget.addItem(QListWidgetItem(item_text))

    def accept(self):
        self.apply_settings()
        super().accept() 