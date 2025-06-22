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
        
        tab_widget.addTab(audio_tab, "Audio")
        tab_widget.addTab(model_tab, "Models")
        
        # --- Populate Audio Tab ---
        self.setup_audio_tab(audio_tab)
        
        # --- Populate Model Tab ---
        self.setup_model_tab(model_tab)

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
        self.capture_mode_combo.addItems(["Streaming", "File-based"])
        self.buffer_size_spinbox = QSpinBox()
        self.buffer_size_spinbox.setRange(1, 30)
        self.buffer_size_spinbox.setSuffix(" seconds")
        
        # File path setting (conditionally visible)
        self.file_path_widget = QWidget()
        file_path_layout = QHBoxLayout(self.file_path_widget)
        file_path_layout.setContentsMargins(0, 0, 0, 0)
        self.file_path_edit = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        file_path_layout.addWidget(self.file_path_edit)
        file_path_layout.addWidget(self.browse_button)
        
        capture_layout.addRow("Capture Mode:", self.capture_mode_combo)
        capture_layout.addRow("Audio Buffer Size:", self.buffer_size_spinbox)
        capture_layout.addRow("Save Audio To:", self.file_path_widget)
        
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

        capture_mode = self.config_manager.get_config_value('audio', 'capture_mode', 'Streaming')
        self.capture_mode_combo.setCurrentText(capture_mode)
        
        buffer_size = self.config_manager.get_config_value('audio', 'buffer_size', 5)
        self.buffer_size_spinbox.setValue(buffer_size)
        
        save_path = self.config_manager.get_config_value('audio', 'save_path', os.path.join(self.config_manager.get_config_dir(), 'recordings'))
        self.file_path_edit.setText(save_path)
        
        # Load model settings
        self.load_model_info()
        
    def apply_settings(self):
        """Save the current settings to the ConfigManager."""
        self.logger.info("Applying settings...")
        
        selected_device_index = self.audio_device_combo.currentIndex()
        if selected_device_index != -1:
            selected_device = self.audio_device_combo.itemData(selected_device_index)
            self.config_manager.set_config_value('audio', 'device', selected_device.name)
            self.config_manager.set_config_value('audio', 'device_id', selected_device.device_id)

        self.config_manager.set_config_value('audio', 'capture_mode', self.capture_mode_combo.currentText())
        self.config_manager.set_config_value('audio', 'buffer_size', self.buffer_size_spinbox.value())
        self.config_manager.set_config_value('audio', 'save_path', self.file_path_edit.text())
        
        self.logger.info("Settings applied and saved.")
        
    def update_ui_visibility(self):
        """Show or hide settings based on other selections."""
        is_file_based = self.capture_mode_combo.currentText() == "File-based"
        self.file_path_widget.setVisible(is_file_based)

    def browse_for_directory(self):
        """Open a dialog to select a directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
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

        found_models = False
        for filename in os.listdir(whisper_cache_path):
            if filename.endswith(".pt"):
                found_models = True
                file_path = os.path.join(whisper_cache_path, filename)
                size_bytes = os.path.getsize(file_path)
                size_mb = size_bytes / (1024 * 1024)
                
                item_text = f"{filename} ({size_mb:.1f} MB)"
                self.model_list_widget.addItem(QListWidgetItem(item_text))
        
        if not found_models:
            self.model_list_widget.addItem("No downloaded models found.")

    def accept(self):
        self.apply_settings()
        super().accept() 