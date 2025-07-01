#!/usr/bin/env python3
"""
Model Manager UI Component for W4L.

Handles model selection, loading, and UI updates for the main window.
Extracted from main_window.py to improve separation of concerns.
"""

import logging
import psutil
import whisper
import gc
from typing import Optional, Tuple, List, Dict
from PyQt6.QtWidgets import QComboBox, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtCore import pyqtSlot
from transcription.model_manager import ModelManager
from config import ConfigManager

# Memory requirements for different models
MODEL_MEMORY_REQ = {
    'tiny': 1 * 1024**3,
    'base': 1 * 1024**3,
    'small': 2 * 1024**3,
    'medium': 5 * 1024**3,
    'large': 10 * 1024**3,
    'large-v1': 10 * 1024**3,
    'large-v2': 10 * 1024**3,
    'large-v3': 10 * 1024**3,
}

class ModelLoadWorker(QObject):
    """Worker thread for loading Whisper models."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, model_name: str, old_model_tuple: Optional[Tuple], 
                 config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.old_model = old_model_tuple[0] if old_model_tuple else None
        self.old_model_name = old_model_tuple[1] if old_model_tuple else None
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"ModelLoadWorker: Constructed for model '{self.model_name}' (thread: {QThread.currentThread()})")

    @pyqtSlot()
    def run(self):
        """Load the specified model in a background thread."""
        import traceback
        from PyQt6.QtCore import QThread
        print(f"DEBUG: ModelLoadWorker.run() called for model '{self.model_name}'")
        self.logger.info(f"ModelLoadWorker: ENTERED run() for model '{self.model_name}' (thread: {QThread.currentThread()})")
        try:
            self.logger.info(f"ModelLoadWorker: Starting to load model '{self.model_name}'")
            
            # Unload old model
            if self.old_model:
                print(f"DEBUG: Unloading old model '{self.old_model_name}'")
                self.logger.info(f"ModelLoadWorker: Unloading old model '{self.old_model_name}'")
                del self.old_model
                gc.collect()
                self.logger.info(f"ModelLoadWorker: Old model unloaded and garbage collected")
            else:
                print(f"DEBUG: No old model to unload")
                self.logger.info(f"ModelLoadWorker: No old model to unload")

            self.logger.info(f"ModelLoadWorker: About to call whisper.load_model('{self.model_name}')")
            model = whisper.load_model(self.model_name)
            self.logger.info(f"ModelLoadWorker: Successfully loaded model '{self.model_name}'")
            
            # Update config
            self.logger.debug(f"ModelLoadWorker: Updating config to use model '{self.model_name}'")
            self.config_manager.set_config_value('transcription', 'model', self.model_name)
            self.logger.debug(f"ModelLoadWorker: Config updated for model '{self.model_name}'")
            
            self.logger.info(f"ModelLoadWorker: Emitting finished signal with model")
            self.finished.emit((model, self.model_name))
            self.logger.info(f"ModelLoadWorker: Finished signal emitted")
            self.logger.info(f"ModelLoadWorker: run() method completed successfully")
        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error(f"ModelLoadWorker: Failed to load model '{self.model_name}': {e}\nTraceback:\n{tb}")
            self.error.emit(str(e))
            self.logger.info(f"ModelLoadWorker: run() method completed with error")
        finally:
            thread = QThread.currentThread()
            self.logger.info(f"ModelLoadWorker: Quitting thread {thread}")
            if isinstance(thread, QThread):
                thread.quit()
            else:
                self.logger.warning("ModelLoadWorker: currentThread is not a QThread instance, cannot call quit()")

class ModelManagerUI(QObject):
    """
    Manages model-related UI components and operations.
    
    Handles:
    - Model dropdown population and selection
    - Model loading in background threads
    - Model-related UI state updates
    - Memory checks for model loading
    """
    
    # Signals
    model_loaded = pyqtSignal(object)  # Emitted when model is successfully loaded
    model_load_error = pyqtSignal(str)  # Emitted when model loading fails
    model_selection_changed = pyqtSignal(str)  # Emitted when user selects a different model
    
    def __init__(self, model_manager: ModelManager, config_manager: ConfigManager, 
                 model_combo: QComboBox, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.config_manager = config_manager
        self.model_combo = model_combo
        self.logger = logging.getLogger(__name__)
        
        # Model state
        self.whisper_model = None
        self.load_threads = []  # Keep references to all running model load threads
        self.load_workers = []  # Keep references to all running model load workers
        
        # Connect model combo signals
        self.model_combo.currentIndexChanged.connect(self._on_model_selected)
        
        self.logger.info("ModelManagerUI initialized")
    
    def populate_model_dropdown(self):
        """Populate the model dropdown with available models."""
        self.model_combo.blockSignals(True)  # Block signals during population
        self.model_combo.clear()
        all_models = self.model_manager.list_models()
        available_models = [m for m in all_models if m.get('is_verified')]
        
        if self.logger:
            self.logger.debug(f"Found {len(all_models)} total models, {len(available_models)} verified models")
            for model in all_models:
                self.logger.debug(f"Model '{model['name']}': downloaded={model.get('is_downloaded')}, verified={model.get('is_verified')}")

        if not available_models:
            self.model_combo.addItem("No models found")
            self.model_combo.setEnabled(False)
            self.logger.warning("No verified models found - dropdown disabled")
            self.model_combo.blockSignals(False)
            return
            
        self.model_combo.setEnabled(True)
        for model in available_models:
            size_bytes = model.get('size_bytes', 0)
            if not size_bytes:
                size_str = 'Unknown size'
            else:
                size_mb = size_bytes / (1024 * 1024)
                size_str = f'{size_mb:.1f} MB'
            display_text = f"{model['name']} ({size_str})"
            self.model_combo.addItem(display_text, userData=model)
            print(f"DEBUG: Added to dropdown: '{display_text}' userData={model}")
            if self.logger:
                self.logger.debug(f"Added model to dropdown: {display_text}")
            
        # Set current model from config
        current_model_name = self.config_manager.get_config_value('transcription', 'model', 'tiny')
        if self.logger:
            self.logger.debug(f"Current model from config: {current_model_name}")

        found_index = -1
        for i in range(self.model_combo.count()):
            model_data = self.model_combo.itemData(i)
            print(f"DEBUG: Dropdown index {i} display='{self.model_combo.itemText(i)}' userData={model_data}")
            if model_data and model_data['name'] == current_model_name:
                found_index = i
                break

        if found_index != -1:
            print(f"DEBUG: About to block signals and set index {found_index}")
            self.model_combo.setCurrentIndex(found_index)
            print(f"DEBUG: Signals unblocked after setting index {found_index}")
            if self.logger:
                self.logger.debug(f"Set dropdown to model at index {found_index}: {current_model_name}")
        else:
            if self.logger:
                self.logger.warning(f"Could not find model '{current_model_name}' in dropdown, will use first available model and update config")
            # If the configured model is not available, use the first available one
            if self.model_combo.count() > 0:
                print(f"DEBUG: About to block signals and set index 0 (fallback)")
                self.model_combo.setCurrentIndex(0)
                print(f"DEBUG: Signals unblocked after setting index 0")
                first_model = self.model_combo.itemData(0)
                if first_model:
                    # Update config to match fallback
                    self.config_manager.set_config_value('transcription', 'model', first_model['name'])
                    if self.logger:
                        self.logger.info(f"Config updated to fallback model: {first_model['name']}")
        self.model_combo.blockSignals(False)  # Unblock signals after population
        # Print all dropdown items for debug
        print("DEBUG: Final dropdown items:")
        for i in range(self.model_combo.count()):
            print(f"  Index {i}: '{self.model_combo.itemText(i)}' userData={self.model_combo.itemData(i)}")
    
    def _on_model_selected(self, index):
        """Handle model selection from dropdown."""
        if index == -1:
            return
        selected_model_data = self.model_combo.itemData(index)
        if not selected_model_data:
            if self.logger:
                self.logger.warning(f"No model data found for dropdown index {index}")
            return
        model_name = selected_model_data['name']
        if self.logger:
            self.logger.info(f"User selected model: {model_name}")
        
        # Emit signal for external handling
        self.model_selection_changed.emit(model_name)
        
        # Load the selected model
        self.load_model(model_name)
    
    def load_model(self, model_name: str):
        """Load a Whisper model in a background thread."""
        print(f"DEBUG: ModelManagerUI.load_model called with model_name: {model_name}")
        if self.logger:
            self.logger.info(f"Request to load model: {model_name}")
        else:
            print(f"DEBUG: No logger available in ModelManagerUI")
        
        # Check memory requirements
        base_model_name = model_name.split('.')[0]
        required_memory = MODEL_MEMORY_REQ.get(base_model_name, 1 * 1024**3)
        available_memory = psutil.virtual_memory().available

        print(f"DEBUG: Memory check - required: {required_memory / 1024**3:.1f}GB, available: {available_memory / 1024**3:.1f}GB")

        if self.logger:
            self.logger.debug(f"Memory check for model '{model_name}': required={required_memory / 1024**3:.1f}GB, available={available_memory / 1024**3:.1f}GB")

        if available_memory < required_memory:
            msg = f"Not enough memory to load model '{model_name}'.\n" \
                  f"Required: {required_memory / 1024**3:.1f} GB\n" \
                  f"Available: {available_memory / 1024**3:.1f} GB"
            QMessageBox.warning(None, "Memory Error", msg)
            
            if self.logger:
                self.logger.warning(f"Insufficient memory to load model '{model_name}'")
            return

        print(f"DEBUG: Memory check passed, creating worker thread")
        if self.logger:
            self.logger.info(f"Starting model load for: {model_name}")
        
        # Create worker thread
        thread = QThread()
        old_model_tuple = self.whisper_model if self.whisper_model else None
        worker = ModelLoadWorker(model_name, old_model_tuple, self.config_manager)
        worker.moveToThread(thread)
        
        print(f"DEBUG: Worker thread created")
        if self.logger:
            self.logger.info(f"Thread and worker created, setting up connections")
        
        # Set up connections
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_model_load_finished)
        worker.error.connect(self._on_model_load_error)
        
        # Store thread reference
        self.load_threads.append(thread)
        self.load_workers.append(worker)  # Keep a reference to the worker
        
        # Clean up when finished
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._remove_load_thread(thread))
        worker.finished.connect(lambda: self._remove_load_worker(worker))  # Clean up worker
        
        print(f"DEBUG: Starting thread")
        if self.logger:
            self.logger.info(f"Starting thread")
        
        thread.start()
        
        print(f"DEBUG: Thread started - isRunning: {thread.isRunning()}, isFinished: {thread.isFinished()}")
        if self.logger:
            self.logger.info(f"Thread started successfully")
            self.logger.info(f"Thread isRunning: {thread.isRunning()}")
            self.logger.info(f"Thread isFinished: {thread.isFinished()}")
    
    def _on_model_load_finished(self, model_tuple):
        """Handle successful model loading."""
        if self.logger:
            self.logger.info("_on_model_load_finished: Received finished signal from worker")
        self.whisper_model = model_tuple  # model_tuple is (model, model_name)
        
        model_name = model_tuple[1]
        if self.logger:
            self.logger.info(f"Successfully loaded model: {model_name}")
        
        # Emit signal for external handling
        self.model_loaded.emit(model_tuple)
        
        # Clean up threads
        if self.logger:
            self.logger.info(f"_on_model_load_finished: Manual cleanup - threads before: {len(self.load_threads)}")
        
        finished_threads = [thread for thread in self.load_threads if thread.isFinished()]
        for thread in finished_threads:
            if self.logger:
                self.logger.info(f"_on_model_load_finished: Removing finished thread manually")
            self._remove_load_thread(thread)
        
        if self.logger:
            self.logger.info(f"_on_model_load_finished: Manual cleanup - threads after: {len(self.load_threads)}")

    def _on_model_load_error(self, error_message):
        """Handle model loading errors."""
        if self.logger:
            self.logger.error(f"Failed to load model: {error_message}")
        
        # Emit signal for external handling
        self.model_load_error.emit(error_message)
    
    def _remove_load_thread(self, thread):
        """Remove a finished thread from the list."""
        if self.logger:
            self.logger.info(f"_remove_load_thread: Attempting to remove thread from list (list size: {len(self.load_threads)})")
        
        if thread in self.load_threads:
            self.load_threads.remove(thread)
            if self.logger:
                self.logger.info(f"_remove_load_thread: Successfully removed thread from list (new size: {len(self.load_threads)})")
        else:
            if self.logger:
                self.logger.warning(f"_remove_load_thread: Thread not found in list")
    
    def _remove_load_worker(self, worker):
        if worker in self.load_workers:
            self.load_workers.remove(worker)
            if self.logger:
                self.logger.info(f"_remove_load_worker: Successfully removed worker from list (new size: {len(self.load_workers)})")
        else:
            if self.logger:
                self.logger.warning(f"_remove_load_worker: Worker not found in list")
    
    def get_current_model(self) -> Optional[Tuple]:
        """Get the currently loaded model."""
        return self.whisper_model
    
    def set_model_loading_state(self, loading: bool):
        """Update UI state for model loading."""
        self.model_combo.setEnabled(not loading)
        if loading:
            self.model_combo.setToolTip("Loading model...")
        else:
            self.model_combo.setToolTip("Select transcription model") 