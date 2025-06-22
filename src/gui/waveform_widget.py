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
        self.is_flatline = True
        
        # Audio data
        self.audio_data = np.array([])
        self.max_points = 1000  # Number of points to display
        self.sample_rate = 16000  # Audio sample rate
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_interval = 50  # 20 FPS (50ms)
        
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
        self.plot_item = self.plot_widget.plot(pen=None)
        
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
        self.is_flatline = True
        
        # Create flatline data
        time_data = np.linspace(0, self.max_points / self.sample_rate if self.sample_rate > 0 else 1, self.max_points)
        flatline_data = np.zeros(self.max_points)
        
        # Update plot
        self.plot_item.setData(time_data, flatline_data, pen=pg.mkPen(color=(189, 195, 199), width=2))
        
        # Update labels
        self.plot_widget.setTitle("No Audio Input", color=(189, 195, 199))
    
    def _show_waveform(self, audio_data: np.ndarray):
        """Show waveform display with audio data."""
        self.is_flatline = False
        
        if len(audio_data) == 0:
            self._show_flatline()
            return
        
        # Normalize audio data
        max_abs = np.max(np.abs(audio_data))
        if max_abs > 0:
            normalized_data = audio_data / max_abs
        else:
            normalized_data = audio_data
        
        # Create time axis
        time_data = np.linspace(0, len(normalized_data) / self.sample_rate if self.sample_rate > 0 else 1, len(normalized_data))
        
        # Update plot with new data
        self.plot_item.setData(time_data, normalized_data, pen=pg.mkPen(color=(52, 152, 219), width=2))
        
        # Update title
        self.plot_widget.setTitle("Audio Waveform", color=(52, 152, 219))
    
    def _update_display(self):
        """Update the waveform display with current audio data."""
        if not self.is_recording or len(self.audio_data) == 0:
            return
        
        # Get the latest audio data
        latest_data = self._get_latest_audio_data()
        self._show_waveform(latest_data)
    
    def _get_latest_audio_data(self) -> np.ndarray:
        """Get the latest audio data for display."""
        if len(self.audio_data) == 0:
            return np.array([])
        
        # Get the most recent data points
        if len(self.audio_data) > self.max_points:
            return self.audio_data[-self.max_points:]
        else:
            return self.audio_data
    
    def start_recording(self):
        """Start recording mode."""
        self.is_recording = True
        self.is_flatline = False
        
        # Start update timer
        self.update_timer.start(self.update_interval)
        
        # Update styling for recording mode
        self.plot_widget.setBackground(QColor(231, 76, 60))  # Red background for recording
        self.plot_widget.setTitle("Recording...", color=(236, 240, 241))
        
        self.logger.info("Waveform widget started recording mode")
    
    def stop_recording(self):
        """Stop recording mode."""
        self.is_recording = False
        
        # Stop update timer
        self.update_timer.stop()
        
        # Reset to flatline
        self._show_flatline()
        
        # Reset background
        self.plot_widget.setBackground(QColor(52, 73, 94))
        
        self.logger.info("Waveform widget stopped recording mode")
    
    def update_audio_data(self, audio_data: np.ndarray):
        """
        Update the audio data for display.
        
        Args:
            audio_data: New audio data as numpy array
        """
        self.audio_data = audio_data.copy()
        
        # If not recording, show static waveform
        if not self.is_recording and len(audio_data) > 0:
            self._show_waveform(audio_data)
    
    def clear_audio_data(self):
        """Clear the audio data and show flatline."""
        self.audio_data = np.array([])
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
    
    def set_update_interval(self, interval_ms: int):
        """
        Set the update interval for real-time display.
        
        Args:
            interval_ms: Update interval in milliseconds
        """
        self.update_interval = interval_ms
        if self.update_timer.isActive():
            self.update_timer.start(interval_ms)
        self.logger.debug(f"Update interval set to {interval_ms} ms")
    
    def get_widget(self) -> pg.PlotWidget:
        """
        Get the underlying PyQtGraph plot widget.
        
        Returns:
            PyQtGraph plot widget
        """
        return self.plot_widget
    
    def resizeEvent(self, event):
        """Handle widget resize events."""
        super().resizeEvent(event)
        # Ensure the plot widget fills the available space
        self.plot_widget.setGeometry(0, 0, self.width(), self.height()) 