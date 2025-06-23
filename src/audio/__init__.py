"""
Audio module for W4L.

Contains audio recording, processing, and silence detection components.
"""

# Audio components will be imported here as they are implemented
# from .recorder import AudioRecorder
# from .processor import AudioProcessor
from .silence_detector import SilenceDetector, SilenceConfig, DetectionStrategy

__all__ = [
    # 'AudioRecorder',
    # 'AudioProcessor',
    'SilenceDetector',
    'SilenceConfig',
    'DetectionStrategy'
] 