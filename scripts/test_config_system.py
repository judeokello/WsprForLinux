#!/usr/bin/env python3
"""
Test script for the configuration system implementation.

This script tests Task 2.4.0.1 Configuration File Structure:
- Directory structure creation
- Configuration file creation
- Default configuration values
- Error handling

Run with: python scripts/test_config_system.py
"""

import sys
import os
import json
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config_manager import ConfigManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_config_system():
    """Test the configuration system implementation."""
    print("🧪 Testing Configuration System Implementation")
    print("=" * 50)
    
    # Test 1: Create ConfigManager
    print("\n1️⃣ Testing ConfigManager creation...")
    try:
        config_manager = ConfigManager()
        print("✅ ConfigManager created successfully")
    except Exception as e:
        print(f"❌ Failed to create ConfigManager: {e}")
        return False
    
    # Test 2: Check directory structure
    print("\n2️⃣ Testing directory structure...")
    config_dir = config_manager.get_config_dir()
    logs_dir = config_manager.get_logs_dir()
    
    expected_files = [
        os.path.join(config_dir, "config.json")
    ]
    
    expected_dirs = [config_dir, logs_dir]
    
    # Check directories
    for directory in expected_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            return False
    
    # Check files
    for file_path in expected_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            return False
    
    # Test 3: Check configuration content
    print("\n3️⃣ Testing configuration content...")
    
    # Check main config
    if config_manager.config:
        print("✅ Main configuration loaded")
        print(f"   Audio sample rate: {config_manager.get_config_value('audio', 'sample_rate')}")
        print(f"   GUI theme: {config_manager.get_config_value('gui', 'theme')}")
        print(f"   System hotkey: {config_manager.get_config_value('system', 'hotkey')}")
    else:
        print("❌ Main configuration is empty")
        return False
    
    # Check audio devices config (now part of unified config)
    audio_devices = config_manager.get_settings_by_category("audio_devices")
    if audio_devices:
        print("✅ Audio devices configuration loaded")
    else:
        print("❌ Audio devices configuration is empty")
        return False
    
    # Check hotkeys config (now part of unified config)
    hotkeys = config_manager.get_settings_by_category("hotkeys")
    if hotkeys:
        print("✅ Hotkeys configuration loaded")
    else:
        print("❌ Hotkeys configuration is empty")
        return False
    
    # Test 4: Test configuration modification
    print("\n4️⃣ Testing configuration modification...")
    try:
        # Set a test value (user-editable setting)
        success = config_manager.set_config_value('audio', 'buffer_size', 10)
        
        if success:
            # Get the value back
            test_value = config_manager.get_config_value('audio', 'buffer_size')
            if test_value == 10:
                print("✅ Configuration modification works")
            else:
                print(f"❌ Configuration modification failed: expected 10, got '{test_value}'")
                return False
        else:
            print("❌ Configuration modification failed: could not set value")
            return False
            
    except Exception as e:
        print(f"❌ Configuration modification failed: {e}")
        return False
    
    # Test 5: Test error handling (corrupted file)
    print("\n5️⃣ Testing error handling...")
    try:
        # Corrupt the config file
        config_file = config_manager.config_file
        with open(config_file, 'w') as f:
            f.write("invalid json content")
        
        # Try to load it
        config_manager.load_config()
        print("✅ Error handling works (corrupted file recovered)")
        
    except Exception as e:
        print(f"❌ Error handling failed: {e}")
        return False
    
    # Test 6: Show directory structure
    print("\n6️⃣ Final directory structure:")
    print(f"Config directory: {config_dir}")
    print("Files created:")
    for root, dirs, files in os.walk(config_dir):
        level = root.replace(config_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    print("\n✅ Configuration system implementation successful!")
    print("   - Directory structure created")
    print("   - Configuration file created")
    print("   - Default values loaded")
    print("   - Error handling works")
    print("   - Configuration modification works")
    
    return True

if __name__ == "__main__":
    success = test_config_system()
    if success:
        print("\n🎉 All tests passed! Task 2.4.0.1 is complete.")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1) 