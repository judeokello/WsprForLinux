# Memory Management and Cleanup

## Overview

The W4L audio system includes comprehensive memory management and cleanup functionality to ensure efficient resource usage and prevent memory leaks. This system is designed to work with both streaming and file-based audio capture modes.

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    W4L Audio System                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              buffer_manager.py                      │   │
│  │  (Audio-specific buffer management)                 │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │        StreamingAudioManager               │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │         AudioBuffer                 │   │   │   │
│  │  │  │  ┌─────────────────────────────┐   │   │   │   │
│  │  │  │  │    AudioBufferTracker       │   │   │   │   │
│  │  │  │  └─────────────────────────────┘   │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │        ResourceManager             │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │      FileBasedAudioManager                 │   │   │
│  │  │  ┌─────────────────────────────────────┐   │   │   │
│  │  │  │        ResourceManager             │   │   │   │
│  │  │  └─────────────────────────────────────┘   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                             │
│                              ▼                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              memory_manager.py                      │   │
│  │  (Core memory management infrastructure)            │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │           MemoryMonitor                     │   │   │
│  │  │  • Memory usage tracking                    │   │   │
│  │  │  • Cleanup triggers                         │   │   │
│  │  │  • Background monitoring                    │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │          ResourceManager                    │   │   │
│  │  │  • Temporary file cleanup                   │   │   │
│  │  │  • Weak reference tracking                  │   │   │
│  │  │  • Cleanup callbacks                        │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │        AudioBufferTracker                   │   │   │
│  │  │  • Buffer memory tracking                   │   │   │
│  │  │  • Buffer cleanup optimization              │   │   │
│  │  │  • Memory usage statistics                  │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 **Data Flow Example**

```
Audio Input → StreamingAudioManager → AudioBuffer → AudioBufferTracker
     ↓              ↓                    ↓              ↓
Microphone    Audio Callback      Circular Buffer   Memory Tracking
     ↓              ↓                    ↓              ↓
sounddevice   Queue Processing    Data Storage     Cleanup Triggers
     ↓              ↓                    ↓              ↓
Real-time     Memory Monitor      ResourceManager   Garbage Collection
```

## 📊 **Memory Usage Timeline**

```
Memory Usage (MB)
    │
 512│    ████████████████████████████████████████████████████████████████
    │    █  Memory Threshold (512MB)  █
    │    ████████████████████████████████████████████████████████████████
 400│    ████████████████████████████████████████████████████████████████
    │    █  Audio Buffer (200MB)      █
 300│    ████████████████████████████████████████████████████████████████
    │    █  System Overhead (100MB)   █
 200│    ████████████████████████████████████████████████████████████████
    │    █  Application Base (100MB)  █
 100│    ████████████████████████████████████████████████████████████████
    │    █  Python Runtime (100MB)    █
   0│    ████████████████████████████████████████████████████████████████
    └─────────────────────────────────────────────────────────────────────
     0s    5s    10s   15s   20s   25s   30s   35s   40s   45s   50s
                    Recording Duration
```

## Components

### 1. MemoryMonitor

The `MemoryMonitor` class provides real-time memory usage tracking and automatic cleanup triggers.

**Features:**
- Real-time memory usage monitoring using `psutil`
- Configurable memory thresholds (default: 512MB)
- Automatic cleanup callbacks
- Background monitoring with configurable intervals
- Memory usage statistics

**Usage:**
```python
from audio.memory_manager import MemoryMonitor

# Create monitor with 200MB threshold
monitor = MemoryMonitor(max_memory_mb=200)

# Get current memory usage
usage = monitor.get_memory_usage()  # Returns MB

# Check if memory usage is high
if monitor.is_memory_high():
    monitor.cleanup()

# Add cleanup callback
def my_cleanup():
    # Custom cleanup logic
    pass

monitor.add_cleanup_callback(my_cleanup)

# Start automatic monitoring
monitor.start_monitoring(interval_seconds=30.0)
```

### 2. ResourceManager

The `ResourceManager` class handles temporary file cleanup and resource tracking.

**Features:**
- Temporary file management and cleanup
- Weak reference tracking
- Cleanup callback system
- Resource usage statistics

**Usage:**
```python
from audio.memory_manager import ResourceManager

resource_mgr = ResourceManager(monitor)

# Add temporary file for cleanup
resource_mgr.add_temp_file("/tmp/audio_123.wav")

# Add cleanup callback
def cleanup_audio():
    # Clean up audio resources
    pass

resource_mgr.add_cleanup_callback(cleanup_audio)

# Get resource information
info = resource_mgr.get_resource_info()
```

### 3. AudioBufferTracker

The `AudioBufferTracker` class specifically tracks audio buffer memory usage.

**Features:**
- Audio buffer memory tracking
- Automatic buffer cleanup when memory is high
- Buffer statistics and reporting
- Memory usage optimization

**Usage:**
```python
from audio.memory_manager import AudioBufferTracker

tracker = AudioBufferTracker(monitor)

# Track a buffer
import numpy as np
buffer_data = np.zeros((16000, 1), dtype=np.float32)
tracker.track_buffer(buffer_data, buffer_data.nbytes)

# Get buffer statistics
info = tracker.get_buffer_info()
print(f"Total buffer memory: {info['total_memory_mb']:.1f}MB")

# Untrack when done
tracker.untrack_buffer(buffer_data)
```

## Integration with Audio Buffer System

### Enhanced AudioBuffer

The `AudioBuffer` class has been enhanced with memory tracking:

```python
from audio.buffer_manager import AudioBuffer
from audio.memory_manager import AudioBufferTracker

tracker = AudioBufferTracker(monitor)

# Create buffer with tracking
buffer = AudioBuffer(
    max_samples=16000 * 5,  # 5 seconds at 16kHz
    channels=1,
    dtype=np.float32,
    buffer_tracker=tracker
)

# Buffer is automatically tracked
# When cleanup is needed, tracker will handle it
```

### Streaming Audio Manager

The `StreamingAudioManager` includes comprehensive memory management:

```python
from audio.buffer_manager import StreamingAudioManager

# Create with memory monitoring
streaming_mgr = StreamingAudioManager(device_manager, monitor)

# Memory is automatically monitored during recording
streaming_mgr.start_recording()

# Get memory information
info = streaming_mgr.get_buffer_info()
print(f"Memory usage: {info['memory_usage_mb']:.1f}MB")
print(f"Buffer fill level: {info['fill_level']:.1%}")

# Cleanup is automatic, but can be forced
streaming_mgr.cleanup()
```

### File-Based Audio Manager

The `FileBasedAudioManager` handles temporary file cleanup:

```python
from audio.buffer_manager import FileBasedAudioManager

# Create with memory monitoring
file_mgr = FileBasedAudioManager(device_manager, monitor)

# Temporary files are automatically tracked and cleaned up
file_mgr.start_recording()

# Files are cleaned up when manager is destroyed
file_mgr.cleanup()
```

## 🔧 **Real-World Usage Examples**

### **Scenario 1: Streaming Audio Recording**
```python
# 1. Create memory monitor
monitor = MemoryMonitor(max_memory_mb=200)

# 2. Create buffer manager (uses memory monitor)
buffer_mgr = AudioBufferManager(device_mgr, monitor)

# 3. Start recording
buffer_mgr.start_recording()

# 4. Memory is automatically monitored and cleaned up
# - AudioBufferTracker tracks buffer memory
# - ResourceManager handles any temporary files
# - MemoryMonitor triggers cleanup when needed
```

### **Scenario 2: File-Based Recording**
```python
# Same setup, but different behavior
buffer_mgr.set_capture_mode(False)  # Switch to file-based
buffer_mgr.start_recording()

# Now:
# - ResourceManager tracks the temporary WAV file
# - MemoryMonitor ensures the file is cleaned up
# - No buffer tracking (since it's file-based)
```

## 🔄 **Detailed Data Flow Example**

Let me show you how data flows through the system:

```python
# 1. Audio data comes in
audio_data = np.random.randn(16000, 1)  # 1 second of audio

# 2. StreamingAudioManager receives it
streaming_mgr._audio_callback(audio_data, ...)

# 3. Data goes to AudioBuffer
buffer.write(audio_data)

# 4. AudioBufferTracker monitors memory usage
# If memory gets high, it triggers cleanup

# 5. MemoryMonitor coordinates cleanup
monitor.cleanup()
# This calls:
# - ResourceManager.cleanup() (cleans temp files)
# - AudioBufferTracker._cleanup_buffers() (clears old buffers)
# - gc.collect() (garbage collection)
```

## 🎛️ **Configuration and Control**

### **Memory Limits**
```python
# Set memory threshold
monitor = MemoryMonitor(max_memory_mb=512)

# Monitor automatically triggers cleanup when usage > 512MB
```

### **Buffer Tracking**
```python
# Track specific buffers
tracker.track_buffer(buffer_obj, size_bytes=1024000)  # 1MB buffer

# Get statistics
info = tracker.get_buffer_info()
# Returns: {'buffer_count': 5, 'total_memory_mb': 5.0, ...}
```

### **Resource Management**
```python
# Add temporary files for cleanup
resource_mgr.add_temp_file("/tmp/audio_123.wav")

# Add custom cleanup callbacks
def my_cleanup():
    # Custom cleanup logic
    pass
resource_mgr.add_cleanup_callback(my_cleanup)
```

## 🎯 **Benefits of This Architecture**

### **1. Separation of Concerns**
- `memory_manager.py`: Generic memory management (could be used by other parts of W4L)
- `buffer_manager.py`: Audio-specific buffer management

### **2. Reusability**
- Memory management components can be used by other systems
- Audio buffer management is focused on audio-specific needs

### **3. Flexibility**
- Easy to switch between streaming and file-based modes
- Memory limits can be adjusted per use case
- Cleanup strategies can be customized

### **4. Reliability**
- Automatic cleanup prevents memory leaks
- Resource tracking ensures temporary files are removed
- Buffer overflow protection

## 🔮 **Future Usage**

This architecture will be particularly important when we add:

1. **GUI Integration**: Memory monitoring can show usage in the UI
2. **Whisper Model Loading**: Large models will need memory management
3. **Real-time Transcription**: Continuous audio processing needs efficient memory usage
4. **Multiple Audio Sources**: Managing multiple buffers simultaneously

## 🚨 **Memory Threshold Considerations**

### **Current Default: 512MB**
```python
monitor = MemoryMonitor(max_memory_mb=512)
```

### **Whisper Model Memory Requirements:**
```
Model Size    | Memory Usage | Status with 512MB limit
--------------|--------------|------------------------
tiny          | ~150MB       | ✅ OK
base          | ~250MB       | ✅ OK  
small         | ~500MB       | ⚠️ Borderline
medium        | ~1.5GB       | ❌ Will trigger cleanup
large         | ~2.5GB       | ❌ Will trigger cleanup
```

### **Future Enhancement (Phase 4.4.5)**
```python
# Model-aware memory management
class W4LMemoryManager:
    def __init__(self):
        self.model_memory_mb = 0
        self.memory_monitor = None
    
    def set_model(self, model_name: str):
        # Adjust memory threshold based on model size
        model_requirements = {
            "tiny": 150, "base": 250, "small": 500,
            "medium": 1500, "large": 2500
        }
        required_memory = model_requirements[model_name]
        total_threshold = required_memory + 512  # Model + buffer overhead
        self.memory_monitor = MemoryMonitor(max_memory_mb=total_threshold)
```

## Memory Management Features

### 1. Automatic Cleanup

- **Memory Thresholds**: Automatic cleanup when memory usage exceeds configured limits
- **Buffer Overflow Protection**: Prevents memory exhaustion from large audio buffers
- **Temporary File Cleanup**: Automatically removes temporary audio files
- **Resource Tracking**: Monitors and cleans up weak references

### 2. Manual Cleanup

- **Explicit Cleanup**: Call `cleanup()` methods to force resource cleanup
- **Destructor Support**: Automatic cleanup when objects are destroyed
- **Context Manager Support**: Safe cleanup with `with` statements

### 3. Memory Monitoring

- **Real-time Tracking**: Continuous memory usage monitoring
- **Statistics Reporting**: Detailed memory usage information
- **Performance Metrics**: Buffer efficiency and memory utilization stats

### 4. Resource Optimization

- **Buffer Reuse**: Efficient buffer management to reduce allocations
- **Memory Pooling**: Reuse memory blocks where possible
- **Garbage Collection**: Automatic garbage collection triggers

## Configuration

### Memory Limits

Configure memory limits in the settings:

```python
# Default memory limits
DEFAULT_MEMORY_LIMIT_MB = 512
DEFAULT_BUFFER_MEMORY_LIMIT_MB = 100

# Audio buffer limits
MAX_BUFFER_SIZE_SECONDS = 30
MIN_BUFFER_SIZE_SECONDS = 1
```

### Cleanup Intervals

Configure cleanup monitoring intervals:

```python
# Memory monitoring intervals
MEMORY_CHECK_INTERVAL_SECONDS = 30
BUFFER_CLEANUP_INTERVAL_SECONDS = 60
```

## Testing

The memory management system includes comprehensive testing:

```bash
# Run memory management tests
python scripts/test_memory_management.py
```

**Test Coverage:**
- Memory monitor functionality
- Resource manager cleanup
- Buffer tracking and optimization
- Integration with audio managers
- Memory leak detection

## Best Practices

### 1. Resource Management

- Always call `cleanup()` when done with audio managers
- Use context managers for automatic cleanup
- Monitor memory usage in long-running applications

### 2. Buffer Management

- Set appropriate buffer sizes for your use case
- Monitor buffer fill levels to prevent overflow
- Use streaming mode for real-time applications

### 3. File Management

- Temporary files are automatically cleaned up
- Don't manually delete files managed by the system
- Use the resource manager for custom temporary files

### 4. Memory Monitoring

- Set appropriate memory thresholds for your system
- Monitor memory usage patterns
- Adjust cleanup intervals based on usage

## Troubleshooting

### High Memory Usage

If you experience high memory usage:

1. Check buffer sizes and reduce if necessary
2. Monitor buffer fill levels
3. Increase cleanup frequency
4. Check for memory leaks in custom code

### Cleanup Issues

If cleanup isn't working properly:

1. Verify cleanup callbacks are registered
2. Check memory monitor configuration
3. Ensure proper object destruction
4. Review resource manager setup

### Performance Issues

If performance is affected:

1. Adjust memory monitoring intervals
2. Optimize buffer sizes
3. Review cleanup frequency
4. Monitor system resources

## Future Enhancements

### Planned Features

1. **Memory Pooling**: Advanced memory pool management
2. **Predictive Cleanup**: AI-based cleanup prediction
3. **Memory Compression**: Audio data compression
4. **Distributed Memory**: Multi-process memory management

### Optimization Opportunities

1. **Buffer Pre-allocation**: Pre-allocate buffers for better performance
2. **Memory Mapping**: Use memory-mapped files for large buffers
3. **Cache Management**: Intelligent cache management
4. **Background Cleanup**: Asynchronous cleanup processes 