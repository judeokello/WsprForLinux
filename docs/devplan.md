# 🚀 W4L Development Plan

## 📋 Tech Stack Overview

| Layer                 | Tool / Library                              | Purpose                                         |
| --------------------- | ------------------------------------------- | ----------------------------------------------- |
| **Language**          | Python 3.10+                                | Core application language                       |
| **GUI**               | PyQt5, PyQtGraph                            | GUI window and waveform visualization           |
| **Audio Input**       | `sounddevice`                               | Captures audio from microphone                  |
| **Data Processing**   | `numpy`                                     | Manages waveform data and buffers              |
| **Speech-to-Text**    | `openai/whisper` (via `whisper` Python lib) | Transcribes audio to text                      |
| **Silence Detection** | Custom RMS-based silence checker            | Stops recording after inactivity                |
| **Pasting Output**    | `pyautogui`, `keyboard`, or `xdotool`       | Simulates key press to paste into active window |
| **Hotkey Listener**   | `keyboard` (fallback to `pynput`)           | Launches W4L with a global shortcut             |
| **Model Handling**    | `whisper` or `faster-whisper`               | Choose CPU/GPU efficient backend                |

---

## 🏗️ Implementation Phases

### Phase 1: Project Setup & Core Infrastructure
**Goal**: Establish project structure and basic dependencies

- [x] **1.1 Project Structure Setup**
  - [x] 1.1.1 Create main application directory structure
  - [x] 1.1.2 Set up `src/` folder with modules
  - [x] 1.1.3 Create `tests/` directory
  - [x] 1.1.4 Set up `resources/` for assets
  - [x] 1.1.5 Initialize `__init__.py` files

- [x] **1.2 Dependencies & Environment**
  - [x] 1.2.1 Update `requirements.txt` with all necessary packages
  - [x] 1.2.2 Create virtual environment setup script
  - [x] 1.2.3 Add development dependencies (pytest, black, flake8)
  - [x] 1.2.4 Create `.env.example` for configuration
  - [x] 1.2.5 Set up pytest conftest.py for proper import resolution

- [x] **1.3 Basic Configuration**
  - [x] 1.3.1 Create configuration management system
  - [x] 1.3.2 Set up logging framework
  - [x] 1.3.3 Create pytest conftest.py for test import resolution
  - [x] 1.3.4 **Configure linter and IDE support**
    - [x] 1.3.4.1 Create `pyproject.toml` for modern Python tooling
    - [x] 1.3.4.2 Add VS Code settings for Python path configuration
    - [x] 1.3.4.3 Create `setup.py` for legacy tool compatibility
    - [x] 1.3.4.4 Configure pytest, black, flake8, and mypy settings
    - [x] 1.3.4.5 **Resolve import errors in test files** ✅
  - [ ] **1.3.5 Create constants file for app settings**
    - [ ] 1.3.5.1 Define audio format constants
    - [ ] 1.3.5.2 Define UI dimension constants
    - [ ] 1.3.5.3 Define timeout and threshold constants
    - [ ] 1.3.5.4 Define default configuration values
    - [ ] 1.3.5.5 Add buffer size configuration (default: 5 seconds, range: 1-30 seconds)
    - [ ] 1.3.5.6 Add capture mode configuration (streaming vs file-based)
  - [x] 1.3.6 Add error handling utilities

- [ ] **1.4 Audio System Foundation**
  - [x] **1.4.1 Audio Device Detection**
    - [x] 1.4.1.1 List available audio devices
    - [x] 1.4.1.2 **Select and configure input device** ✅
    - [x] 1.4.1.3 **Test device permissions** ✅
    - [x] 1.4.1.4 **Handle device selection** ✅
  - [x] **1.4.2 Audio Buffer Management Class**
    - [x] 1.4.2.1 Implement streaming buffer (primary)
    - [x] 1.4.2.2 Implement file-based buffer (fallback)
    - [x] 1.4.2.3 Add configurable buffer size (default: 5 seconds)
    - [x] 1.4.2.4 **Add memory management and cleanup** ✅
  - [x] **1.4.3 Audio Format Configuration** ✅
    - [x] 1.4.3.1 Set up 16kHz, mono, 16-bit format
    - [x] 1.4.3.2 Configure chunk sizes
    - [x] 1.4.3.3 Add format validation
    - [x] 1.4.3.4 Handle format conversion
  - [ ] **1.4.4 Microphone Access & Testing**
    - [ ] 1.4.4.1 Test microphone permissions
    - [ ] 1.4.4.2 Verify audio capture works
    - [ ] 1.4.4.3 Test buffer overflow handling
    - [ ] 1.4.4.4 Validate both streaming and file modes work

### Phase 2: GUI Prototype
**Goal**: Create the minimal dialog interface with waveform visualization

- [ ] **2.1 Basic GUI Framework**
  - [ ] 2.1.1 Create main application window class
  - [ ] 2.1.2 Implement window centering and styling
  - [ ] 2.1.3 Add basic PyQt5 application structure
  - [ ] 2.1.4 Set up window properties (always on top, frameless)

- [ ] **2.2 Waveform Visualization**
  - [ ] 2.2.1 Integrate PyQtGraph for real-time plotting
  - [ ] 2.2.2 Create waveform display widget
  - [ ] 2.2.3 Implement flatline display (before recording)
  - [ ] 2.2.4 Add real-time waveform updates during recording
  - [ ] 2.2.5 Style waveform with appropriate colors and scaling

- [ ] **2.3 UI Elements**
  - [ ] 2.3.1 Add instruction label: "Speak now... Press ESC to cancel or Enter to finish early"
  - [ ] 2.3.2 Implement status indicators
  - [ ] 2.3.3 Add recording state visual feedback
  - [ ] 2.3.4 Create loading/processing indicators

- [ ] **2.4 Window Management**
  - [ ] 2.4.1 Implement window show/hide functionality
  - [ ] 2.4.2 Add window positioning (center screen)
  - [ ] 2.4.3 Set up window focus management
  - [ ] 2.4.4 Test window behavior across different Linux DEs

### Phase 3: Audio Recording & Processing
**Goal**: Implement audio capture with silence detection and key controls

- [ ] **3.1 Audio Recording System**
  - [ ] 3.1.1 Implement real-time audio capture with sounddevice
  - [ ] 3.1.2 Create audio stream management
  - [ ] 3.1.3 Set up proper audio format (16kHz, mono, 16-bit)
  - [ ] 3.1.4 Add audio buffer handling and overflow protection

- [ ] **3.2 Silence Detection**
  - [ ] 3.2.1 Implement RMS-based silence detection algorithm
  - [ ] 3.2.2 Create configurable silence threshold settings
  - [ ] 3.2.3 Add silence duration tracking (5-second auto-stop)
  - [ ] 3.2.4 Test silence detection accuracy

- [ ] **3.3 Key Controls**
  - [ ] 3.3.1 Implement Enter key handling (finish recording early)
  - [ ] 3.3.2 Add Escape key handling (cancel recording)
  - [ ] 3.3.3 Create key event management system
  - [ ] 3.3.4 Test key responsiveness and edge cases

- [ ] **3.4 Recording State Management**
  - [ ] 3.4.1 Create recording state machine
  - [ ] 3.4.2 Implement start/stop/pause recording logic
  - [ ] 3.4.3 Add recording duration tracking
  - [ ] 3.4.4 Handle recording errors gracefully

### Phase 4: Whisper Integration & Transcription
**Goal**: Implement offline speech-to-text using Whisper

- [ ] **4.1 Whisper Setup**
  - [ ] 4.1.1 Integrate OpenAI Whisper library
  - [ ] 4.1.2 Set up model downloading and caching
  - [ ] 4.1.3 Configure for CPU-only inference
  - [ ] 4.1.4 Test model loading and initialization

- [ ] **4.2 Audio Preprocessing**
  - [ ] 4.2.1 Implement audio format conversion for Whisper
  - [ ] 4.2.2 Add audio normalization and filtering
  - [ ] 4.2.3 Create audio chunking for long recordings
  - [ ] 4.2.4 Optimize audio processing pipeline

- [ ] **4.3 Transcription Engine**
  - [ ] 4.3.1 Create transcription service class
  - [ ] 4.3.2 Implement async transcription processing
  - [ ] 4.3.3 Add transcription progress indicators
  - [ ] 4.3.4 Handle transcription errors and timeouts

- [ ] **4.4 Model Optimization**
  - [ ] 4.4.1 Implement model preloading on startup
  - [ ] 4.4.2 Add model caching for faster subsequent use
  - [ ] 4.4.3 Optimize memory usage for Whisper model
  - [ ] 4.4.4 Test transcription accuracy and speed
  - [ ] **4.4.5 Model-Aware Memory Management** 🔄
    - [ ] 4.4.5.1 Implement dynamic memory thresholds based on model size
    - [ ] 4.4.5.2 Add model memory requirements tracking (tiny: 150MB, base: 250MB, small: 500MB, medium: 1.5GB, large: 2.5GB)
    - [ ] 4.4.5.3 Create W4LMemoryManager class for adaptive memory management
    - [ ] 4.4.5.4 Add memory compatibility warnings for large models
    - [ ] 4.4.5.5 Implement optimal buffer sizing based on available memory

### Phase 5: Auto-Paste Integration
**Goal**: Automatically paste transcribed text into active applications

- [ ] **5.1 Clipboard Integration**
  - [ ] 5.1.1 Implement clipboard management
  - [ ] 5.1.2 Add text copying to system clipboard
  - [ ] 5.1.3 Test clipboard functionality across Linux DEs
  - [ ] 5.1.4 Handle clipboard permission issues

- [ ] **5.2 Keyboard Simulation**
  - [ ] 5.2.1 Research and implement keyboard simulation (pyautogui/xdotool)
  - [ ] 5.2.2 Create paste key combination simulation
  - [ ] 5.2.3 Add focus restoration to previous window
  - [ ] 5.2.4 Test with various applications (Cursor, VS Code, etc.)

- [ ] **5.3 Application Detection**
  - [ ] 5.3.1 Implement active window detection
  - [ ] 5.3.2 Add application-specific paste strategies
  - [ ] 5.3.3 Create fallback paste methods
  - [ ] 5.3.4 Test compatibility with different IDEs

- [ ] **5.4 Paste Reliability**
  - [ ] 5.4.1 Add paste confirmation mechanisms
  - [ ] 5.4.2 Implement paste retry logic
  - [ ] 5.4.3 Create paste error handling
  - [ ] 5.4.4 Test paste reliability across different scenarios

### Phase 6: Global Hotkey Support
**Goal**: Enable launching W4L from anywhere with keyboard shortcuts

- [ ] **6.1 Hotkey System**
  - [ ] 6.1.1 Implement global hotkey listener (keyboard/pynput)
  - [ ] 6.1.2 Create configurable hotkey settings
  - [ ] 6.1.3 Add hotkey registration and unregistration
  - [ ] 6.1.4 Test hotkey functionality across Linux DEs

- [ ] **6.2 Application Lifecycle**
  - [ ] 6.2.1 Create daemon/service mode for background operation
  - [ ] 6.2.2 Implement application startup and shutdown
  - [ ] 6.2.3 Add system tray integration (optional)
  - [ ] 6.2.4 Handle application persistence

- [ ] **6.3 Hotkey Management**
  - [ ] 6.3.1 Add hotkey conflict detection
  - [ ] 6.3.2 Implement hotkey customization interface
  - [ ] 6.3.3 Create hotkey help/documentation
  - [ ] 6.3.4 Test hotkey behavior with other applications

- [ ] **6.4 System Integration**
  - [ ] 6.4.1 Create desktop entry for autostart
  - [ ] 6.4.2 Add systemd service file (optional)
  - [ ] 6.4.3 Implement proper signal handling
  - [ ] 6.4.4 Test system integration on different distros

### Phase 7: Performance & Polish
**Goal**: Optimize performance and add final polish

- [ ] **7.1 Performance Optimization**
  - [ ] 7.1.1 Optimize audio processing pipeline
  - [ ] 7.1.2 Implement memory management improvements
  - [ ] 7.1.3 Add CPU usage optimization
  - [ ] 7.1.4 Profile and optimize critical paths

- [ ] **7.2 User Experience**
  - [ ] 7.2.1 Add startup splash screen
  - [ ] 7.2.2 Implement smooth animations and transitions
  - [ ] 7.2.3 Create user feedback mechanisms
  - [ ] 7.2.4 Add accessibility features

- [ ] **7.3 Error Handling & Logging**
  - [ ] 7.3.1 Implement comprehensive error handling
  - [ ] 7.3.2 Add detailed logging system
  - [ ] 7.3.3 Create user-friendly error messages
  - [ ] 7.3.4 Add crash reporting (optional)

- [ ] **7.4 Testing & Quality Assurance**
  - [ ] 7.4.1 Write unit tests for core components
  - [ ] 7.4.2 Add integration tests
  - [ ] 7.4.3 Perform cross-distribution testing
  - [ ] 7.4.4 Conduct user acceptance testing

### Phase 8: Advanced Features (Optional)
**Goal**: Add advanced features for power users

- [ ] **8.1 Streaming Audio**
  - [ ] 8.1.1 Implement real-time streaming transcription
  - [ ] 8.1.2 Add live transcription display
  - [ ] 8.1.3 Create streaming audio buffers
  - [ ] 8.1.4 Optimize for low-latency operation

- [ ] **8.2 Model Picker**
  - [ ] 8.2.1 Add support for different Whisper models
  - [ ] 8.2.2 Create model selection interface
  - [ ] 8.2.3 Implement model switching functionality
  - [ ] 8.2.4 Add model performance comparison

- [ ] **8.3 Settings Panel**
  - [ ] 8.3.1 Create comprehensive settings interface
  - [ ] 8.3.2 Add audio device selection
  - [ ] 8.3.3 Implement hotkey customization
  - [ ] 8.3.4 Add transcription language selection

- [ ] **8.4 Advanced Audio Features**
  - [ ] 8.4.1 Add noise reduction
  - [ ] 8.4.2 Implement audio level normalization
  - [ ] 8.4.3 Create audio quality settings
  - [ ] 8.4.4 Add microphone calibration

### Phase 9: Deployment & Distribution
**Goal**: Prepare for distribution and deployment

- [ ] **9.1 Packaging**
  - [ ] 9.1.1 Create AppImage package
  - [ ] 9.1.2 Build .deb package for Debian/Ubuntu
  - [ ] 9.1.3 Create RPM package for Fedora/RHEL
  - [ ] 9.1.4 Add flatpak support (optional)

- [ ] **9.2 Documentation**
  - [ ] 9.2.1 Write comprehensive README
  - [ ] 9.2.2 Create installation guide
  - [ ] 9.2.3 Add troubleshooting documentation
  - [ ] 9.2.4 Create user manual

- [ ] **9.3 CI/CD Pipeline**
  - [ ] 9.3.1 Set up GitHub Actions for automated testing
  - [ ] 9.3.2 Create automated build pipeline
  - [ ] 9.3.3 Add release automation
  - [ ] 9.3.4 Implement automated packaging

- [ ] **9.4 Distribution**
  - [ ] 9.4.1 Prepare GitHub repository
  - [ ] 9.4.2 Create release notes template
  - [ ] 9.4.3 Set up issue templates
  - [ ] 9.4.4 Add contribution guidelines

---

## 📊 Progress Tracking

**Overall Progress**: 18% Complete
- Phase 1: 3.5/4 tasks complete (1.1, 1.2, 1.3 done; 1.4 in progress)
  - ✅ 1.1 Project Structure Setup (100% complete)
  - ✅ 1.2 Dependencies & Environment (100% complete)
  - ✅ 1.3 Basic Configuration (80% complete - conftest.py added)
  - 🔄 1.4 Audio System Foundation (60% complete - device detection and buffer management done)
- Phase 2: 0/4 tasks complete
- Phase 3: 0/4 tasks complete
- Phase 4: 0/4 tasks complete
- Phase 5: 0/4 tasks complete
- Phase 6: 0/4 tasks complete
- Phase 7: 0/4 tasks complete
- Phase 8: 0/4 tasks complete (Optional)
- Phase 9: 0/4 tasks complete

**Recent Improvements**:
- ✅ Created `tests/conftest.py` for proper import resolution
- ✅ All 20 tests passing without PYTHONPATH environment variable
- ✅ Linter errors resolved for test files
- ✅ Organized debug scripts and test files properly

---

## 🎯 Success Criteria

- [ ] W4L launches with global hotkey
- [ ] GUI appears with waveform visualization
- [ ] Audio recording starts immediately
- [ ] Silence detection works reliably
- [ ] Transcription completes within 2-3 seconds
- [ ] Text pastes into active application
- [ ] GUI dismisses automatically
- [ ] Works offline without internet
- [ ] Compatible with major Linux distributions
- [ ] Memory usage stays under 500MB
- [ ] CPU usage reasonable during transcription

---

## 🔧 Development Environment Setup

```bash
# Create virtual environment
python3 -m venv w4l_env
source w4l_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black src/
```

