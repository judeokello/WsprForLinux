import sys
import os
from PyQt6.QtWidgets import QApplication

# Add project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, 'src'))

from gui.main_window import W4LMainWindow
from config import ConfigManager

def main():
    """
    Initializes and runs the WsprForLinux application.
    """
    print("--- Starting WsprForLinux GUI Test ---")
    
    app = QApplication(sys.argv)
    
    print("1. Creating ConfigManager instance...")
    try:
        config_manager = ConfigManager()
        print("   ✅ ConfigManager created successfully.")
    except Exception as e:
        print(f"   ❌ Error creating ConfigManager: {e}")
        return
    
    print("2. Creating W4LMainWindow instance...")
    try:
        main_win = W4LMainWindow(config_manager)
        print("   ✅ W4LMainWindow created successfully.")
    except Exception as e:
        print(f"   ❌ Error creating W4LMainWindow: {e}")
        return

    print("3. Showing main window...")
    main_win.show()
    print("   ✅ Main window shown. Please check the display.")
    print("      - The window should have the title 'W4L - Whisper for Linux'.")
    print("      - It should contain a waveform display area.")
    print("      - A status label 'Ready' should be at the bottom.")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 