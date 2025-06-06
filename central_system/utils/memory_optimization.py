"""
Memory optimization utilities for ConsultEase system.
Provides garbage collection, memory monitoring, and optimization for Raspberry Pi.
"""

import gc
import logging
import psutil
import threading
import time
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class MemoryMonitor(QObject):
    """
    Monitor system memory usage and trigger optimizations.
    Optimized for Raspberry Pi resource constraints.
    """
    
    # Signals
    memory_warning = pyqtSignal(float)  # memory_usage_percent
    memory_critical = pyqtSignal(float)  # memory_usage_percent
    
    def __init__(self, warning_threshold=75.0, critical_threshold=90.0):
        """
        Initialize memory monitor.
        
        Args:
            warning_threshold: Memory usage percentage to trigger warning
            critical_threshold: Memory usage percentage to trigger critical alert
        """
        super().__init__()
        
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
        # Monitoring state
        self.monitoring = False
        self.monitor_interval = 5.0  # seconds
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_memory)
        
        # Memory tracking
        self.memory_history: List[float] = []
        self.max_history = 100
        self.last_warning_time = 0
        self.last_critical_time = 0
        self.warning_cooldown = 30.0  # seconds
        
        # Process reference
        self.process = psutil.Process()
        
        logger.debug("Memory monitor initialized")
    
    def start_monitoring(self):
        """Start memory monitoring."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_timer.start(int(self.monitor_interval * 1000))
            logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        if self.monitoring:
            self.monitoring = False
            self.monitor_timer.stop()
            logger.info("Memory monitoring stopped")
    
    def _check_memory(self):
        """Check current memory usage and trigger alerts if needed."""
        try:
            # Get system memory info
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent
            
            # Get process memory info
            process_memory = self.process.memory_info()
            process_memory_mb = process_memory.rss / 1024 / 1024
            
            # Track memory history
            self.memory_history.append(memory_percent)
            if len(self.memory_history) > self.max_history:
                self.memory_history.pop(0)
            
            current_time = time.time()
            
            # Check for critical memory usage
            if memory_percent >= self.critical_threshold:
                if current_time - self.last_critical_time > self.warning_cooldown:
                    logger.critical(f"Critical memory usage: {memory_percent:.1f}% (Process: {process_memory_mb:.1f}MB)")
                    self.memory_critical.emit(memory_percent)
                    self.last_critical_time = current_time
                    
                    # Trigger aggressive cleanup
                    self._trigger_aggressive_cleanup()
            
            # Check for warning memory usage
            elif memory_percent >= self.warning_threshold:
                if current_time - self.last_warning_time > self.warning_cooldown:
                    logger.warning(f"High memory usage: {memory_percent:.1f}% (Process: {process_memory_mb:.1f}MB)")
                    self.memory_warning.emit(memory_percent)
                    self.last_warning_time = current_time
                    
                    # Trigger gentle cleanup
                    self._trigger_gentle_cleanup()
            
            # Log debug info periodically
            if len(self.memory_history) % 12 == 0:  # Every minute at 5s intervals
                logger.debug(f"Memory usage: {memory_percent:.1f}% (Process: {process_memory_mb:.1f}MB)")
                
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
    
    def _trigger_gentle_cleanup(self):
        """Trigger gentle memory cleanup."""
        try:
            # Force garbage collection
            collected = gc.collect()
            logger.debug(f"Gentle cleanup: collected {collected} objects")
            
            # Clear Qt object caches if available
            from ..ui.component_pool import get_component_pool
            pool = get_component_pool()
            if hasattr(pool, 'cleanup_unused'):
                pool.cleanup_unused()
                
        except Exception as e:
            logger.error(f"Error during gentle cleanup: {e}")
    
    def _trigger_aggressive_cleanup(self):
        """Trigger aggressive memory cleanup."""
        try:
            # Multiple garbage collection passes
            for i in range(3):
                collected = gc.collect()
                logger.debug(f"Aggressive cleanup pass {i+1}: collected {collected} objects")
            
            # Clear all Qt object pools
            from ..ui.component_pool import get_component_pool
            from ..ui.pooled_faculty_card import get_faculty_card_manager
            
            pool = get_component_pool()
            if hasattr(pool, 'clear_all_pools'):
                pool.clear_all_pools()
            
            card_manager = get_faculty_card_manager()
            if hasattr(card_manager, 'clear_pool'):
                card_manager.clear_pool()
            
            # Clear query caches
            from ..utils.query_cache import get_query_cache
            cache = get_query_cache()
            if hasattr(cache, 'clear'):
                cache.clear()
                
            logger.info("Aggressive memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during aggressive cleanup: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics."""
        try:
            memory_info = psutil.virtual_memory()
            process_memory = self.process.memory_info()
            
            return {
                'system_total_mb': memory_info.total / 1024 / 1024,
                'system_available_mb': memory_info.available / 1024 / 1024,
                'system_used_percent': memory_info.percent,
                'process_rss_mb': process_memory.rss / 1024 / 1024,
                'process_vms_mb': process_memory.vms / 1024 / 1024,
                'gc_counts': gc.get_count(),
                'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {}
    
    def get_memory_trend(self) -> Dict[str, float]:
        """Get memory usage trend analysis."""
        if len(self.memory_history) < 2:
            return {'trend': 0.0, 'average': 0.0, 'peak': 0.0}
        
        # Calculate trend (simple linear regression slope)
        n = len(self.memory_history)
        x_sum = sum(range(n))
        y_sum = sum(self.memory_history)
        xy_sum = sum(i * self.memory_history[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        trend = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        return {
            'trend': trend,
            'average': y_sum / n,
            'peak': max(self.memory_history),
            'current': self.memory_history[-1]
        }


class GarbageCollectionOptimizer:
    """
    Optimize garbage collection for better performance.
    """
    
    def __init__(self):
        """Initialize garbage collection optimizer."""
        self.gc_stats = {'collections': 0, 'objects_collected': 0}
        self.auto_gc_enabled = True
        self.gc_threshold_multiplier = 1.5  # Increase thresholds for less frequent GC
        
        # Store original thresholds
        self.original_thresholds = gc.get_threshold()
        
        logger.debug("Garbage collection optimizer initialized")
    
    def optimize_gc_thresholds(self):
        """Optimize garbage collection thresholds for Raspberry Pi."""
        try:
            # Get current thresholds
            current = gc.get_threshold()
            
            # Increase thresholds to reduce GC frequency
            new_thresholds = tuple(int(t * self.gc_threshold_multiplier) for t in current)
            
            gc.set_threshold(*new_thresholds)
            logger.info(f"GC thresholds optimized: {current} -> {new_thresholds}")
            
        except Exception as e:
            logger.error(f"Error optimizing GC thresholds: {e}")
    
    def restore_gc_thresholds(self):
        """Restore original garbage collection thresholds."""
        try:
            gc.set_threshold(*self.original_thresholds)
            logger.info(f"GC thresholds restored: {self.original_thresholds}")
        except Exception as e:
            logger.error(f"Error restoring GC thresholds: {e}")
    
    def force_full_gc(self) -> int:
        """Force a full garbage collection cycle."""
        try:
            # Disable automatic GC temporarily
            gc.disable()
            
            total_collected = 0
            
            # Multiple passes to ensure thorough cleanup
            for generation in range(3):
                collected = gc.collect(generation)
                total_collected += collected
                logger.debug(f"GC generation {generation}: collected {collected} objects")
            
            # Re-enable automatic GC
            if self.auto_gc_enabled:
                gc.enable()
            
            self.gc_stats['collections'] += 1
            self.gc_stats['objects_collected'] += total_collected
            
            logger.debug(f"Full GC completed: {total_collected} objects collected")
            return total_collected
            
        except Exception as e:
            logger.error(f"Error during full GC: {e}")
            # Ensure GC is re-enabled
            if self.auto_gc_enabled:
                gc.enable()
            return 0
    
    def get_gc_stats(self) -> Dict[str, Any]:
        """Get garbage collection statistics."""
        return {
            'gc_counts': gc.get_count(),
            'gc_threshold': gc.get_threshold(),
            'gc_enabled': gc.isenabled(),
            'collections_performed': self.gc_stats['collections'],
            'total_objects_collected': self.gc_stats['objects_collected'],
            'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
        }


class MemoryOptimizer:
    """
    Main memory optimization coordinator.
    """
    
    def __init__(self):
        """Initialize memory optimizer."""
        self.monitor = MemoryMonitor()
        self.gc_optimizer = GarbageCollectionOptimizer()
        
        # Connect signals
        self.monitor.memory_warning.connect(self._on_memory_warning)
        self.monitor.memory_critical.connect(self._on_memory_critical)
        
        logger.debug("Memory optimizer initialized")
    
    def start(self):
        """Start memory optimization."""
        # Optimize GC thresholds
        self.gc_optimizer.optimize_gc_thresholds()
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        logger.info("Memory optimization started")
    
    def stop(self):
        """Stop memory optimization."""
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Restore GC thresholds
        self.gc_optimizer.restore_gc_thresholds()
        
        logger.info("Memory optimization stopped")
    
    def _on_memory_warning(self, memory_percent: float):
        """Handle memory warning."""
        logger.warning(f"Memory warning triggered at {memory_percent:.1f}%")
        
        # Perform gentle cleanup
        self.gc_optimizer.force_full_gc()
    
    def _on_memory_critical(self, memory_percent: float):
        """Handle critical memory situation."""
        logger.critical(f"Critical memory situation at {memory_percent:.1f}%")
        
        # Perform aggressive cleanup
        self.gc_optimizer.force_full_gc()
        
        # Additional cleanup measures could be added here
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory and GC statistics."""
        return {
            'memory_stats': self.monitor.get_memory_stats(),
            'memory_trend': self.monitor.get_memory_trend(),
            'gc_stats': self.gc_optimizer.get_gc_stats(),
            'monitoring_active': self.monitor.monitoring
        }
    
    def force_cleanup(self):
        """Force immediate memory cleanup."""
        logger.info("Forcing memory cleanup")
        collected = self.gc_optimizer.force_full_gc()
        logger.info(f"Forced cleanup completed: {collected} objects collected")
        return collected


# Global instance
_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get the global memory optimizer instance."""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer


def start_memory_optimization():
    """Start global memory optimization."""
    optimizer = get_memory_optimizer()
    optimizer.start()


def stop_memory_optimization():
    """Stop global memory optimization."""
    optimizer = get_memory_optimizer()
    optimizer.stop()


def force_memory_cleanup() -> int:
    """Force immediate memory cleanup."""
    optimizer = get_memory_optimizer()
    return optimizer.force_cleanup()
