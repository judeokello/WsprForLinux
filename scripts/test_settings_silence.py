#!/usr/bin/env python3
"""
Test script for the silence detection settings tab.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from config.config_manager import ConfigManager
from gui.settings_dialog import SettingsDialog

def test_silence_settings():
    """Test the silence detection settings tab."""
    app = QApplication(sys.argv)
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Create settings dialog
    dialog = SettingsDialog(config_manager)
    
    print("🎛️  Testing Silence Detection Settings Tab")
    print("=" * 50)
    print("The settings dialog should now open with 3 tabs:")
    print("1. Audio - Basic audio settings")
    print("2. Models - Whisper model management")
    print("3. Silence Detection - NEW! Background noise handling")
    print()
    print("💡 In the Silence Detection tab, you'll see:")
    print("• Basic Settings: Threshold, Duration, Strategy dropdown")
    print("• Adaptive Settings: Noise learning, margins, adaptation")
    print("• Advanced Settings: Spectral analysis, min speech duration")
    print("• Info section explaining how it works")
    print()
    print("🔧 Try changing settings and click 'Apply' to save them.")
    print("📋 The strategy dropdown shows all detection methods.")
    print("🎧 Adaptive settings help with laptop fan noise.")
    
    # Show the dialog
    result = dialog.exec()
    
    if result == SettingsDialog.DialogCode.Accepted:
        print("\n✅ Settings saved successfully!")
    else:
        print("\n❌ Settings dialog was cancelled.")
    
    app.quit()

if __name__ == "__main__":
    test_silence_settings() 