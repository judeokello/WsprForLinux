# 📝 Product Requirements Document: W4L (Wispr for Linux)

## Overview
**W4L** is a lightweight offline voice input assistant for Linux. Inspired by Wispr Flow, it allows developers to trigger a voice recording dialog with a global hotkey and insert transcribed text directly into their IDE (e.g., Cursor). It operates fully offline and is optimized for quick developer workflows.

---

## 🎯 Goals

- Enable quick voice-to-text input on Linux.
- Operate entirely offline with no internet dependency.
- Provide a distraction-free micro GUI with waveform visualization.
- Transcribe voice into text using a local Whisper model.
- Insert transcription into an active text input (e.g., Cursor IDE chat).

---

## 🧑‍💻 Target Users

- Developers on Linux, especially users of Cursor IDE.
- Voice-first users and those with accessibility needs.
- Developers in bandwidth-limited or air-gapped environments.

---

## 🔧 Features

### Core Features

- **Global Hotkey Trigger**
  - Launches W4L from anywhere with a keyboard shortcut.
  
- **Minimal Dialog Interface**
  - Centered GUI window with:
    - Flatlined waveform before speech.
    - Real-time waveform while speaking.
    - Instruction label: “Speak now... Press ESC to cancel or Enter to finish early.”

- **Recording Behavior**
  - Starts capturing audio immediately.
  - Auto-stop after ~5 seconds of silence.
  - Manual stop via Enter key.
  - Cancel via Escape key.

- **Transcription**
  - Uses locally stored Whisper model (`small`) for transcription.
  - CPU-only inference for maximum compatibility.
  - Pasted into active window (Cursor IDE chat).

- **Performance Enhancements**
  - Whisper model preloaded on first launch for faster reuse.
  - GUI auto-dismisses after paste/cancel.

---

## 💻 Tech Stack

| Layer          | Technology                      |
|----------------|----------------------------------|
| Language       | Python 3.10+                     |
| GUI            | PyQt5                            |
| Audio Capture  | sounddevice                      |
| Visualization  | pyqtgraph                        |
| Transcription  | OpenAI Whisper (offline, CPU)    |
| Buffer Mgmt    | NumPy                            |

---

## 🧪 Development Workflow

- Install dependencies via `requirements.txt`
- Launch script with a hotkey manager (e.g., `xdotool`, `sxhkd`, or custom daemon)
- On hotkey press:
  - GUI opens
  - Audio is recorded
  - Transcribed text is pasted into active input
  - GUI closes and app remains preloaded

---

## 🚀 Deployment

- **Distribution:** via GitHub repo, optionally packaged as `.AppImage` or `.deb`
- **Internet Access:** Not required post-installation
- **System Requirements:**
  - Linux (any modern distro)
  - Python 3.10+
  - ffmpeg installed

---