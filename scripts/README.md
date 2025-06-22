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

# Test Scripts for W4L

This directory contains various test scripts for different components of the W4L application.

## 🔧 Configuration System Tests

### **Primary Test (Recommended)**
- **`test_unified_config.py`** - Comprehensive test for the unified configuration system
  - Tests access control (user-editable vs system-only settings)
  - Tests schema validation
  - Tests error handling and recovery
  - Tests settings retrieval by category
  - **Use this for thorough testing of the configuration system**

### **Legacy Test (Updated)**
- **`test_config_system.py`** - Updated test for Task 2.4.0.1 completion
  - Tests basic configuration file structure
  - Tests directory creation and permissions
  - Tests error handling for corrupted files
  - **Use this to verify Task 2.4.0.1 is complete**

### **Demo Script**
- **`show_unified_config.py`** - Visual demonstration of the unified configuration
  - Shows the complete configuration structure
  - Displays user-editable vs system-only settings
  - Provides a summary of all settings
  - **Use this to understand the configuration structure**

## 🎯 **Which Test to Use When**

### **For Development:**
```bash
# Test the unified configuration system thoroughly
python scripts/test_unified_config.py

# Show the configuration structure
python scripts/show_unified_config.py
```

### **For Task Verification:**
```bash
# Verify Task 2.4.0.1 is complete
python scripts/test_config_system.py
```

### **For Understanding:**
```bash
# See the complete configuration structure
python scripts/show_unified_config.py
```

## 📋 **Test File Purposes**

| File | Purpose | When to Use |
|------|---------|-------------|
| `test_unified_config.py` | Comprehensive testing of unified config system | Development, thorough testing |
| `test_config_system.py` | Basic configuration structure verification | Task completion verification |
| `show_unified_config.py` | Configuration structure demonstration | Understanding, documentation |

## 🚀 **Quick Start**

1. **Test the unified system:**
   ```bash
   python scripts/test_unified_config.py
   ```

2. **View the configuration structure:**
   ```bash
   python scripts/show_unified_config.py
   ```

3. **Verify task completion:**
   ```bash
   python scripts/test_config_system.py
   ```

## 📝 **Notes**

- All tests are compatible with the unified configuration system
- The old multi-file configuration approach has been replaced
- All configuration is now in a single `~/.config/w4l/config.json` file
- Access control prevents users from modifying system-only settings 