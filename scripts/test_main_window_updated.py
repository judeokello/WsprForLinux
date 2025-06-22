#!/usr/bin/env python3
"""
Test script for the updated main window with sophisticated design.

This script tests the main window that now matches the design from test_gui_simple.py
but with the actual WaveformWidget integrated.

Run with: python scripts/test_main_window_updated.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from gui.main_window import W4LMainWindow
from config import ConfigManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_main_window_updated():
    """Test the updated main window with sophisticated design."""
    app = QApplication(sys.argv)
    
    # Create ConfigManager instance
    config_manager = ConfigManager()
    
    # Create and show the main window
    main_win = W4LMainWindow(config_manager)
    main_win.show()
    
    print("✅ Updated main window displayed successfully!")
    print("   - Title bar with W4L branding and settings button")
    print("   - Content area with waveform widget")
    print("   - Status bar with recording and close buttons")
    print("   - Always on top and frameless window")
    print("   - Professional styling with rounded corners")
    print("   - Configuration manager integrated")
    print("\n💡 Click the red × button to close the application properly")
    
    # Run the application
    exit_code = app.exec()
    print("✅ Application terminated successfully")
    return exit_code

if __name__ == "__main__":
    test_main_window_updated() 