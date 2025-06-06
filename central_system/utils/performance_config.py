"""
Performance configuration and optimization settings for ConsultEase.
Optimized for Raspberry Pi deployment with configurable performance levels.
"""

import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PerformanceConfig:
    """
    Performance configuration settings.
    """
    
    # UI Performance
    ui_update_batch_delay: int = 100  # milliseconds
    ui_refresh_interval: int = 180000  # 3 minutes
    ui_max_refresh_interval: int = 600000  # 10 minutes
    ui_cache_ttl: int = 120  # 2 minutes
    
    # Virtual Scrolling
    virtual_scroll_buffer: int = 2  # Extra items to render
    virtual_scroll_item_height: int = 120  # pixels
    virtual_scroll_update_delay: int = 16  # ~60 FPS
    
    # Faculty Grid
    faculty_grid_columns: int = 3
    faculty_card_width: int = 280
    faculty_card_height: int = 120
    faculty_card_spacing: int = 15
    
    # Component Pooling
    component_pool_max_size: int = 50
    faculty_card_pool_size: int = 20
    
    # Memory Management
    memory_warning_threshold: float = 75.0  # percent
    memory_critical_threshold: float = 90.0  # percent
    memory_monitor_interval: float = 5.0  # seconds
    gc_threshold_multiplier: float = 1.5
    
    # MQTT Performance
    mqtt_batch_size: int = 10
    mqtt_batch_timeout: float = 0.1  # seconds
    mqtt_max_queue_size: int = 1000
    mqtt_worker_threads: int = 2
    
    # Database Performance
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800  # 30 minutes
    query_cache_ttl: int = 180  # 3 minutes
    
    # Performance Monitoring
    perf_monitor_enabled: bool = True
    perf_warning_threshold: float = 100.0  # milliseconds
    perf_critical_threshold: float = 200.0  # milliseconds
    perf_max_samples: int = 100
    
    # Raspberry Pi Specific
    rpi_optimize_for_touch: bool = True
    rpi_reduce_animations: bool = True
    rpi_limit_concurrent_operations: bool = True
    rpi_aggressive_gc: bool = True


class PerformanceLevel:
    """Performance level presets for different hardware configurations."""
    
    HIGH_PERFORMANCE = PerformanceConfig(
        ui_update_batch_delay=50,
        ui_refresh_interval=120000,  # 2 minutes
        virtual_scroll_buffer=3,
        virtual_scroll_update_delay=8,  # ~120 FPS
        component_pool_max_size=100,
        faculty_card_pool_size=50,
        memory_warning_threshold=80.0,
        memory_critical_threshold=95.0,
        mqtt_batch_size=20,
        mqtt_worker_threads=4,
        db_pool_size=10,
        rpi_reduce_animations=False,
        rpi_aggressive_gc=False
    )
    
    BALANCED = PerformanceConfig()  # Default values
    
    POWER_SAVING = PerformanceConfig(
        ui_update_batch_delay=200,
        ui_refresh_interval=300000,  # 5 minutes
        ui_max_refresh_interval=900000,  # 15 minutes
        virtual_scroll_buffer=1,
        virtual_scroll_update_delay=33,  # ~30 FPS
        component_pool_max_size=25,
        faculty_card_pool_size=10,
        memory_warning_threshold=70.0,
        memory_critical_threshold=85.0,
        memory_monitor_interval=10.0,
        gc_threshold_multiplier=2.0,
        mqtt_batch_size=5,
        mqtt_batch_timeout=0.2,
        mqtt_worker_threads=1,
        db_pool_size=3,
        perf_max_samples=50,
        rpi_aggressive_gc=True
    )
    
    RASPBERRY_PI_OPTIMIZED = PerformanceConfig(
        ui_update_batch_delay=150,
        ui_refresh_interval=240000,  # 4 minutes
        virtual_scroll_buffer=2,
        virtual_scroll_update_delay=25,  # ~40 FPS
        faculty_grid_columns=2,  # Fewer columns for smaller screen
        faculty_card_width=320,
        component_pool_max_size=30,
        faculty_card_pool_size=15,
        memory_warning_threshold=70.0,
        memory_critical_threshold=85.0,
        memory_monitor_interval=3.0,
        gc_threshold_multiplier=1.8,
        mqtt_batch_size=8,
        mqtt_worker_threads=2,
        db_pool_size=4,
        rpi_optimize_for_touch=True,
        rpi_reduce_animations=True,
        rpi_limit_concurrent_operations=True,
        rpi_aggressive_gc=True
    )


class PerformanceManager:
    """
    Manages performance configuration and optimization.
    """
    
    def __init__(self):
        """Initialize performance manager."""
        self.current_config = PerformanceConfig()
        self.config_file = "performance_config.json"
        self.auto_detect_enabled = True
        
        logger.debug("Performance manager initialized")
    
    def detect_hardware_level(self) -> str:
        """
        Detect hardware performance level automatically.
        
        Returns:
            str: Performance level name
        """
        try:
            import psutil
            
            # Get system info
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            
            # Detect Raspberry Pi
            is_rpi = self._is_raspberry_pi()
            
            if is_rpi:
                logger.info("Raspberry Pi detected, using optimized settings")
                return "raspberry_pi_optimized"
            elif memory_gb >= 8 and cpu_count >= 4:
                logger.info("High-performance hardware detected")
                return "high_performance"
            elif memory_gb >= 4 and cpu_count >= 2:
                logger.info("Balanced hardware detected")
                return "balanced"
            else:
                logger.info("Low-performance hardware detected")
                return "power_saving"
                
        except Exception as e:
            logger.error(f"Error detecting hardware level: {e}")
            return "balanced"
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        try:
            # Check for Raspberry Pi specific files
            rpi_indicators = [
                "/proc/device-tree/model",
                "/sys/firmware/devicetree/base/model"
            ]
            
            for indicator in rpi_indicators:
                if os.path.exists(indicator):
                    with open(indicator, 'r') as f:
                        content = f.read().lower()
                        if 'raspberry pi' in content:
                            return True
            
            # Check /proc/cpuinfo for ARM processor
            if os.path.exists("/proc/cpuinfo"):
                with open("/proc/cpuinfo", 'r') as f:
                    content = f.read().lower()
                    if 'arm' in content and ('bcm' in content or 'raspberry' in content):
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking for Raspberry Pi: {e}")
            return False
    
    def set_performance_level(self, level: str):
        """
        Set performance level by name.
        
        Args:
            level: Performance level name
        """
        level_configs = {
            "high_performance": PerformanceLevel.HIGH_PERFORMANCE,
            "balanced": PerformanceLevel.BALANCED,
            "power_saving": PerformanceLevel.POWER_SAVING,
            "raspberry_pi_optimized": PerformanceLevel.RASPBERRY_PI_OPTIMIZED
        }
        
        if level in level_configs:
            self.current_config = level_configs[level]
            logger.info(f"Performance level set to: {level}")
            self._apply_configuration()
        else:
            logger.error(f"Unknown performance level: {level}")
    
    def auto_configure(self):
        """Automatically configure performance based on hardware."""
        if self.auto_detect_enabled:
            level = self.detect_hardware_level()
            self.set_performance_level(level)
    
    def _apply_configuration(self):
        """Apply current configuration to system components."""
        try:
            # Apply UI performance settings
            self._apply_ui_config()
            
            # Apply memory management settings
            self._apply_memory_config()
            
            # Apply MQTT settings
            self._apply_mqtt_config()
            
            # Apply database settings
            self._apply_database_config()
            
            logger.info("Performance configuration applied successfully")
            
        except Exception as e:
            logger.error(f"Error applying performance configuration: {e}")
    
    def _apply_ui_config(self):
        """Apply UI performance configuration."""
        try:
            from ..utils.ui_performance import get_ui_batcher, get_performance_monitor
            
            # Configure UI batcher
            batcher = get_ui_batcher()
            batcher.batch_delay = self.current_config.ui_update_batch_delay
            
            # Configure performance monitor
            monitor = get_performance_monitor()
            monitor.warning_threshold = self.current_config.perf_warning_threshold
            monitor.critical_threshold = self.current_config.perf_critical_threshold
            monitor.max_samples = self.current_config.perf_max_samples
            
        except Exception as e:
            logger.error(f"Error applying UI configuration: {e}")
    
    def _apply_memory_config(self):
        """Apply memory management configuration."""
        try:
            from ..utils.memory_optimization import get_memory_optimizer
            
            optimizer = get_memory_optimizer()
            optimizer.monitor.warning_threshold = self.current_config.memory_warning_threshold
            optimizer.monitor.critical_threshold = self.current_config.memory_critical_threshold
            optimizer.monitor.monitor_interval = self.current_config.memory_monitor_interval
            optimizer.gc_optimizer.gc_threshold_multiplier = self.current_config.gc_threshold_multiplier
            
        except Exception as e:
            logger.error(f"Error applying memory configuration: {e}")
    
    def _apply_mqtt_config(self):
        """Apply MQTT performance configuration."""
        try:
            from ..services.async_mqtt_service import get_async_mqtt_service
            
            service = get_async_mqtt_service()
            service.batch_size = self.current_config.mqtt_batch_size
            service.batch_timeout = self.current_config.mqtt_batch_timeout
            service.max_queue_size = self.current_config.mqtt_max_queue_size
            
        except Exception as e:
            logger.error(f"Error applying MQTT configuration: {e}")
    
    def _apply_database_config(self):
        """Apply database performance configuration."""
        try:
            from ..utils.config_manager import get_config_manager
            
            config_manager = get_config_manager()
            config_manager.set_config('database.pool_size', self.current_config.db_pool_size)
            config_manager.set_config('database.max_overflow', self.current_config.db_max_overflow)
            config_manager.set_config('database.pool_timeout', self.current_config.db_pool_timeout)
            config_manager.set_config('database.pool_recycle', self.current_config.db_pool_recycle)
            
        except Exception as e:
            logger.error(f"Error applying database configuration: {e}")
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get current configuration as dictionary."""
        return asdict(self.current_config)
    
    def save_config(self, filename: Optional[str] = None):
        """Save current configuration to file."""
        try:
            import json
            
            filename = filename or self.config_file
            config_dict = self.get_config_dict()
            
            with open(filename, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info(f"Performance configuration saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def load_config(self, filename: Optional[str] = None):
        """Load configuration from file."""
        try:
            import json
            
            filename = filename or self.config_file
            
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    config_dict = json.load(f)
                
                # Update current config with loaded values
                for key, value in config_dict.items():
                    if hasattr(self.current_config, key):
                        setattr(self.current_config, key, value)
                
                self._apply_configuration()
                logger.info(f"Performance configuration loaded from {filename}")
            else:
                logger.info(f"Configuration file {filename} not found, using defaults")
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")


# Global instance
_performance_manager: Optional[PerformanceManager] = None


def get_performance_manager() -> PerformanceManager:
    """Get the global performance manager instance."""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager()
    return _performance_manager


def auto_configure_performance():
    """Automatically configure performance based on hardware."""
    manager = get_performance_manager()
    manager.auto_configure()


def get_current_config() -> PerformanceConfig:
    """Get current performance configuration."""
    manager = get_performance_manager()
    return manager.current_config
