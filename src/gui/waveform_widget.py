"""
Waveform visualization widget for W4L.

Provides real-time audio waveform display using PyQtGraph.
"""

import numpy as np
import logging
from typing import Optional, List
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPen, QBrush

import pyqtgraph as pg

# Configure pyqtgraph to use PyQt6
pg.setConfigOption('imageAxisOrder', 'row-major')


class WaveformWidget(QWidget):
    """
    Real-time waveform visualization widget.
    
    Features:
    - Real-time audio waveform display
    - Flatline display when not recording
    - Configurable colors and scaling
    - Smooth updates during recording
    """
    
    # Signals
    waveform_clicked = pyqtSignal()  # Emitted when waveform is clicked
    
    def __init__(self, parent=None):
        """
        Initialize the waveform widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger("w4l.gui.waveform_widget")
        
        # Widget state
        self.is_recording = False
        self.gain = 5.0  # Visual amplification factor
        
        # Audio data
        self.max_points = 16000 * 2 # Display 2 seconds of audio
        self.sample_rate = 16000     # Audio sample rate
        self.plot_data = np.zeros(self.max_points, dtype=np.float32)
        
        # Initialize UI
        self._setup_plot()
        self._setup_styling()
        self._show_flatline()
        
        self.logger.info("Waveform widget initialized")
    
    def _setup_plot(self):
        """Set up the PyQtGraph plot widget."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')  # White background
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Time')
        
        # Configure plot properties
        self.plot_widget.setMouseEnabled(x=False, y=False)  # Disable mouse interaction
        self.plot_widget.setMenuEnabled(False)  # Disable context menu
        self.plot_widget.hideButtons()  # Hide axis buttons
        
        # Create plot item for waveform
        self.plot_item = self.plot_widget.plot(pen=pg.mkPen(color=(46, 204, 113), width=2))  # Green line
        
        # Add to layout
        layout.addWidget(self.plot_widget)
    
    def _setup_styling(self):
        """Set up the styling for the plot."""
        # Set plot colors
        self.plot_widget.setBackground(QColor(52, 73, 94))  # Dark blue-gray background
        
        # Grid styling
        self.plot_widget.getAxis('left').setPen(QPen(QColor(189, 195, 199), 1))
        self.plot_widget.getAxis('bottom').setPen(QPen(QColor(189, 195, 199), 1))
        
        # Label styling
        self.plot_widget.getAxis('left').setTextPen(QColor(236, 240, 241))
        self.plot_widget.getAxis('bottom').setTextPen(QColor(236, 240, 241))
        
        # Set axis ranges
        self.plot_widget.setYRange(-1, 1)
        self.plot_widget.setXRange(0, self.max_points / self.sample_rate if self.sample_rate > 0 else 1)
    
    def _show_flatline(self):
        """Show flatline display when not recording."""
        flatline_data = np.zeros(self.max_points)
        self.plot_item.setData(flatline_data)
        self.plot_widget.setTitle("Ready", color=(189, 195, 199))
    
    def update_waveform(self, new_chunk: np.ndarray):
        """
        Update the waveform display with a new chunk of audio data.
        This method is designed to be called directly from the audio recorder's callback.
        """
        if not self.is_recording:
            return

        # Normalize the int16 chunk to float data between -1.0 and 1.0
        normalized_chunk = new_chunk.astype(np.float32) / 32768.0
        
        # Apply visual gain and compression using tanh
        amplified_chunk = np.tanh(normalized_chunk * self.gain)
        
        # Flatten the chunk to 1D array
        flat_chunk = amplified_chunk.flatten()
        chunk_len = len(flat_chunk)
        
        if chunk_len > 0:
            # Use numpy roll to shift data and append new chunk
            self.plot_data = np.roll(self.plot_data, -chunk_len)
            self.plot_data[-chunk_len:] = flat_chunk
            
            # Update the plot with new data
            self.plot_item.setData(y=self.plot_data)

    def start_recording(self):
        """Start recording mode."""
        self.is_recording = True
        self.plot_data = np.zeros(self.max_points, dtype=np.float32) # Clear buffer
        
        # Update styling for recording mode
        self.plot_widget.setTitle("Recording...", color=(236, 240, 241))
        
        self.logger.info("Waveform widget started recording mode")
    
    def stop_recording(self):
        """Stop recording mode."""
        self.is_recording = False
        
        # Reset to flatline
        self._show_flatline()
        
        self.logger.info("Waveform widget stopped recording mode")
    
    def clear_audio_data(self):
        """Clear the audio data and show flatline."""
        self.plot_data = np.zeros(self.max_points, dtype=np.float32)
        self._show_flatline()
    
    def set_sample_rate(self, sample_rate: int):
        """
        Set the audio sample rate.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        if self.sample_rate > 0:
            self.plot_widget.setXRange(0, self.max_points / self.sample_rate)
        self.logger.debug(f"Sample rate set to {sample_rate} Hz")
    
    def set_max_points(self, max_points: int):
        """
        Set the maximum number of points to display.
        
        Args:
            max_points: Maximum number of points
        """
        self.max_points = max_points
        if self.sample_rate > 0:
            self.plot_widget.setXRange(0, self.max_points / self.sample_rate)
        self.logger.debug(f"Max points set to {max_points}")
    
    def get_widget(self) -> pg.PlotWidget:
        """
        Get the underlying PyQtGraph plot widget.
        
        This can be used to further customize the plot appearance or
        to embed it in other layouts.
        """
        return self.plot_widget

    def resizeEvent(self, event):
        """Handle widget resize event."""
        super().resizeEvent(event)
        self.logger.debug(f"Waveform widget resized to {event.size().width()}x{event.size().height()}")
        # Ensure the plot widget fills the available space
        self.plot_widget.setGeometry(0, 0, self.width(), self.height()) 