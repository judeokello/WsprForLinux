#!/usr/bin/env python3
"""
Show the unified configuration structure.

This script demonstrates the harmonized configuration system.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.config_manager import ConfigManager
import json

def main():
    """Show the unified configuration structure."""
    print("🔧 Unified Configuration System")
    print("=" * 40)
    
    # Create config manager
    config_manager = ConfigManager()
    
    # Show the unified config file
    config_file = config_manager.config_file
    print(f"\n📁 Single config file: {config_file}")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    print("\n📋 Configuration Structure:")
    for section, settings in config.items():
        print(f"\n   📁 {section}:")
        for key, value in settings.items():
            # Get setting definition
            setting_def = config_manager.schema.get_setting(f"{section}.{key}")
            if setting_def:
                access = setting_def.access.value
                description = setting_def.description
                print(f"      - {key}: {value} ({access})")
                print(f"        {description}")
            else:
                print(f"      - {key}: {value}")
    
    # Show user-editable settings
    print(f"\n🎛️  User-Editable Settings ({len(config_manager.get_user_editable_settings())} sections):")
    for section, settings in config_manager.get_user_editable_settings().items():
        print(f"   📁 {section}:")
        for key, data in settings.items():
            definition = data['definition']
            print(f"      - {key}: {data['value']}")
            print(f"        {definition.description}")
    
    # Show system-only settings
    print(f"\n🔒 System-Only Settings:")
    system_only_count = 0
    for section, settings in config.items():
        for key in settings.keys():
            if config_manager.schema.is_system_only(f"{section}.{key}"):
                system_only_count += 1
                print(f"   - {section}.{key}: {settings[key]}")
    
    print(f"\n📊 Summary:")
    print(f"   - Total settings: {sum(len(settings) for settings in config.values())}")
    print(f"   - User-editable: {sum(len(settings) for settings in config_manager.get_user_editable_settings().values())}")
    print(f"   - System-only: {system_only_count}")
    print(f"   - Advanced: {sum(len(settings) for settings in config_manager.get_advanced_settings().values())}")

if __name__ == "__main__":
    main() 