"""
UI Performance optimization utilities for ConsultEase.
Provides tools to reduce unnecessary re-renders and improve UI responsiveness.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable, List
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class UIUpdateBatcher(QObject):
    """
    Batches UI updates to reduce frequent re-renders.
    Collects multiple update requests and executes them in a single batch.
    """

    updates_ready = pyqtSignal()

    def __init__(self, batch_delay: int = 100):
        """
        Initialize the UI update batcher.

        Args:
            batch_delay: Delay in milliseconds before executing batched updates
        """
        super().__init__()
        self.batch_delay = batch_delay
        self.pending_updates: Dict[str, Callable] = {}
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._execute_batch)

    def schedule_update(self, update_id: str, update_func: Callable):
        """
        Schedule an update to be executed in the next batch.

        Args:
            update_id: Unique identifier for the update (overwrites previous with same ID)
            update_func: Function to execute for the update
        """
        self.pending_updates[update_id] = update_func

        # Restart the timer to batch multiple updates
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(self.batch_delay)

    def _execute_batch(self):
        """Execute all pending updates in a batch."""
        if not self.pending_updates:
            return

        logger.debug(f"Executing batch of {len(self.pending_updates)} UI updates")
        start_time = time.time()

        # Execute all pending updates
        for update_id, update_func in self.pending_updates.items():
            try:
                update_func()
            except Exception as e:
                logger.error(f"Error executing UI update {update_id}: {e}")

        # Clear pending updates
        self.pending_updates.clear()

        execution_time = (time.time() - start_time) * 1000
        logger.debug(f"Batch UI update completed in {execution_time:.2f}ms")

        # Emit signal that updates are ready
        self.updates_ready.emit()


class WidgetStateManager:
    """
    Manages widget state to prevent unnecessary updates.
    Tracks widget properties and only updates when values actually change.
    """

    def __init__(self):
        self.widget_states: Dict[int, Dict[str, Any]] = {}

    def should_update(self, widget: QWidget, property_name: str, new_value: Any) -> bool:
        """
        Check if a widget property should be updated.

        Args:
            widget: The widget to check
            property_name: Name of the property
            new_value: New value to set

        Returns:
            True if the property should be updated, False if it's already the same value
        """
        widget_id = id(widget)

        # Initialize widget state if not exists
        if widget_id not in self.widget_states:
            self.widget_states[widget_id] = {}

        current_value = self.widget_states[widget_id].get(property_name)

        # Check if value has changed
        if current_value != new_value:
            self.widget_states[widget_id][property_name] = new_value
            return True

        return False

    def update_property(self, widget: QWidget, property_name: str, new_value: Any,
                       update_func: Callable):
        """
        Update a widget property only if the value has changed.

        Args:
            widget: The widget to update
            property_name: Name of the property
            new_value: New value to set
            update_func: Function to call to update the property
        """
        if self.should_update(widget, property_name, new_value):
            update_func()

    def clear_widget_state(self, widget: QWidget):
        """Clear stored state for a widget (call when widget is destroyed)."""
        widget_id = id(widget)
        if widget_id in self.widget_states:
            del self.widget_states[widget_id]


class PerformanceMonitor:
    """
    Enhanced UI performance monitor with frame rate and memory tracking.
    Optimized for Raspberry Pi performance monitoring.
    """

    def __init__(self):
        self.update_times: List[float] = []
        self.frame_times: List[float] = []
        self.memory_usage: List[float] = []
        self.max_samples = 100
        self.warning_threshold = 100  # milliseconds
        self.critical_threshold = 200  # milliseconds
        self.target_frame_time = 33.33  # ~30 FPS target

        # Performance tracking
        self.last_frame_time = time.time()
        self.frame_count = 0
        self.fps_calculation_interval = 1.0  # seconds
        self.last_fps_calculation = time.time()
        self.current_fps = 0.0

    def record_update_time(self, update_time: float):
        """Record the time taken for a UI update."""
        self.update_times.append(update_time)

        # Keep only the last N samples
        if len(self.update_times) > self.max_samples:
            self.update_times.pop(0)

        # Log warnings for slow updates
        if update_time > self.critical_threshold:
            logger.warning(f"Critical UI update time: {update_time:.1f}ms")
        elif update_time > self.warning_threshold:
            logger.debug(f"Slow UI update time: {update_time:.1f}ms")

    def record_frame_time(self):
        """Record frame rendering time for FPS calculation."""
        current_time = time.time()
        frame_time = (current_time - self.last_frame_time) * 1000  # Convert to ms

        self.frame_times.append(frame_time)
        self.frame_count += 1

        # Keep only recent samples
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)

        # Calculate FPS periodically
        if current_time - self.last_fps_calculation >= self.fps_calculation_interval:
            if self.frame_count > 0:
                self.current_fps = self.frame_count / (current_time - self.last_fps_calculation)
                self.frame_count = 0
                self.last_fps_calculation = current_time

        self.last_frame_time = current_time

        # Log warnings for slow frames
        if frame_time > self.target_frame_time * 2:
            logger.debug(f"Slow frame time: {frame_time:.1f}ms (target: {self.target_frame_time:.1f}ms)")

    def record_memory_usage(self, memory_mb: float):
        """Record memory usage in megabytes."""
        self.memory_usage.append(memory_mb)

        # Keep only recent samples
        if len(self.memory_usage) > self.max_samples:
            self.memory_usage.pop(0)

    def get_average_update_time(self) -> float:
        """Get the average update time in milliseconds."""
        if not self.update_times:
            return 0.0
        return sum(self.update_times) / len(self.update_times)

    def get_current_fps(self) -> float:
        """Get current frames per second."""
        return self.current_fps

    def get_average_frame_time(self) -> float:
        """Get average frame time in milliseconds."""
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)

    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        if not self.memory_usage:
            return {'current': 0.0, 'average': 0.0, 'peak': 0.0}

        return {
            'current': self.memory_usage[-1] if self.memory_usage else 0.0,
            'average': sum(self.memory_usage) / len(self.memory_usage),
            'peak': max(self.memory_usage)
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self.update_times:
            return {
                'average_update_time': 0.0,
                'max_update_time': 0.0,
                'min_update_time': 0.0,
                'total_updates': 0,
                'slow_updates': 0,
                'critical_updates': 0,
                'fps': 0.0,
                'average_frame_time': 0.0,
                'memory_stats': self.get_memory_stats()
            }

        slow_updates = sum(1 for t in self.update_times if t > self.warning_threshold)
        critical_updates = sum(1 for t in self.update_times if t > self.critical_threshold)

        return {
            'average_update_time': self.get_average_update_time(),
            'max_update_time': max(self.update_times),
            'min_update_time': min(self.update_times),
            'total_updates': len(self.update_times),
            'slow_updates': slow_updates,
            'critical_updates': critical_updates,
            'fps': self.get_current_fps(),
            'average_frame_time': self.get_average_frame_time(),
            'memory_stats': self.get_memory_stats()
        }

    def is_performance_degraded(self) -> bool:
        """Check if performance is significantly degraded."""
        stats = self.get_performance_stats()

        # Check multiple performance indicators
        degraded_indicators = 0

        if stats['average_update_time'] > self.warning_threshold:
            degraded_indicators += 1

        if stats['fps'] < 20.0 and stats['fps'] > 0:  # Below 20 FPS
            degraded_indicators += 1

        if stats['critical_updates'] > stats['total_updates'] * 0.1:  # More than 10% critical updates
            degraded_indicators += 1

        return degraded_indicators >= 2


class SmartRefreshManager:
    """
    Manages smart refresh intervals based on activity and changes.
    Automatically adjusts refresh rates to optimize performance.
    """

    def __init__(self, base_interval: int = 3000, max_interval: int = 10000):
        """
        Initialize the smart refresh manager.

        Args:
            base_interval: Base refresh interval in milliseconds
            max_interval: Maximum refresh interval in milliseconds
        """
        self.base_interval = base_interval
        self.max_interval = max_interval
        self.current_interval = base_interval
        self.no_change_count = 0
        self.last_data_hash: Optional[str] = None

    def update_refresh_rate(self, data_hash: str) -> int:
        """
        Update refresh rate based on data changes.

        Args:
            data_hash: Hash of current data

        Returns:
            New refresh interval in milliseconds
        """
        if self.last_data_hash == data_hash:
            # No changes detected
            self.no_change_count += 1

            # Gradually increase interval
            if self.no_change_count >= 2:
                self.current_interval = min(
                    self.current_interval + 2000,  # Increase by 2 seconds
                    self.max_interval
                )
        else:
            # Changes detected, reset to base interval
            self.no_change_count = 0
            self.current_interval = self.base_interval

        self.last_data_hash = data_hash
        return self.current_interval

    def reset(self):
        """Reset the refresh manager to base settings."""
        self.current_interval = self.base_interval
        self.no_change_count = 0
        self.last_data_hash = None


# Global instances
_ui_batcher = UIUpdateBatcher()
_widget_state_manager = WidgetStateManager()
_performance_monitor = PerformanceMonitor()


def get_ui_batcher() -> UIUpdateBatcher:
    """Get the global UI update batcher."""
    return _ui_batcher


def get_widget_state_manager() -> WidgetStateManager:
    """Get the global widget state manager."""
    return _widget_state_manager


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor."""
    return _performance_monitor


def batch_ui_update(update_id: str):
    """
    Decorator to batch UI updates.

    Args:
        update_id: Unique identifier for the update
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            _ui_batcher.schedule_update(update_id, lambda: func(*args, **kwargs))
        return wrapper
    return decorator


def timed_ui_update(func):
    """
    Decorator to time UI updates for performance monitoring.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        update_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        _performance_monitor.record_update_time(update_time)
        return result
    return wrapper


def smart_widget_update(widget: QWidget, property_name: str, new_value: Any):
    """
    Smart widget update that only updates if the value has changed.

    Args:
        widget: Widget to update
        property_name: Property name
        new_value: New value

    Returns:
        Function to use as decorator or call directly
    """
    def decorator(update_func):
        def wrapper(*args, **kwargs):
            if _widget_state_manager.should_update(widget, property_name, new_value):
                return update_func(*args, **kwargs)
        return wrapper
    return decorator
