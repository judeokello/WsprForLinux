| Layer                 | Tool / Library                              | Purpose                                         |
| --------------------- | ------------------------------------------- | ----------------------------------------------- |
| **GUI**               | PyQt5, PyQtGraph                            | GUI window and waveform visual                  |
| **Audio Input**       | `sounddevice`                               | Captures audio from mic                         |
| **Data Processing**   | `numpy`                                     | Manages waveform data                           |
| **Speech-to-Text**    | `openai/whisper` (via `whisper` Python lib) | Transcribes audio                               |
| **Silence Detection** | Custom RMS-based silence checker            | Stops recording after inactivity                |
| **Pasting Output**    | `pyautogui`, `keyboard`, or `xdotool`       | Simulates key press to paste into active window |
| **Hotkey Listener**   | `keyboard` (fallback to `pynput`)           | Launches W4L with a global shortcut             |
| **Model Handling**    | `whisper` or `faster-whisper`               | Choose CPU/GPU efficient backend                |


🏗️ Implementation Phases
Phase 1: GUI Prototype 
Phase 2: Silence Detection & Key Controls 
Phase 3: Auto-Paste to IDE
Phase 4: Global Hotkey Support
Phase 5: Preload & Warm Start
Phase 6: Streaming Audio, Model Picker, Settings Panel
Phase 7: Deployment-ready CLI or AppImage (optional)