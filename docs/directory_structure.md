# 📁 W4L Directory Structure Design

## 🏗️ Proposed Directory Structure

```
WsprForLinux/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main GUI window
│   │   ├── waveform_widget.py  # Waveform visualization
│   │   └── ui_components.py    # Reusable UI elements
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── recorder.py         # Audio recording system
│   │   ├── processor.py        # Audio processing utilities
│   │   └── silence_detector.py # Silence detection logic
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── whisper_service.py  # Whisper integration
│   │   ├── model_manager.py    # Model loading/caching
│   │   └── audio_converter.py  # Audio format conversion
│   ├── system/
│   │   ├── __init__.py
│   │   ├── hotkey_manager.py   # Global hotkey handling
│   │   ├── clipboard_manager.py # Clipboard operations
│   │   ├── window_manager.py   # Active window detection
│   │   └── paste_service.py    # Auto-paste functionality
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Configuration management
│   │   ├── constants.py        # Application constants
│   │   └── logging_config.py   # Logging setup
│   └── utils/
│       ├── __init__.py
│       ├── error_handler.py    # Error handling utilities
│       ├── validators.py       # Input validation
│       └── helpers.py          # General utility functions
├── tests/
│   ├── __init__.py
│   ├── test_gui/
│   ├── test_audio/
│   ├── test_transcription/
│   ├── test_system/
│   └── conftest.py
├── resources/
│   ├── icons/
│   │   ├── app_icon.png
│   │   ├── record_icon.png
│   │   ├── stop_icon.png
│   │   └── mic_icon.png
│   ├── styles/
│   │   ├── main.qss           # Qt stylesheet
│   │   └── dark_theme.qss     # Dark theme stylesheet
│   ├── sounds/
│   │   ├── start_recording.wav
│   │   └── stop_recording.wav
│   └── models/
│       └── .gitkeep           # Placeholder for downloaded models
├── docs/
│   ├── wfl_prd.md
│   ├── devplan.md
│   ├── directory_structure.md
│   └── requirements.txt
├── scripts/
│   ├── setup.sh               # Development environment setup
│   ├── install.sh             # Installation script
│   └── build_package.sh       # Package building script
├── requirements.txt
├── requirements-dev.txt        # Development dependencies
├── setup.py                   # Package configuration
├── .env.example               # Environment variables template
├── .gitignore
├── README.md
└── LICENSE
```

---

## 📂 Detailed Module Breakdown

### **src/ - Main Application Code**

#### **gui/ - User Interface Components**
- **main_window.py**: The primary application window that users see
  - Window positioning and styling
  - Event handling for key presses (Enter/Escape)
  - Integration with other modules
- **waveform_widget.py**: Real-time audio waveform visualization
  - PyQtGraph integration for plotting
  - Audio level display and animation
  - Color schemes and styling
- **ui_components.py**: Reusable UI elements
  - Custom buttons, labels, and indicators
  - Status displays and progress bars
  - Consistent styling across the app

#### **audio/ - Audio Processing System**
- **recorder.py**: Core audio recording functionality
  - Microphone access and device management
  - Real-time audio stream handling
  - Buffer management and overflow protection
- **processor.py**: Audio data processing utilities
  - Audio format conversion (16kHz, mono, 16-bit)
  - Audio normalization and filtering
  - Data chunking for processing
- **silence_detector.py**: Silence detection algorithm
  - RMS-based volume analysis
  - Configurable silence thresholds
  - Duration tracking for auto-stop

#### **transcription/ - Speech-to-Text System**
- **whisper_service.py**: OpenAI Whisper integration
  - Model loading and initialization
  - Audio transcription processing
  - Error handling and timeouts
- **model_manager.py**: Whisper model management
  - Model downloading and caching
  - Memory optimization
  - Model switching capabilities
- **audio_converter.py**: Audio format preparation
  - Conversion to Whisper-compatible format
  - Audio preprocessing pipeline
  - Quality optimization

#### **system/ - System Integration**
- **hotkey_manager.py**: Global hotkey functionality
  - Keyboard event listening
  - Hotkey registration/unregistration
  - Conflict detection and resolution
- **clipboard_manager.py**: Clipboard operations
  - Text copying to system clipboard
  - Cross-desktop environment compatibility
  - Permission handling
- **window_manager.py**: Active window detection
  - Current application identification
  - Window focus management
  - Application-specific handling
- **paste_service.py**: Auto-paste functionality
  - Keyboard simulation (Ctrl+V)
  - Application-specific paste strategies
  - Fallback mechanisms

#### **config/ - Configuration Management**
- **settings.py**: Application settings
  - User preferences storage
  - Configuration file management
  - Default values and validation
- **constants.py**: Application constants
  - Audio format specifications
  - UI dimensions and colors
  - Timeout values and thresholds
- **logging_config.py**: Logging system setup
  - Log level configuration
  - File and console output
  - Error tracking

#### **utils/ - Utility Functions**
- **error_handler.py**: Error management
  - Exception handling utilities
  - User-friendly error messages
  - Crash reporting (optional)
- **validators.py**: Input validation
  - Audio device validation
  - Configuration validation
  - User input sanitization
- **helpers.py**: General utilities
  - File path handling
  - Platform detection
  - Common helper functions

---

## 🎨 Resources/ Assets Explained

### **icons/ - Visual Assets**
- **app_icon.png**: Main application icon (system tray, desktop)
- **record_icon.png**: Recording state indicator
- **stop_icon.png**: Stop recording button
- **mic_icon.png**: Microphone status indicator

**Why these assets?**
- Professional appearance and brand identity
- Clear visual feedback for different states
- Consistent iconography across the application

### **styles/ - UI Styling**
- **main.qss**: Primary Qt stylesheet
  - Modern, clean design
  - Consistent color scheme
  - Responsive layout styling
- **dark_theme.qss**: Dark mode support
  - Reduced eye strain for developers
  - Consistent with modern IDE themes

**Why QSS files?**
- Qt's native styling system
- Easy theme switching
- Maintainable and customizable

### **sounds/ - Audio Feedback**
- **start_recording.wav**: Audio cue when recording begins
- **stop_recording.wav**: Audio cue when recording ends

**Why audio feedback?**
- Accessibility for users with visual impairments
- Clear indication of recording state
- Professional user experience

### **models/ - AI Model Storage**
- **.gitkeep**: Placeholder file to maintain directory structure
- Downloaded Whisper models will be stored here
- Kept out of version control (large files)

**Why separate models directory?**
- Models are large (~150MB for small Whisper model)
- Not included in git repository
- Easy to manage and update independently

---

## 📝 __init__.py Files Explained

### **What are __init__.py files?**
- Python package markers that make directories into packages
- Enable importing modules from those directories
- Can contain package initialization code

### **Where they go:**
1. **src/__init__.py**: Main package initialization
2. **src/gui/__init__.py**: GUI module exports
3. **src/audio/__init__.py**: Audio module exports
4. **src/transcription/__init__.py**: Transcription module exports
5. **src/system/__init__.py**: System module exports
6. **src/config/__init__.py**: Config module exports
7. **src/utils/__init__.py**: Utils module exports
8. **tests/__init__.py**: Test package marker

### **What they contain:**
```python
# Example: src/gui/__init__.py
from .main_window import MainWindow
from .waveform_widget import WaveformWidget
from .ui_components import StatusIndicator

__all__ = ['MainWindow', 'WaveformWidget', 'StatusIndicator']
```

**Why this structure?**
- Clean imports: `from src.gui import MainWindow`
- Clear module boundaries
- Easy to maintain and refactor
- Standard Python package structure

---

## 🎯 Design Principles

### **Separation of Concerns**
- Each module has a single responsibility
- Clear interfaces between modules
- Easy to test individual components

### **Modularity**
- Components can be developed independently
- Easy to swap implementations
- Clear dependency management

### **Scalability**
- Easy to add new features
- Clear extension points
- Maintainable codebase

### **Cross-Platform Compatibility**
- Platform-specific code isolated in system/ module
- Easy to adapt for different Linux distributions
- Clear abstraction layers

---

## 🚀 Next Steps

1. **Create the directory structure** as outlined above
2. **Initialize __init__.py files** with proper exports
3. **Set up basic module skeletons** with class definitions
4. **Create placeholder files** for resources
5. **Set up import structure** for clean module access

This structure provides a solid foundation for building W4L with clear organization, maintainability, and scalability in mind. Each module has a specific purpose and clear interfaces, making the development process more manageable and the final product more robust.  M