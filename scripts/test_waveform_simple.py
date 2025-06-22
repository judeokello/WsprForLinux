#!/usr/bin/env python3
"""
Simple test for waveform widget with test audio data.
"""

import sys
import os
import numpy as np
import time

# Add project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer
from src.gui.waveform_widget import WaveformWidget

class SimpleWaveformTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Waveform Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Waveform widget
        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform)
        
        # Test button
        self.test_button = QPushButton("Generate Test Audio")
        self.test_button.clicked.connect(self.generate_test_audio)
        layout.addWidget(self.test_button)
        
        # Status label
        self.status_label = QLabel("Click button to generate test audio")
        layout.addWidget(self.status_label)
        
        # Timer for continuous updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_waveform)
        self.test_data = np.array([])
        
    def generate_test_audio(self):
        """Generate some test audio data."""
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        samples = int(sample_rate * duration)
        
        # Create time array
        t = np.linspace(0, duration, samples)
        
        # Generate a sine wave with some variation
        frequency = 440  # A4 note
        audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)
        
        # Add some noise
        noise = 0.1 * np.random.randn(samples)
        self.test_data = audio_data + noise
        
        # Update waveform
        self.waveform.update_audio_data(self.test_data)
        self.status_label.setText(f"Generated {len(self.test_data)} samples of test audio")
        
        # Start continuous updates
        self.timer.start(100)  # Update every 100ms
        
    def update_waveform(self):
        """Update waveform with scrolling data."""
        if len(self.test_data) > 0:
            # Shift data to create scrolling effect
            self.test_data = np.roll(self.test_data, -100)
            self.waveform.update_audio_data(self.test_data)

def main():
    app = QApplication(sys.argv)
    window = SimpleWaveformTest()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 