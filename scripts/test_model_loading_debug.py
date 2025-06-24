#!/usr/bin/env python3
"""
Test script to debug model loading issues with comprehensive logging.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcription.model_manager import ModelManager
from transcription.model_metadata_manager import ModelMetadataManager
from config.config_manager import ConfigManager

def setup_logging():
    """Set up comprehensive logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/w4l_model_debug.log')
        ]
    )
    
    # Set specific loggers to DEBUG level
    loggers = [
        'transcription.model_manager',
        'transcription.model_metadata_manager',
        'config.config_manager',
        'gui.main_window'
    ]
    
    for logger_name in loggers:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)

def test_model_manager():
    """Test the model manager with debug logging."""
    print("=== Testing Model Manager ===")
    
    # Initialize managers
    config_manager = ConfigManager()
    metadata_manager = ModelMetadataManager()
    model_manager = ModelManager(metadata_manager=metadata_manager)
    
    print(f"Models path: {model_manager.models_path}")
    print(f"Metadata path: {metadata_manager.metadata_path}")
    
    # List all models
    print("\n=== Listing All Models ===")
    all_models = model_manager.list_models()
    
    for model in all_models:
        print(f"Model: {model['name']}")
        print(f"  - Downloaded: {model.get('is_downloaded')}")
        print(f"  - Verified: {model.get('is_verified')}")
        print(f"  - Status: {model.get('status')}")
        print(f"  - Size: {model.get('size_bytes', 'Unknown')}")
        print(f"  - Filepath: {model['filepath']}")
        print(f"  - File exists: {model['filepath'].exists()}")
        print()
    
    # Check verified models
    verified_models = [m for m in all_models if m.get('is_verified')]
    print(f"Verified models: {[m['name'] for m in verified_models]}")
    
    # Check current config
    current_model = config_manager.get_config_value('transcription', 'model', 'base')
    print(f"Current model in config: {current_model}")
    
    # Test model verification for specific models
    print("\n=== Testing Model Verification ===")
    for model_name in ['tiny', 'base', 'small']:
        try:
            is_verified = model_manager.verify_model(model_name)
            print(f"Model '{model_name}' verification: {is_verified}")
        except Exception as e:
            print(f"Error verifying model '{model_name}': {e}")

def test_metadata_manager():
    """Test the metadata manager specifically."""
    print("\n=== Testing Metadata Manager ===")
    
    metadata_manager = ModelMetadataManager()
    print(f"Metadata path: {metadata_manager.metadata_path}")
    print(f"Metadata exists: {metadata_manager.metadata_path.exists()}")
    
    if metadata_manager.metadata_path.exists():
        print("Metadata file contents:")
        try:
            with open(metadata_manager.metadata_path, 'r') as f:
                import json
                data = json.load(f)
                print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error reading metadata: {e}")
    else:
        print("Metadata file does not exist - will be created on first use")

def main():
    """Main test function."""
    setup_logging()
    
    print("W4L Model Loading Debug Test")
    print("=" * 50)
    
    test_metadata_manager()
    test_model_manager()
    
    print("\nDebug log written to: /tmp/w4l_model_debug.log")

if __name__ == "__main__":
    main() 