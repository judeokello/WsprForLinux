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
    RECORDING = auto()      # Actively recording
    STOPPING = auto()       # Transitional state during cleanup
    FINISHED = auto()       # Recording completed successfully
    ABORTED = auto()        # Recording was cancelled
    ERROR = auto()          # Error occurred
    RECOVERING = auto()     # Attempting to recover from error

class RecordingEvent(Enum):
    """Events that can trigger state transitions."""
    START_REQUESTED = auto()
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
        self._lock = threading.Lock()
        self._state = RecordingState.IDLE
        
        # State transition table
        self._transitions = self._build_transition_table()
        
        # State handlers
        self._state_handlers = {
            RecordingState.IDLE: self._handle_idle,
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
        }
        
        # ABORTED state transitions
        transitions[RecordingState.ABORTED] = {
            RecordingEvent.START_REQUESTED: StateTransition(
                RecordingState.ABORTED, RecordingState.RECORDING,
                RecordingEvent.START_REQUESTED, "Start new recording"
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
    
    def handle_event(self, event: RecordingEvent, **kwargs) -> bool:
        """
        Handle an event and transition state if valid.
        
        Args:
            event: The event to handle
            **kwargs: Additional data for the event
            
        Returns:
            True if transition was successful, False otherwise
        """
        with self._lock:
            current_state = self._state
            self.logger.debug(f"Handling event {event.name} in state {current_state.name}")
            
            # Check if transition is valid
            if current_state not in self._transitions:
                self.logger.error(f"No transitions defined for state {current_state.name}")
                return False
            
            if event not in self._transitions[current_state]:
                self.logger.warning(f"Invalid event {event.name} for state {current_state.name}")
                return False
            
            # Get the transition
            transition = self._transitions[current_state][event]
            
            # Execute the transition
            old_state = self._state
            self._state = transition.to_state
            
            # Log the transition
            self.logger.info(f"State transition: {old_state.name} -> {self._state.name} ({transition.description})")
            
            # Emit signal for UI updates
            self.state_changed.emit(old_state, self._state, event)
            
            # Call state handler
            if self._state in self._state_handlers:
                try:
                    self._state_handlers[self._state](event, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error in state handler for {self._state.name}: {e}")
                    self._handle_internal_error(e)
            
            return True
    
    def _handle_idle(self, event: RecordingEvent, **kwargs):
        """Handle IDLE state."""
        if event == RecordingEvent.START_REQUESTED and self.on_start_recording:
            try:
                self.on_start_recording()
            except Exception as e:
                self.logger.error(f"Error starting recording: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _handle_recording(self, event: RecordingEvent, **kwargs):
        """Handle RECORDING state."""
        if event == RecordingEvent.STOP_REQUESTED and self.on_stop_recording:
            try:
                self.on_stop_recording()
                self.handle_event(RecordingEvent.CLEANUP_COMPLETED)
            except Exception as e:
                self.logger.error(f"Error stopping recording: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
        elif event == RecordingEvent.ABORT_REQUESTED and self.on_abort_recording:
            try:
                self.on_abort_recording()
            except Exception as e:
                self.logger.error(f"Error aborting recording: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
        elif event == RecordingEvent.SILENCE_DETECTED and self.on_stop_recording:
            try:
                self.on_stop_recording()
                self.handle_event(RecordingEvent.CLEANUP_COMPLETED)
            except Exception as e:
                self.logger.error(f"Error stopping recording due to silence: {e}")
                self.handle_event(RecordingEvent.ERROR_OCCURRED, error=e)
    
    def _handle_stopping(self, event: RecordingEvent, **kwargs):
        """Handle STOPPING state."""
        # This state is mainly for cleanup operations
        # The actual cleanup should be handled by the external callback
        pass
    
    def _handle_finished(self, event: RecordingEvent, **kwargs):
        """Handle FINISHED state."""
        # Recording completed successfully
        self.logger.info("Recording completed successfully")
    
    def _handle_aborted(self, event: RecordingEvent, **kwargs):
        """Handle ABORTED state."""
        # Recording was cancelled
        self.logger.info("Recording was aborted")
    
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