"""
GUI module for W4L.

Contains the main application window, settings dialog, and UI components.
"""

from .main_window import W4LMainWindow
# from .settings_dialog import W4LSettingsDialog  # Temporarily commented out
from .waveform_widget import WaveformWidget

__all__ = ['W4LMainWindow', 'WaveformWidget']  # Removed W4LSettingsDialog 