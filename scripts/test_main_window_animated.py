#!/usr/bin/env python3
"""
Test script for main window with animated waveform display.
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
from src.gui.main_window import W4LMainWindow

class AnimatedMainWindowTest(W4LMainWindow):
    def __init__(self):
        super().__init__()
        
        # Add a test button to the layout
        self.test_button = QPushButton("Start Test Animation")
        self.test_button.clicked.connect(self.toggle_animation)
        
        # Get the central widget's layout and add the button
        central_widget = self.centralWidget()
        if central_widget:
            layout = central_widget.layout()
            if layout:
                layout.addWidget(self.test_button)
        
        # Animation state
        self.is_animating = False
        self.test_data = np.array([])
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        
        # Update status
        self.status_label.setText("Click 'Start Test Animation' to see waveform")
        
    def toggle_animation(self):
        """Toggle the test animation on/off."""
        if not self.is_animating:
            self.start_animation()
        else:
            self.stop_animation()
    
    def start_animation(self):
        """Start the test animation."""
        self.is_animating = True
        self.test_button.setText("Stop Animation")
        
        # Generate initial test data
        sample_rate = 16000
        duration = 2.0
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Create a sine wave
        frequency = 440  # A4 note
        self.test_data = 0.5 * np.sin(2 * np.pi * frequency * t)
        
        # Start the waveform widget in recording mode
        self.waveform_widget.start_recording()
        
        # Start timer for continuous updates
        self.timer.start(100)  # Update every 100ms
        
        self.status_label.setText("Animation running - Watch the waveform!")
        
    def stop_animation(self):
        """Stop the test animation."""
        self.is_animating = False
        self.test_button.setText("Start Test Animation")
        
        # Stop the timer
        self.timer.stop()
        
        # Stop recording mode
        self.waveform_widget.stop_recording()
        
        self.status_label.setText("Animation stopped")
        
    def update_animation(self):
        """Update the animation with scrolling data."""
        if len(self.test_data) > 0:
            # Shift data to create scrolling effect
            self.test_data = np.roll(self.test_data, -100)
            
            # Add some variation to make it more interesting
            variation = 0.1 * np.sin(time.time() * 3)
            self.test_data += variation * np.random.randn(len(self.test_data))
            
            # Update the waveform widget
            self.waveform_widget.update_audio_data(self.test_data)

def main():
    """
    Test the main window with animated waveform display.
    """
    print("--- Starting WsprForLinux Animated GUI Test ---")
    
    app = QApplication(sys.argv)
    
    print("1. Creating animated main window...")
    try:
        main_win = AnimatedMainWindowTest()
        print("   ✅ Animated main window created successfully.")
    except Exception as e:
        print(f"   ❌ Error creating animated main window: {e}")
        return

    print("2. Showing main window...")
    main_win.show()
    print("   ✅ Main window shown.")
    print("   📋 Instructions:")
    print("      - You should see a waveform display area")
    print("      - Click 'Start Test Animation' to see the waveform in action")
    print("      - The waveform should scroll and animate")
    print("      - Click 'Stop Animation' to return to flatline")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 