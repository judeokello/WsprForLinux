#!/usr/bin/env python3
"""
Script to populate the model metadata file with information about existing downloaded models.
This will help the application recognize and properly verify the models.
"""

import sys
import os
import hashlib
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcription.model_manager import ModelManager
from transcription.model_metadata_manager import ModelMetadataManager
from transcription.model_constants import OFFICIAL_WHISPER_MODELS

def populate_metadata():
    """Populate the metadata file with information about existing models."""
    print("Populating model metadata...")
    
    # Initialize managers
    metadata_manager = ModelMetadataManager()
    model_manager = ModelManager(metadata_manager=metadata_manager)
    
    print(f"Models path: {model_manager.models_path}")
    print(f"Metadata path: {metadata_manager.metadata_path}")
    
    # Check each official model
    for model_name, url in OFFICIAL_WHISPER_MODELS.items():
        checksum = url.split("/")[-2]
        filepath = model_manager.models_path / f"{model_name}.pt"
        
        print(f"\nChecking model: {model_name}")
        print(f"  URL: {url}")
        print(f"  Expected checksum: {checksum}")
        print(f"  File path: {filepath}")
        print(f"  File exists: {filepath.exists()}")
        
        if filepath.exists():
            try:
                # Calculate actual file size and checksum
                file_size = filepath.stat().st_size
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                
                print(f"  Actual file size: {file_size}")
                print(f"  Actual checksum: {file_hash}")
                print(f"  Checksum matches: {file_hash == checksum}")
                
                # Update metadata
                status = "downloaded" if file_hash == checksum else "corrupted"
                metadata_manager.update_model_info(model_name, checksum, file_size, status)
                print(f"  Status: {status}")
                
            except Exception as e:
                print(f"  Error processing file: {e}")
                # Still update metadata with what we know
                metadata_manager.update_model_info(model_name, checksum, 0, "error")
        else:
            print(f"  File not found - not updating metadata")
    
    print(f"\nMetadata saved to: {metadata_manager.metadata_path}")
    
    # Verify the metadata was saved
    if metadata_manager.metadata_path.exists():
        print("Metadata file created successfully!")
    else:
        print("Warning: Metadata file was not created!")

def main():
    """Main function."""
    print("W4L Model Metadata Population Tool")
    print("=" * 50)
    
    populate_metadata()
    
    print("\nDone!")

if __name__ == "__main__":
    main() 