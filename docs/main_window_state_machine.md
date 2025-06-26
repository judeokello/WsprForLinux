# W4L Main Window State Machine: States & UI/Logging Actions

This document describes the state machine for the W4L main window, including all states, their meaning, and the corresponding UI and logging actions. This mapping ensures the UI is always in sync with the app's state and provides clear feedback to the user.

## State Descriptions and Actions

- **MODEL_LOADING**
  - *Description*: The app is loading the selected Whisper model (downloading, verifying, or initializing in memory).
  - *UI*: Status label shows "Loading model: [model name]..."; model dropdown and record button are disabled; waveform is flatline/inactive.
  - *Logging*: Log "Started loading model [model name]".

- **MODEL_READY**
  - *Description*: The model is fully loaded and ready for use.
  - *UI*: Status label shows "Model loaded: [model name]"; model dropdown and record button are enabled; waveform is flatline.
  - *Logging*: Log "Model loaded: [model name]".

- **MODEL_ERROR**
  - *Description*: There was an error loading the model (download failed, checksum mismatch, etc.).
  - *UI*: Status label shows "Error loading model: [error message]"; model dropdown enabled; record button disabled; waveform is flatline.
  - *Logging*: Log error details.

- **RECORDING**
  - *Description*: The app is actively recording audio.
  - *UI*: Status label shows "Recording..."; model dropdown disabled; record button changes to "Stop Recording"; waveform is live.
  - *Logging*: Log "Recording started".

- **STOPPING_RECORDING**
  - *Description*: The app is stopping the recording and processing the audio (e.g., for transcription).
  - *UI*: Status label shows "Processing recording..." or "Transcribing..."; model dropdown and record button are disabled; waveform may freeze or show "processing".
  - *Logging*: Log "Stopping recording, processing audio".

- **IDLE / READY**
  - *Description*: The app is ready for a new recording (no model loading or recording in progress).
  - *UI*: Status label shows "Ready" or "Model loaded: [model name]"; model dropdown and record button are enabled; waveform is flatline.
  - *Logging*: Log "Ready for recording".

- **ERROR / ABORTED**
  - *Description*: An error occurred during recording or processing, or the user aborted.
  - *UI*: Status label shows "Error: [error message]" or "Recording aborted"; model dropdown and record button are enabled; waveform is flatline.
  - *Logging*: Log error or abort event.

## State/UI/Logging Summary Table

| State             | Status Label                | Dropdown | Record Btn | Waveform   | Logging/Event                |
|-------------------|----------------------------|----------|------------|------------|------------------------------|
| MODEL_LOADING     | Loading model: ...          | Disabled | Disabled   | Flatline   | Log start loading            |
| MODEL_READY       | Model loaded: ...           | Enabled  | Enabled    | Flatline   | Log model loaded             |
| MODEL_ERROR       | Error loading model: ...    | Enabled  | Disabled   | Flatline   | Log error                    |
| RECORDING         | Recording...                | Disabled | Stop       | Live       | Log recording started        |
| STOPPING_RECORDING| Processing recording...     | Disabled | Disabled   | Freeze     | Log stopping/processing      |
| IDLE/READY        | Ready / Model loaded: ...   | Enabled  | Enabled    | Flatline   | Log ready                    |
| ERROR/ABORTED     | Error: ... / Aborted        | Enabled  | Enabled    | Flatline   | Log error/abort              |

This mapping should be used to drive all UI and logging behavior in the main window, ensuring a consistent and user-friendly experience. 