#!/usr/bin/env python3
"""
Simple test for Recording State Machine transitions.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio.recording_state_machine import RecordingStateMachine, RecordingState, RecordingEvent

def test_state_machine():
    """Test basic state machine transitions."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test.simple")
    
    # Create state machine
    sm = RecordingStateMachine()
    
    # Test initial state
    assert sm.get_state() == RecordingState.IDLE
    logger.info("✓ Initial state: IDLE")
    
    # Test start recording
    sm.handle_event(RecordingEvent.START_REQUESTED)
    assert sm.get_state() == RecordingState.RECORDING
    logger.info("✓ Start recording: RECORDING")
    
    # Test stop recording
    sm.handle_event(RecordingEvent.STOP_REQUESTED)
    assert sm.get_state() == RecordingState.STOPPING
    logger.info("✓ Stop recording: STOPPING")
    
    # Test cleanup completion
    sm.handle_event(RecordingEvent.CLEANUP_COMPLETED)
    assert sm.get_state() == RecordingState.FINISHED
    logger.info("✓ Cleanup completed: FINISHED")
    
    # Test start new recording
    sm.handle_event(RecordingEvent.START_REQUESTED)
    assert sm.get_state() == RecordingState.RECORDING
    logger.info("✓ Start new recording: RECORDING")
    
    # Test abort recording
    sm.handle_event(RecordingEvent.ABORT_REQUESTED)
    assert sm.get_state() == RecordingState.ABORTED
    logger.info("✓ Abort recording: ABORTED")
    
    # Test start after abort
    sm.handle_event(RecordingEvent.START_REQUESTED)
    assert sm.get_state() == RecordingState.RECORDING
    logger.info("✓ Start after abort: RECORDING")
    
    # Test silence detection
    sm.handle_event(RecordingEvent.SILENCE_DETECTED)
    assert sm.get_state() == RecordingState.STOPPING
    logger.info("✓ Silence detected: STOPPING")
    
    # Test cleanup completion
    sm.handle_event(RecordingEvent.CLEANUP_COMPLETED)
    assert sm.get_state() == RecordingState.FINISHED
    logger.info("✓ Cleanup completed: FINISHED")
    
    logger.info("🎉 All state machine transitions working correctly!")

if __name__ == "__main__":
    test_state_machine() 