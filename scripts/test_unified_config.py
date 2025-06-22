#!/usr/bin/env python3
"""
Test script for the unified configuration system.

This script tests the harmonized configuration system that addresses:
- Configuration duplication across multiple files
- Access control (user-editable vs system-only settings)
- Schema-based validation
- Single source of truth for all settings

Run with: python scripts/test_unified_config.py
"""

import sys
import os
import json
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config_manager import ConfigManager
from config.config_schema import SettingAccess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_unified_config_system():
    """Test the unified configuration system."""
    print("🧪 Testing Unified Configuration System")
    print("=" * 50)
    
    # Define paths
    config_dir = os.path.expanduser("~/.config/w4l/")
    backup_dir = os.path.expanduser("~/.config/w4l_backup_test")
    
    # Track if we created a backup
    backup_created = False
    
    # Check if original config exists and create backup if needed
    if os.path.exists(config_dir):
        # Remove any existing backup first
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        # Create backup
        shutil.copytree(config_dir, backup_dir)
        backup_created = True
        print(f"📦 Backed up existing config to: {backup_dir}")
    else:
        print(f"ℹ️  No existing config found, will create new one")
    
    # Test 1: Create unified ConfigManager
    print("\n1️⃣ Testing unified ConfigManager creation...")
    try:
        config_manager = ConfigManager()
        print("✅ Unified ConfigManager created successfully")
    except Exception as e:
        print(f"❌ Failed to create ConfigManager: {e}")
        return False, backup_created
    
    # Test 2: Check single config file
    print("\n2️⃣ Testing single configuration file...")
    config_file = config_manager.config_file
    
    if os.path.exists(config_file):
        print(f"✅ Single config file exists: {config_file}")
        
        # Check file content
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        print(f"   Config sections: {list(config_data.keys())}")
        
        # Verify all sections are present
        expected_sections = ['audio', 'gui', 'transcription', 'system', 'hotkeys', 'audio_devices']
        for section in expected_sections:
            if section in config_data:
                print(f"   ✅ Section '{section}' present")
            else:
                print(f"   ❌ Section '{section}' missing")
                return False, backup_created
    else:
        print(f"❌ Config file missing: {config_file}")
        return False, backup_created
    
    # Test 3: Test access control
    print("\n3️⃣ Testing access control...")
    
    # Test system-only settings (should not be user-editable)
    system_only_tests = [
        ('audio', 'sample_rate', 16000),
        ('audio', 'channels', 1),
        ('audio', 'bit_depth', 16),
    ]
    
    for section, key, value in system_only_tests:
        result = config_manager.set_config_value(section, key, value)
        if not result:
            print(f"   ✅ Correctly prevented setting system-only: {section}.{key}")
        else:
            print(f"   ❌ Incorrectly allowed setting system-only: {section}.{key}")
            return False, backup_created
    
    # Test user-editable settings (should be allowed)
    user_editable_tests = [
        ('audio', 'buffer_size', 10),
        ('audio', 'capture_mode', 'streaming'),
        ('gui', 'theme', 'dark'),
        ('transcription', 'model', 'small'),
    ]
    
    for section, key, value in user_editable_tests:
        result = config_manager.set_config_value(section, key, value)
        if result:
            print(f"   ✅ Correctly allowed setting user-editable: {section}.{key}")
        else:
            print(f"   ❌ Incorrectly prevented setting user-editable: {section}.{key}")
            return False, backup_created
    
    # Test 4: Test schema validation
    print("\n4️⃣ Testing schema validation...")
    
    # Test invalid values
    invalid_tests = [
        ('audio', 'buffer_size', 50),  # Above max (30)
        ('audio', 'buffer_size', 0),   # Below min (1)
        ('audio', 'capture_mode', 'invalid_mode'),  # Not in allowed values
        ('gui', 'theme', 'invalid_theme'),  # Not in allowed values
    ]
    
    for section, key, value in invalid_tests:
        result = config_manager.set_config_value(section, key, value)
        if not result:
            print(f"   ✅ Correctly rejected invalid value: {section}.{key} = {value}")
        else:
            print(f"   ❌ Incorrectly accepted invalid value: {section}.{key} = {value}")
            return False, backup_created
    
    # Test 5: Test user-editable settings retrieval
    print("\n5️⃣ Testing user-editable settings retrieval...")
    
    editable_settings = config_manager.get_user_editable_settings()
    print(f"   Found {len(editable_settings)} sections with user-editable settings:")
    
    for section, settings in editable_settings.items():
        print(f"   📁 {section}: {len(settings)} editable settings")
        for key, data in settings.items():
            definition = data['definition']
            print(f"      - {key}: {data['value']} ({definition.description})")
    
    # Test 6: Test advanced settings
    print("\n6️⃣ Testing advanced settings...")
    
    advanced_settings = config_manager.get_advanced_settings()
    print(f"   Found {len(advanced_settings)} sections with advanced settings:")
    
    for section, settings in advanced_settings.items():
        print(f"   📁 {section}: {len(settings)} advanced settings")
        for key, data in settings.items():
            definition = data['definition']
            print(f"      - {key}: {data['value']} ({definition.description})")
    
    # Test 7: Test category-based settings
    print("\n7️⃣ Testing category-based settings...")
    
    audio_settings = config_manager.get_settings_by_category("audio")
    print(f"   Audio settings: {len(audio_settings.get('audio', {}))} total settings")
    
    # Count system-only vs user-editable in audio
    audio_section = audio_settings.get('audio', {})
    system_only_count = 0
    user_editable_count = 0
    
    for key, data in audio_section.items():
        definition = data['definition']
        if definition.access == SettingAccess.SYSTEM_ONLY:
            system_only_count += 1
        elif definition.access == SettingAccess.USER_EDITABLE:
            user_editable_count += 1
    
    print(f"      - System-only: {system_only_count}")
    print(f"      - User-editable: {user_editable_count}")
    
    # Test 8: Test reset functionality
    print("\n8️⃣ Testing reset functionality...")
    
    # Change a user-editable setting
    config_manager.set_config_value('audio', 'buffer_size', 15)
    current_value = config_manager.get_config_value('audio', 'buffer_size')
    print(f"   Set buffer_size to: {current_value}")
    
    # Reset audio category
    config_manager.reset_to_defaults('audio')
    reset_value = config_manager.get_config_value('audio', 'buffer_size')
    print(f"   After reset, buffer_size is: {reset_value}")
    
    if reset_value == 5:  # Default value
        print("   ✅ Reset functionality works")
    else:
        print(f"   ❌ Reset failed, expected 5, got {reset_value}")
        return False, backup_created
    
    # Test 9: Show final unified config structure
    print("\n9️⃣ Final unified configuration structure:")
    print(f"Config file: {config_file}")
    
    with open(config_file, 'r') as f:
        final_config = json.load(f)
    
    for section, settings in final_config.items():
        print(f"   📁 {section}:")
        for key, value in settings.items():
            setting_def = config_manager.schema.get_setting(f"{section}.{key}")
            if setting_def:
                access = setting_def.access.value
                print(f"      - {key}: {value} ({access})")
            else:
                print(f"      - {key}: {value} (unknown)")
    
    print("\n✅ Unified configuration system successful!")
    print("   - Single config file eliminates duplication")
    print("   - Access control prevents system-only changes")
    print("   - Schema validation ensures data integrity")
    print("   - User-editable settings are clearly defined")
    print("   - Advanced settings are separated")
    
    # Return backup status for cleanup
    return True, backup_created

def cleanup_test(backup_created):
    """Clean up test artifacts.
    
    Args:
        backup_created (bool): Whether a backup was created during the test
    """
    config_dir = os.path.expanduser("~/.config/w4l/")
    backup_dir = os.path.expanduser("~/.config/w4l_backup_test")
    
    if backup_created and os.path.exists(backup_dir):
        try:
            # Restore original config
            if os.path.exists(config_dir):
                shutil.rmtree(config_dir)
            shutil.move(backup_dir, config_dir)
            print(f"🔄 Restored original configuration")
        except Exception as e:
            print(f"⚠️  Warning: Could not restore original configuration: {e}")
            print(f"   Original config may have been modified by the test")
    elif backup_created:
        print(f"⚠️  Warning: Backup was created but backup directory is missing")
        print(f"   Original config may have been modified by the test")
    else:
        print(f"ℹ️  No backup was created - keeping test configuration")

if __name__ == "__main__":
    backup_created = False
    try:
        success, backup_created = test_unified_config_system()
        if success:
            print("\n🎉 All tests passed! Unified configuration system is working.")
        else:
            print("\n💥 Some tests failed. Please check the implementation.")
            sys.exit(1)
    finally:
        # Only ask about restoration if we actually created a backup
        if backup_created:
            response = input("\n🔄 Restore original configuration? (y/N): ")
            if response.lower() in ['y', 'yes']:
                cleanup_test(backup_created)
            else:
                print("💾 Keeping test configuration")
        else:
            print("\n💾 Keeping test configuration (no original config to restore)") 