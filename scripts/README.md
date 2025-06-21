# Scripts Directory

This directory contains utility scripts for debugging, testing, and development of W4L.

## Available Scripts

### `debug_audio_devices.py`
**Purpose**: Debug and understand sounddevice device information
**Usage**: `python scripts/debug_audio_devices.py`
**Description**: 
- Lists all available audio devices on the system
- Shows raw device information from sounddevice
- Displays device properties and capabilities
- Useful for troubleshooting audio device issues

## Running Scripts

All scripts in this directory can be run directly from the project root:

```bash
# Debug audio devices
python scripts/debug_audio_devices.py

# Run tests (from project root)
PYTHONPATH=src pytest tests/test_audio/
```

## Notes

- Scripts are designed to be run from the project root directory
- Some scripts may require specific environment setup (e.g., PYTHONPATH=src)
- Debug scripts are for development/troubleshooting and not part of the main application 