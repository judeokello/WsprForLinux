# Linux-Specific Assumptions & Dependencies

This document outlines all Linux-specific assumptions, dependencies, and implementation details in W4L. This information is crucial for future cross-platform development.

## 🐧 Current Linux-Only Implementation

### **1. System Tray Implementation**
**Component**: `src/main.py` - `W4LApplication._setup_system_tray()`

**Linux-Specific Features**:
- Uses `QSystemTrayIcon` with D-Bus backend
- Relies on system tray protocols (KDE/GNOME/XFCE)
- D-Bus error handling for service availability

**Cross-Platform Considerations**:
```python
# Windows: Different system tray API
# macOS: Menu bar instead of system tray
# Linux: D-Bus system tray protocols
```

**Dependencies**:
- PyQt6.QtWidgets.QSystemTrayIcon
- D-Bus system tray support
- Desktop environment compatibility

---

### **2. Global Hotkey Registration**
**Component**: Planned implementation in `src/main.py`

**Linux-Specific Features**:
- Uses `keyboard` library or `pynput` for global hotkeys
- Requires X11/Wayland display server
- May need root permissions for some hotkey combinations

**Cross-Platform Considerations**:
```python
# Windows: Different hotkey registration APIs
# macOS: Different permission requirements
# Linux: X11/Wayland specific implementation
```

**Dependencies**:
- `keyboard` library (Linux-specific)
- `pynput` library (cross-platform alternative)
- X11/Wayland display server

---

### **3. Audio System**
**Component**: `src/audio/` modules

**Linux-Specific Features**:
- Uses ALSA/PulseAudio backend via `sounddevice`
- Audio device detection via ALSA/PulseAudio APIs
- Linux-specific audio permissions and device naming

**Cross-Platform Considerations**:
```python
# Windows: DirectSound/WASAPI backend
# macOS: Core Audio backend
# Linux: ALSA/PulseAudio backend
```

**Dependencies**:
- `sounddevice` library
- ALSA or PulseAudio system
- Linux audio device permissions

---

### **4. Window Management**
**Component**: `src/gui/main_window.py`

**Linux-Specific Features**:
- X11/Wayland window management
- Linux-specific window flags and properties
- Desktop environment window behavior

**Cross-Platform Considerations**:
```python
# Windows: Win32 API window management
# macOS: Cocoa/AppKit window management
# Linux: X11/Wayland window management
```

**Dependencies**:
- PyQt6 window management
- X11/Wayland display server
- Desktop environment compatibility

---

### **5. Clipboard Operations**
**Component**: `src/gui/main_window.py` - `_copy_text_to_clipboard()`

**Linux-Specific Features**:
- X11 clipboard via PyQt6
- Linux clipboard selection protocols
- D-Bus clipboard integration

**Cross-Platform Considerations**:
```python
# Windows: Windows clipboard API
# macOS: macOS clipboard API
# Linux: X11 clipboard protocols
```

**Dependencies**:
- PyQt6 clipboard support
- X11 clipboard protocols
- D-Bus clipboard integration

---

### **6. File System Paths**
**Component**: Configuration and data storage

**Linux-Specific Paths**:
```python
# Configuration directory
config_dir = os.path.expanduser("~/.config/w4l/")

# Data directory
data_dir = os.path.expanduser("~/.local/share/w4l/")

# Cache directory
cache_dir = os.path.expanduser("~/.cache/w4l/")

# Log file
log_file = os.path.expanduser("~/.local/share/w4l/w4l.log")
```

**Cross-Platform Considerations**:
```python
# Windows: %APPDATA%\w4l\
# macOS: ~/Library/Application Support/w4l/
# Linux: ~/.config/w4l/
```

---

### **7. Keyboard Simulation (Future Implementation)**
**Component**: Planned clipboard manager

**Linux-Specific Features**:
- `xdotool` for keyboard simulation
- X11/Wayland input simulation
- Linux-specific key codes

**Cross-Platform Considerations**:
```python
# Windows: pyautogui or Windows API
# macOS: pyautogui or macOS API
# Linux: xdotool or pyautogui
```

**Dependencies**:
- `xdotool` (Linux-specific)
- `pyautogui` (cross-platform alternative)
- X11/Wayland input protocols

---

### **8. Process Management**
**Component**: `src/main.py` - Signal handling

**Linux-Specific Features**:
- POSIX signal handling (SIGINT, SIGTERM)
- Linux process management
- Systemd service integration (future)

**Cross-Platform Considerations**:
```python
# Windows: Windows service management
# macOS: LaunchAgent/LaunchDaemon
# Linux: systemd services
```

**Dependencies**:
- POSIX signal handling
- Linux process management
- Systemd integration (optional)

---

### **9. Desktop Environment Integration**
**Component**: System tray and autostart

**Linux-Specific Features**:
- Desktop entry files for autostart
- System tray integration per DE
- Desktop environment detection

**Cross-Platform Considerations**:
```python
# Windows: Windows startup folder
# macOS: LaunchAgents
# Linux: Desktop entry files
```

**Dependencies**:
- Desktop entry file format
- Desktop environment detection
- System tray protocols

---

### **10. Package Management**
**Component**: Installation and dependencies

**Linux-Specific Features**:
- Package manager integration (apt, dnf, pacman)
- System package dependencies
- Linux-specific installation paths

**Cross-Platform Considerations**:
```python
# Windows: MSI/NSIS installers
# macOS: DMG/pkg installers
# Linux: Package manager integration
```

**Dependencies**:
- Linux package managers
- System package dependencies
- Installation path conventions

---

## 🔧 Cross-Platform Migration Strategy

### **Phase 1: Platform Detection**
```python
import platform

def get_platform_info():
    system = platform.system()
    release = platform.release()
    machine = platform.machine()
    return system, release, machine
```

### **Phase 2: Conditional Imports**
```python
if platform.system() == "Linux":
    from .linux import LinuxClipboardManager as ClipboardManager
elif platform.system() == "Windows":
    from .windows import WindowsClipboardManager as ClipboardManager
elif platform.system() == "Darwin":
    from .macos import MacOSClipboardManager as ClipboardManager
```

### **Phase 3: Platform-Specific Implementations**
- Create platform-specific modules
- Implement platform detection
- Add cross-platform abstractions

### **Phase 4: Testing & Validation**
- Test on each platform
- Validate functionality
- Fix platform-specific issues

---

## 📋 Current Linux Dependencies

### **System Packages**:
```bash
# Audio
sudo dnf install alsa-lib pulseaudio-libs

# Display
sudo dnf install libX11 libXext libXrandr

# Development
sudo dnf install python3-devel python3-tk

# Optional: xdotool for keyboard simulation
sudo dnf install xdotool
```

### **Python Packages**:
```python
# requirements.txt
PyQt6>=6.0.0
sounddevice>=0.4.0
numpy>=1.20.0
pyqtgraph>=0.12.0
keyboard>=0.13.0  # Linux-specific
pynput>=1.7.0     # Cross-platform alternative
```

### **Runtime Dependencies**:
- X11 or Wayland display server
- ALSA or PulseAudio audio system
- D-Bus system
- Desktop environment with system tray support

---

## 🎯 Future Cross-Platform Tasks

### **High Priority**:
1. **Platform detection system**
2. **Cross-platform hotkey library** (pynput)
3. **Cross-platform paste simulation** (pyautogui)
4. **Platform-specific configuration paths**

### **Medium Priority**:
1. **Platform-specific system tray implementations**
2. **Cross-platform audio configuration**
3. **Platform-specific window management**
4. **Cross-platform installation scripts**

### **Low Priority**:
1. **Platform-specific packaging**
2. **Cross-platform documentation**
3. **Platform-specific testing**
4. **Cross-platform CI/CD**

---

## 📝 Notes for Developers

1. **Always check platform before using Linux-specific features**
2. **Use cross-platform libraries when possible**
3. **Test on multiple Linux distributions**
4. **Document platform-specific behavior**
5. **Plan for cross-platform migration from the start**

This document should be updated as new Linux-specific features are added to the codebase. 