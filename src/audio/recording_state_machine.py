#!/usr/bin/env python3
"""
Recording State Machine for W4L.

Manages the complete lifecycle of recording sessions with proper state transitions,
error handling, and thread safety.
"""

import logging
import threading
from enum import Enum, auto
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

class RecordingState(Enum):
    """Recording session states."""
    IDLE = auto()           # Ready to start recording
    MODEL_LOADING = auto()  # Loading a transcription model
    RECORDING = auto()      # Actively recording
    STOPPING = auto()       # Transitional state during cleanup
    FINISHED = auto()       # Recording completed successfully
    ABORTED = auto()        # Recording was cancelled
    ERROR = auto()          # Error occurred
    RECOVERING = auto()     # Attempting to recover from error

class RecordingEvent(Enum):
    """Events that can trigger state transitions."""
    START_REQUESTED = auto()
    MODEL_LOAD_REQUESTED = auto()
    MODEL_LOAD_COMPLETED = auto()
    MODEL_LOAD_FAILED = auto()
    STOP_REQUESTED = auto()
    ABORT_REQUESTED = auto()
    SILENCE_DETECTED = auto()
    ERROR_OCCURRED = auto()
    RECOVERY_ATTEMPTED = auto()
    CLEANUP_COMPLETED = auto()
    RECOVERY_SUCCESS = auto()
    RECOVERY_FAILED = auto()

@dataclass
class StateTransition:
    """Represents a valid state transition."""
    from_state: RecordingState
    to_state: RecordingState
    event: RecordingEvent
    description: str

class RecordingStateMachine(QObject):
    """
    Thread-safe recording state machine with event-driven architecture.
    
    Features:
    - Validated state transitions
    - Event-driven state changes
    - Thread safety with locks
    - Error handling and recovery
    - State change notifications
    """
    
    # Signals for UI updates
    state_changed = pyqtSignal(RecordingState, RecordingState, RecordingEvent)
    error_occurred = pyqtSignal(str)
    recovery_attempted = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("w4l.audio.state_machine")
        
        # State management
        self._lock = threading.RLock()
        self._state = RecordingState.IDLE
        
        # State transition table
        self._transitions = self._build_transition_table()
        
        # State handlers
        self._state_handlers = {
            RecordingState.IDLE: self._handle_idle,
            RecordingState.MODEL_LOADING: self._handle_model_loading,
            RecordingState.RECORDING: self._handle_recording,
            RecordingState.STOPPING: self._handle_stopping,
            RecordingState.FINISHED: self._handle_finished,
            RecordingState.ABORTED: self._handle_aborted,
            RecordingState.ERROR: self._handle_error,
            RecordingState.RECOVERING: self._handle_recovering,
        }
        
        # Callbacks for external actions
        self.on_start_recording: Optional[Callable[[], None]] = None
        self.on_stop_recording: Optional[Callable[[], None]] = None
        self.on_abort_recording: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_recovery: Optional[Callable[[], None]] = None
        
        self.logger.info("Recording state machine initialized")
    
    def _build_transition_table(self) -> Dict[RecordingState, Dict[RecordingEvent, StateTransition]]:
        """Build the state transition table."""
        transitions = {}
        
        # IDLE state transitions
        transitions[RecordingState.IDLE] = {
            RecordingEvent.START_REQUESTED: StateTransition(
                RecordingState.IDLE, RecordingState.RECORDING, 
                RecordingEvent.START_REQUESTED, "Start recording"
            ),
            RecordingEvent.MODEL_LOAD_REQUESTED: StateTransition(
                RecordingState.IDLE, RecordingState.MODEL_LOADING,
                RecordingEvent.MODEL_LOAD_REQUESTED, "Start model loading"
            ),
        }
        
        # MODEL_LOADING state transitions
        transitions[RecordingState.MODEL_LOADING] = {
            RecordingEvent.MODEL_LOAD_COMPLETED: StateTransition(
                RecordingState.MODEL_LOADING, RecordingState.IDLE,
                RecordingEvent.MODEL_LOAD_COMPLETED, "Model loading completed"
            ),
            RecordingEvent.MODEL_LOAD_FAILED: StateTransition(
                RecordingState.MODEL_LOADING, RecordingState.ERROR,
                RecordingEvent.MODEL_LOAD_FAILED, "Model loading failed"
            ),
        }
        
        # RECORDING state transitions
        transitions[RecordingState.RECORDING] = {
            RecordingEvent.STOP_REQUESTED: StateTransition(
                RecordingState.RECORDING, RecordingState.STOPPING,
                RecordingEvent.STOP_REQUESTED, "Stop recording normally"
            ),
            RecordingEvent.ABORT_REQUESTED: StateTransition(
                RecordingState.RECORDING, RecordingState.ABORTED,
                RecordingEvent.ABORT_REQUESTED, "Abort recording"
            ),
            RecordingEvent.SILENCE_DETECTED: StateTransition(
                RecordingState.RECORDING, RecordingState.STOPPING,
                RecordingEvent.SILENCE_DETECTED, "Stop due to silence"
            ),
            RecordingEvent.ERROR_OCCURRED: StateTransition(
                RecordingState.RECORDING, RecordingState.ERROR,
                RecordingEvent.ERROR_OCCURRED, "Error during recording"
            ),
        }
        
        # STOPPING state transitions
        transitions[RecordingState.STOPPING] = {
            RecordingEvent.CLEANUP_COMPLETED: StateTransition(
                RecordingState.STOPPING, RecordingState.FINISHED,
                RecordingEvent.CLEANUP_COMPLETED, "Cleanup completed"
            ),
            RecordingEvent.ERROR_OCCURRED: StateTransition(
                RecordingState.STOPPING, RecordingState.ERROR,
                RecordingEvent.ERROR_OCCURRED, "Error during cleanup"
            ),
        }
        
        # FINISHED state transitions
        transitions[RecordingState.FINISHED] = {
            RecordingEvent.START_REQUESTED: StateTransition(
                RecordingState.FINISHED, RecordingState.RECORDING,
                RecordingEvent.START_REQUESTED, "Start new recording"
            ),
            RecordingEvent.MODEL_LOAD_REQUESTED: StateTransition(
                RecordingState.FINISHED, RecordingState.MODEL_LOADING,
                RecordingEvent.MODEL_LOAD_REQUESTED, "Start model loading"
            ),
        }
        
        # ABORTED state transitions
        transitions[RecordingState.ABORTED] = {
            RecordingEvent.START_REQUESTED: StateTransition(
                RecordingState.ABORTED, RecordingState.RECORDING,
                RecordingEvent.START_REQUESTED, "Start new recording"
            ),
            RecordingEvent.MODEL_LOAD_REQUESTED: StateTransition(
                RecordingState.ABORTED, RecordingState.MODEL_LOADING,
                RecordingEvent.MODEL_LOAD_REQUESTED, "Start model loading"
            ),
        }
        
        # ERROR state transitions
        transitions[RecordingState.ERROR] = {
            RecordingEvent.RECOVERY_ATTEMPTED: StateTransition(
                RecordingState.ERROR, RecordingState.RECOVERING,
                RecordingEvent.RECOVERY_ATTEMPTED, "Attempt recovery"
            ),
            RecordingEvent.START_REQUESTED: StateTransition(
                RecordingState.ERROR, RecordingState.RECORDING,
                RecordingEvent.START_REQUESTED, "Start new recording"
            ),
            RecordingEvent.MODEL_LOAD_REQUESTED: StateTransition(
                RecordingState.ERROR, RecordingState.MODEL_LOADING,
                RecordingEvent.MODEL_LOAD_REQUESTED, "Start model loading"
            ),
        }
        
        # RECOVERING state transitions
        transitions[RecordingState.RECOVERING] = {
            RecordingEvent.RECOVERY_SUCCESS: StateTransition(
                RecordingState.RECOVERING, RecordingState.IDLE,
                RecordingEvent.RECOVERY_SUCCESS, "Recovery successful"
            ),
            RecordingEvent.RECOVERY_FAILED: StateTransition(
                RecordingState.RECOVERING, RecordingState.ERROR,
                RecordingEvent.RECOVERY_FAILED, "Recovery failed"
            ),
        }
        
        return transitions
    
    def get_state(self) -> RecordingState:
        """Get the current state (thread-safe)."""
        with self._lock:
            return self._state
    
    def handle_event(self, event: RecordingEvent, **kwargs):
        """Handle an event and transition to the appropriate state."""
        with self._lock:
            current_state = self._state
            transition = self._transitions.get(current_state, {}).get(event)
            
            if transition:
                old_state = current_state
                self._state = transition.to_state
                
                self.logger.info(f"State transition: {old_state.name} -> {self._state.name} ({transition.description})")
                
                # Emit state change signal
                self.state_changed.emit(old_state, self._state, event)
                
                # Call state handler
                handler = self._state_handlers.get(self._state)
                if handler:
                    try:
                        handler(event, **kwargs)
                    except Exception as e:
                        self.logger.error(f"Error in state handler for {self._state.name}: {e}")
                        self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
            else:
                self.logger.warning(f"Invalid event {event.name} for state {current_state.name}")
                # Emit error signal for invalid transitions
                self.error_occurred.emit(f"Invalid event {event.name} for state {current_state.name}")
    
    def _handle_idle(self, event: RecordingEvent, **kwargs):
        """Handle IDLE state."""
        if event == RecordingEvent.START_REQUESTED and self.on_start_recording:
            try:
                self.on_start_recording()
            except Exception as e:
                self.logger.error(f"Error starting recording: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _handle_model_loading(self, event: RecordingEvent, **kwargs):
        """Handle MODEL_LOADING state."""
        # This handler is called when entering MODEL_LOADING state
        if event == RecordingEvent.MODEL_LOAD_REQUESTED:
            self.logger.info("Model loading started")
            # The actual model loading is handled by the main window
            # This handler just logs the state change
    
    def _handle_recording(self, event: RecordingEvent, **kwargs):
        """Handle RECORDING state."""
        # This handler is called when entering RECORDING state
        if event == RecordingEvent.START_REQUESTED and self.on_start_recording:
            try:
                self.on_start_recording()
            except Exception as e:
                self.logger.error(f"Error starting recording: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _handle_stopping(self, event: RecordingEvent, **kwargs):
        """Handle STOPPING state."""
        self.logger.info(f"_handle_stopping: Entering STOPPING state with event {event.name}")
        # This handler is called when entering STOPPING state
        if event == RecordingEvent.STOP_REQUESTED and self.on_stop_recording:
            try:
                self.logger.info("_handle_stopping: Calling on_stop_recording callback")
                self.on_stop_recording()
                self.logger.info("_handle_stopping: on_stop_recording callback completed")
                # Don't call handle_event here - let the callback do it
            except Exception as e:
                self.logger.error(f"Error stopping recording: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
        elif event == RecordingEvent.SILENCE_DETECTED and self.on_stop_recording:
            try:
                self.logger.info("_handle_stopping: Calling on_stop_recording callback (silence detected)")
                self.on_stop_recording()
                self.logger.info("_handle_stopping: on_stop_recording callback completed (silence detected)")
                # Don't call handle_event here - let the callback do it
            except Exception as e:
                self.logger.error(f"Error stopping recording due to silence: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
        else:
            self.logger.warning(f"_handle_stopping: No on_stop_recording callback or unexpected event {event.name}")
    
    def _handle_finished(self, event: RecordingEvent, **kwargs):
        """Handle FINISHED state."""
        self.logger.info(f"_handle_finished: Entering FINISHED state with event {event.name}")
        # Recording completed successfully
        self.logger.info("Recording completed successfully")
    
    def _handle_aborted(self, event: RecordingEvent, **kwargs):
        """Handle ABORTED state."""
        # This handler is called when entering ABORTED state
        if event == RecordingEvent.ABORT_REQUESTED and self.on_abort_recording:
            try:
                self.on_abort_recording()
            except Exception as e:
                self.logger.error(f"Error aborting recording: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _handle_error(self, event: RecordingEvent, **kwargs):
        """Handle ERROR state."""
        error = kwargs.get('error')
        if error:
            self.logger.error(f"Recording error: {error}")
            self.error_occurred.emit(str(error))
            if self.on_error:
                try:
                    self.on_error(error)
                except Exception as e:
                    self.logger.error(f"Error in error handler: {e}")
    
    def _handle_recovering(self, event: RecordingEvent, **kwargs):
        """Handle RECOVERING state."""
        self.logger.info("Attempting to recover from error")
        self.recovery_attempted.emit()
        
        if self.on_recovery:
            try:
                self.on_recovery()
                self.handle_event(RecordingEvent.RECOVERY_SUCCESS)
            except Exception as e:
                self.logger.error(f"Recovery failed: {e}")
                self.handle_event(RecordingEvent.RECOVERY_FAILED, error=e)
    
    def _handle_internal_error(self, error: Exception):
        """Handle internal state machine errors."""
        self.logger.error(f"Internal state machine error: {error}")
        # Force transition to error state
        with self._lock:
            old_state = self._state
            self._state = RecordingState.ERROR
            self.state_changed.emit(old_state, self._state, RecordingEvent.ERROR_OCCURRED)
    
    def reset_to_idle(self):
        """Reset the state machine to IDLE state."""
        with self._lock:
            old_state = self._state
            self._state = RecordingState.IDLE
            self.logger.info(f"State machine reset: {old_state.name} -> IDLE")
            self.state_changed.emit(old_state, self._state, RecordingEvent.START_REQUESTED)
    
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self.get_state() == RecordingState.RECORDING
    
    def can_start_recording(self) -> bool:
        """Check if recording can be started."""
        state = self.get_state()
        return state in [RecordingState.IDLE, RecordingState.FINISHED, RecordingState.ABORTED, RecordingState.ERROR]
    
    def can_stop_recording(self) -> bool:
        """Check if recording can be stopped."""
        return self.get_state() == RecordingState.RECORDING
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get detailed information about the current state."""
        state = self.get_state()
        return {
            'state': state.name,
            'is_recording': self.is_recording(),
            'can_start': self.can_start_recording(),
            'can_stop': self.can_stop_recording(),
            'valid_events': [event.name for event in self._transitions.get(state, {}).keys()]
        } 