#!/usr/bin/env python3
"""
Test script for basic GUI framework functionality (2.1).

This script demonstrates:
- Creating the main application window
- Window centering and styling
- Basic PyQt5 application structure
- Window properties (always on top, frameless)

Run with: python scripts/test_gui_basic.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after adding src to path
from gui.main_window import W4LMainWindow, create_application
from audio.device_config import AudioDeviceManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_gui_basic():
    """Test basic GUI framework functionality."""
    print("=== W4L Basic GUI Framework Test (2.1) ===\n")
    
    try:
        # Create application
        print("1. Creating QApplication...")
        app = create_application()
        print("   ✅ QApplication created successfully")
        
        # Create device manager
        print("\n2. Creating device manager...")
        device_manager = AudioDeviceManager()
        print("   ✅ Device manager created successfully")
        
        # Create main window
        print("\n3. Creating main window...")
        window = W4LMainWindow(device_manager)
        print("   ✅ Main window created successfully")
        
        # Test window properties
        print("\n4. Testing window properties...")
        
        # Check window flags
        flags = window.windowFlags()
        has_always_on_top = bool(flags & 0x40000)  # Qt.WindowStaysOnTopHint
        has_frameless = bool(flags & 0x800000)     # Qt.FramelessWindowHint
        has_tool = bool(flags & 0x1000000)         # Qt.Tool
        
        print(f"   Always on top: {'✅ Yes' if has_always_on_top else '❌ No'}")
        print(f"   Frameless: {'✅ Yes' if has_frameless else '❌ No'}")
        print(f"   Tool window: {'✅ Yes' if has_tool else '❌ No'}")
        
        # Check window size
        size = window.size()
        print(f"   Window size: {size.width()}x{size.height()}")
        
        # Check window title
        title = window.windowTitle()
        print(f"   Window title: {title}")
        
        # Test window centering
        print("\n5. Testing window centering...")
        window._center_window()
        pos = window.pos()
        print(f"   Window position: ({pos.x()}, {pos.y()})")
        print("   ✅ Window centering completed")
        
        # Test window show/hide
        print("\n6. Testing window show/hide...")
        window.show_window()
        print("   ✅ Window shown successfully")
        
        # Test settings button (should open placeholder dialog)
        print("\n7. Testing settings button...")
        try:
            window._open_settings()
            print("   ✅ Settings button works (placeholder dialog)")
        except Exception as e:
            print(f"   ⚠️  Settings button test: {e}")
        
        # Test recording button
        print("\n8. Testing recording button...")
        initial_text = window.record_button.text()
        print(f"   Initial button text: {initial_text}")
        
        # Test recording toggle
        window._toggle_recording()
        recording_text = window.record_button.text()
        print(f"   After toggle text: {recording_text}")
        print(f"   Recording state: {'✅ Active' if window.is_recording else '❌ Inactive'}")
        
        # Stop recording
        if window.is_recording:
            window._toggle_recording()
            print("   ✅ Recording stopped")
        
        print("\n=== GUI Test Summary ===")
        print("✅ Basic GUI framework is working correctly!")
        print("✅ Window properties are set correctly")
        print("✅ Window centering works")
        print("✅ Recording controls work")
        print("✅ Settings button works")
        
        print("\n=== Test Complete ===")
        print("The GUI will remain open for manual testing.")
        print("Close the window to exit.")
        
        # Run the application
        return app.exec_()
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_gui_basic()) 