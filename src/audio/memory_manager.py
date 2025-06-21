"""
Memory management utilities for W4L audio system.

Provides memory monitoring, cleanup, and resource management for audio buffers.
"""

import gc
import psutil
import os
import threading
import time
import logging
from typing import List, Callable, Optional
import weakref
from pathlib import Path


class MemoryMonitor:
    """Monitors memory usage and provides cleanup utilities."""
    
    def __init__(self, max_memory_mb: int = 512):
        """
        Initialize memory monitor.
        
        Args:
            max_memory_mb: Maximum memory usage in MB before cleanup
        """
        self.logger = logging.getLogger("w4l.audio.memory_monitor")
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()
        self._cleanup_callbacks: List[Callable] = []
        self._monitoring = False
        self._monitor_thread = None
        
    def get_memory_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in MB
        """
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except Exception as e:
            self.logger.warning(f"Could not get memory usage: {e}")
            return 0.0
    
    def is_memory_high(self) -> bool:
        """
        Check if memory usage is above threshold.
        
        Returns:
            True if memory usage is high
        """
        return self.get_memory_usage() > self.max_memory_mb
    
    def add_cleanup_callback(self, callback: Callable) -> None:
        """
        Add a cleanup callback function.
        
        Args:
            callback: Function to call during cleanup
        """
        self._cleanup_callbacks.append(callback)
    
    def remove_cleanup_callback(self, callback: Callable) -> None:
        """
        Remove a cleanup callback function.
        
        Args:
            callback: Function to remove
        """
        if callback in self._cleanup_callbacks:
            self._cleanup_callbacks.remove(callback)
    
    def cleanup(self, force: bool = False) -> None:
        """
        Perform memory cleanup.
        
        Args:
            force: Force cleanup even if memory usage is not high
        """
        if not force and not self.is_memory_high():
            return
        
        self.logger.info(f"Performing memory cleanup. Current usage: {self.get_memory_usage():.1f}MB")
        
        # Call cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in cleanup callback: {e}")
        
        # Force garbage collection
        collected = gc.collect()
        self.logger.debug(f"Garbage collection freed {collected} objects")
        
        # Log final memory usage
        final_usage = self.get_memory_usage()
        self.logger.info(f"Cleanup complete. Memory usage: {final_usage:.1f}MB")
    
    def start_monitoring(self, interval_seconds: float = 30.0) -> None:
        """
        Start automatic memory monitoring.
        
        Args:
            interval_seconds: Check interval in seconds
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info(f"Started memory monitoring (check every {interval_seconds}s)")
    
    def stop_monitoring(self) -> None:
        """Stop automatic memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        self.logger.info("Stopped memory monitoring")
    
    def _monitor_loop(self, interval_seconds: float) -> None:
        """Memory monitoring loop."""
        while self._monitoring:
            try:
                if self.is_memory_high():
                    self.cleanup()
                time.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in memory monitoring: {e}")
                time.sleep(interval_seconds)


class ResourceManager:
    """Manages audio resources and cleanup."""
    
    def __init__(self, memory_monitor: Optional[MemoryMonitor] = None):
        """
        Initialize resource manager.
        
        Args:
            memory_monitor: Optional memory monitor for cleanup
        """
        self.logger = logging.getLogger("w4l.audio.resource_manager")
        self.memory_monitor = memory_monitor or MemoryMonitor()
        self._temp_files: List[str] = []
        self._weak_refs: List[weakref.ref] = []
        self._cleanup_callbacks: List[Callable] = []
        
        # Register with memory monitor
        self.memory_monitor.add_cleanup_callback(self.cleanup)
    
    def add_temp_file(self, file_path: str) -> None:
        """
        Add a temporary file for cleanup.
        
        Args:
            file_path: Path to temporary file
        """
        self._temp_files.append(file_path)
        self.logger.debug(f"Added temp file for cleanup: {file_path}")
    
    def remove_temp_file(self, file_path: str) -> None:
        """
        Remove a temporary file from cleanup list.
        
        Args:
            file_path: Path to temporary file
        """
        if file_path in self._temp_files:
            self._temp_files.remove(file_path)
            self.logger.debug(f"Removed temp file from cleanup: {file_path}")
    
    def add_weak_ref(self, obj: object) -> None:
        """
        Add a weak reference for cleanup tracking.
        
        Args:
            obj: Object to track
        """
        self._weak_refs.append(weakref.ref(obj))
    
    def add_cleanup_callback(self, callback: Callable) -> None:
        """
        Add a cleanup callback.
        
        Args:
            callback: Function to call during cleanup
        """
        self._cleanup_callbacks.append(callback)
    
    def cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        for temp_file in self._temp_files[:]:  # Copy list to avoid modification during iteration
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self._temp_files.remove(temp_file)
                    self.logger.debug(f"Removed temporary file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Could not remove temporary file {temp_file}: {e}")
    
    def cleanup_weak_refs(self) -> None:
        """Clean up weak references."""
        # Remove dead references
        self._weak_refs = [ref for ref in self._weak_refs if ref() is not None]
    
    def cleanup(self) -> None:
        """Perform complete cleanup."""
        self.logger.debug("Starting resource cleanup")
        
        # Call cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in cleanup callback: {e}")
        
        # Clean up temporary files
        self.cleanup_temp_files()
        
        # Clean up weak references
        self.cleanup_weak_refs()
        
        self.logger.debug("Resource cleanup complete")
    
    def get_resource_info(self) -> dict:
        """
        Get information about managed resources.
        
        Returns:
            Dictionary with resource information
        """
        return {
            "temp_files_count": len(self._temp_files),
            "weak_refs_count": len(self._weak_refs),
            "cleanup_callbacks_count": len(self._cleanup_callbacks),
            "memory_usage_mb": self.memory_monitor.get_memory_usage(),
            "memory_limit_mb": self.memory_monitor.max_memory_mb
        }


class AudioBufferTracker:
    """Tracks audio buffer memory usage and provides cleanup."""
    
    def __init__(self, memory_monitor: Optional[MemoryMonitor] = None):
        """
        Initialize audio buffer tracker.
        
        Args:
            memory_monitor: Optional memory monitor for cleanup
        """
        self.logger = logging.getLogger("w4l.audio.buffer_tracker")
        self.memory_monitor = memory_monitor or MemoryMonitor()
        self._buffers: List[object] = []
        self._buffer_sizes: List[int] = []
        
        # Register with memory monitor
        self.memory_monitor.add_cleanup_callback(self._cleanup_buffers)
    
    def track_buffer(self, buffer_obj: object, size_bytes: int) -> None:
        """
        Track an audio buffer.
        
        Args:
            buffer_obj: Buffer object to track
            size_bytes: Size of buffer in bytes
        """
        self._buffers.append(buffer_obj)
        self._buffer_sizes.append(size_bytes)
        self.logger.debug(f"Tracking buffer: {size_bytes / 1024:.1f}KB")
    
    def untrack_buffer(self, buffer_obj: object) -> None:
        """
        Stop tracking an audio buffer.
        
        Args:
            buffer_obj: Buffer object to untrack
        """
        if buffer_obj in self._buffers:
            index = self._buffers.index(buffer_obj)
            self._buffers.pop(index)
            self._buffer_sizes.pop(index)
            self.logger.debug("Stopped tracking buffer")
    
    def get_total_buffer_memory(self) -> int:
        """
        Get total memory used by tracked buffers.
        
        Returns:
            Total memory in bytes
        """
        return sum(self._buffer_sizes)
    
    def _cleanup_buffers(self) -> None:
        """Clean up buffers when memory is high."""
        total_memory = self.get_total_buffer_memory()
        if total_memory > 100 * 1024 * 1024:  # 100MB threshold
            self.logger.info(f"Buffer memory high ({total_memory / 1024 / 1024:.1f}MB), clearing old buffers")
            
            # Clear half of the buffers (oldest first)
            buffers_to_remove = len(self._buffers) // 2
            for i in range(buffers_to_remove):
                if self._buffers:
                    self._buffers.pop(0)
                    self._buffer_sizes.pop(0)
    
    def get_buffer_info(self) -> dict:
        """
        Get information about tracked buffers.
        
        Returns:
            Dictionary with buffer information
        """
        return {
            "buffer_count": len(self._buffers),
            "total_memory_bytes": self.get_total_buffer_memory(),
            "total_memory_mb": self.get_total_buffer_memory() / 1024 / 1024,
            "average_buffer_size_kb": sum(self._buffer_sizes) / max(len(self._buffer_sizes), 1) / 1024
        } 