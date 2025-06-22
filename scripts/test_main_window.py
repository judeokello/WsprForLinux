import sys
import os
from PyQt6.QtWidgets import QApplication

# Add project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.gui.main_window import W4LMainWindow

def main():
    """
    Initializes and runs the WsprForLinux application.
    """
    print("--- Starting WsprForLinux GUI Test ---")
    
    app = QApplication(sys.argv)
    
    print("1. Creating W4LMainWindow instance...")
    try:
        main_win = W4LMainWindow()
        print("   ✅ W4LMainWindow created successfully.")
    except Exception as e:
        print(f"   ❌ Error creating W4LMainWindow: {e}")
        return

    print("2. Showing main window...")
    main_win.show()
    print("   ✅ Main window shown. Please check the display.")
    print("      - The window should have the title 'WsprForLinux'.")
    print("      - It should contain a waveform display area.")
    print("      - A status label 'Ready' should be at the bottom.")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 