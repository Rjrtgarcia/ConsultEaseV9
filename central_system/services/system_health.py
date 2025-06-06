"""
Enhanced System Health Monitoring for ConsultEase.
Provides comprehensive health monitoring, integration status, and system diagnostics.
"""

import logging
import threading
import time
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """System component types."""
    MQTT = "mqtt"
    ESP32 = "esp32"
    UI = "ui"
    STORAGE = "storage"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class HealthCheck:
    """Health check configuration."""
    name: str
    component_type: ComponentType
    check_function: Callable[[], bool]
    interval: float = 30.0  # seconds
    timeout: float = 10.0  # seconds
    critical: bool = False
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_status: HealthStatus = HealthStatus.UNKNOWN
    error_count: int = 0
    max_errors: int = 3


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    temperature: Optional[float] = None
    load_average: Optional[float] = None


@dataclass
class IntegrationStatus:
    """Integration component status."""
    component: str
    status: HealthStatus
    last_check: datetime
    response_time: float
    error_count: int
    details: Dict[str, Any] = field(default_factory=dict)


class SystemHealthMonitor:
    """
    Comprehensive system health monitoring service.
    """
    
    def __init__(self):
        """Initialize system health monitor."""
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.check_interval = 10.0  # seconds
        
        # Health checks registry
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # Metrics storage
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 288  # 24 hours at 5-minute intervals
        
        # Integration status
        self.integration_statuses: Dict[str, IntegrationStatus] = {}
        
        # Alert thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 85.0,
            'memory_warning': 75.0,
            'memory_critical': 90.0,
            'disk_warning': 80.0,
            'disk_critical': 95.0,
            'temperature_warning': 65.0,
            'temperature_critical': 75.0
        }
        
        # Alert tracking
        self.active_alerts: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.max_alert_history = 100
        
        # Performance tracking
        self.performance_baseline = None
        self.performance_degradation_threshold = 0.3  # 30% degradation
        
        # Setup default health checks
        self._setup_default_health_checks()
        
        logger.info("System health monitor initialized")
    
    def start_monitoring(self):
        """Start health monitoring."""
        if self.is_monitoring:
            logger.warning("Health monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            name="SystemHealthMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("System health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        logger.info("System health monitoring stopped")
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check."""
        self.health_checks[health_check.name] = health_check
        logger.info(f"Registered health check: {health_check.name}")
    
    def unregister_health_check(self, name: str):
        """Unregister a health check."""
        if name in self.health_checks:
            del self.health_checks[name]
            logger.info(f"Unregistered health check: {name}")
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        critical_issues = []
        warning_issues = []
        healthy_components = []
        
        # Check all health checks
        for name, check in self.health_checks.items():
            if not check.enabled:
                continue
                
            if check.last_status == HealthStatus.CRITICAL:
                critical_issues.append(name)
            elif check.last_status == HealthStatus.WARNING:
                warning_issues.append(name)
            elif check.last_status == HealthStatus.HEALTHY:
                healthy_components.append(name)
        
        # Determine overall status
        if critical_issues:
            overall_status = HealthStatus.CRITICAL
            status_message = f"{len(critical_issues)} critical issue(s) detected"
        elif warning_issues:
            overall_status = HealthStatus.WARNING
            status_message = f"{len(warning_issues)} warning(s) detected"
        elif healthy_components:
            overall_status = HealthStatus.HEALTHY
            status_message = "All systems operational"
        else:
            overall_status = HealthStatus.UNKNOWN
            status_message = "System status unknown"
        
        return {
            'overall_status': overall_status.value,
            'status_message': status_message,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'healthy_components': healthy_components,
            'total_checks': len(self.health_checks),
            'enabled_checks': len([c for c in self.health_checks.values() if c.enabled]),
            'last_update': datetime.now().isoformat()
        }
    
    def get_system_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Load average (Unix-like systems)
            load_average = None
            try:
                load_average = psutil.getloadavg()[0]  # 1-minute load average
            except (AttributeError, OSError):
                pass  # Not available on all systems
            
            # Temperature (Raspberry Pi)
            temperature = None
            try:
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if 'cpu_thermal' in temps:
                        temperature = temps['cpu_thermal'][0].current
            except (AttributeError, OSError):
                pass
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                temperature=temperature,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration component status."""
        return {
            name: {
                'component': status.component,
                'status': status.status.value,
                'last_check': status.last_check.isoformat(),
                'response_time': status.response_time,
                'error_count': status.error_count,
                'details': status.details
            }
            for name, status in self.integration_statuses.items()
        }
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Get performance analysis and trends."""
        if len(self.metrics_history) < 2:
            return {'status': 'insufficient_data'}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 readings
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_percent for m in recent_metrics) / len(recent_metrics)
        
        # Calculate trends
        cpu_trend = self._calculate_trend([m.cpu_percent for m in recent_metrics])
        memory_trend = self._calculate_trend([m.memory_percent for m in recent_metrics])
        
        # Performance assessment
        performance_score = self._calculate_performance_score(avg_cpu, avg_memory, avg_disk)
        
        return {
            'performance_score': performance_score,
            'averages': {
                'cpu': round(avg_cpu, 2),
                'memory': round(avg_memory, 2),
                'disk': round(avg_disk, 2)
            },
            'trends': {
                'cpu': cpu_trend,
                'memory': memory_trend
            },
            'analysis_period': len(recent_metrics),
            'last_update': datetime.now().isoformat()
        }
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Collect system metrics
                metrics = self.get_system_metrics()
                if metrics:
                    self.metrics_history.append(metrics)
                    
                    # Trim history
                    if len(self.metrics_history) > self.max_history:
                        self.metrics_history.pop(0)
                    
                    # Check for alerts
                    self._check_system_alerts(metrics)
                
                # Run health checks
                self._run_health_checks()
                
                # Update integration status
                self._update_integration_status()
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _setup_default_health_checks(self):
        """Setup default health checks."""
        # MQTT health check
        self.register_health_check(HealthCheck(
            name="mqtt_connection",
            component_type=ComponentType.MQTT,
            check_function=self._check_mqtt_health,
            interval=30.0,
            critical=True
        ))
        
        # Disk space check
        self.register_health_check(HealthCheck(
            name="disk_space",
            component_type=ComponentType.STORAGE,
            check_function=self._check_disk_space,
            interval=60.0,
            critical=True
        ))
        
        # System services check
        self.register_health_check(HealthCheck(
            name="system_services",
            component_type=ComponentType.SYSTEM,
            check_function=self._check_system_services,
            interval=60.0,
            critical=True
        ))
    
    def _run_health_checks(self):
        """Run all enabled health checks."""
        current_time = datetime.now()
        
        for name, check in self.health_checks.items():
            if not check.enabled:
                continue
            
            # Check if it's time to run this check
            if (check.last_check is None or 
                current_time - check.last_check >= timedelta(seconds=check.interval)):
                
                try:
                    # Run the health check
                    start_time = time.time()
                    is_healthy = check.check_function()
                    response_time = time.time() - start_time
                    
                    # Update check status
                    check.last_check = current_time
                    
                    if is_healthy:
                        check.last_status = HealthStatus.HEALTHY
                        check.error_count = 0
                    else:
                        check.error_count += 1
                        if check.error_count >= check.max_errors:
                            check.last_status = HealthStatus.CRITICAL if check.critical else HealthStatus.WARNING
                        else:
                            check.last_status = HealthStatus.WARNING
                    
                    # Update integration status
                    self.integration_statuses[name] = IntegrationStatus(
                        component=check.component_type.value,
                        status=check.last_status,
                        last_check=current_time,
                        response_time=response_time,
                        error_count=check.error_count
                    )
                    
                except Exception as e:
                    logger.error(f"Error running health check {name}: {e}")
                    check.last_status = HealthStatus.CRITICAL
                    check.error_count += 1
    
    def _check_mqtt_health(self) -> bool:
        """Check MQTT health."""
        try:
            from ..services.async_mqtt_service import get_async_mqtt_service
            mqtt_service = get_async_mqtt_service()
            stats = mqtt_service.get_stats()
            return stats['connected']
        except Exception as e:
            logger.debug(f"MQTT health check failed: {e}")
            return False
    
    def _check_disk_space(self) -> bool:
        """Check disk space."""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            return disk_percent < self.thresholds['disk_critical']
        except Exception as e:
            logger.debug(f"Disk space check failed: {e}")
            return False
    
    def _check_system_services(self) -> bool:
        """Check critical system services."""
        try:
            import subprocess
            critical_services = ['postgresql', 'mosquitto']
            
            for service in critical_services:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    return False
            
            return True
        except Exception as e:
            logger.debug(f"System services check failed: {e}")
            return False
    
    def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system alerts based on metrics."""
        alerts = []
        
        # CPU alerts
        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            alerts.append({
                'type': 'cpu_critical',
                'message': f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
                'severity': 'critical',
                'value': metrics.cpu_percent
            })
        elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
            alerts.append({
                'type': 'cpu_warning',
                'message': f"High CPU usage: {metrics.cpu_percent:.1f}%",
                'severity': 'warning',
                'value': metrics.cpu_percent
            })
        
        # Memory alerts
        if metrics.memory_percent >= self.thresholds['memory_critical']:
            alerts.append({
                'type': 'memory_critical',
                'message': f"Critical memory usage: {metrics.memory_percent:.1f}%",
                'severity': 'critical',
                'value': metrics.memory_percent
            })
        elif metrics.memory_percent >= self.thresholds['memory_warning']:
            alerts.append({
                'type': 'memory_warning',
                'message': f"High memory usage: {metrics.memory_percent:.1f}%",
                'severity': 'warning',
                'value': metrics.memory_percent
            })
        
        # Temperature alerts
        if metrics.temperature:
            if metrics.temperature >= self.thresholds['temperature_critical']:
                alerts.append({
                    'type': 'temperature_critical',
                    'message': f"Critical temperature: {metrics.temperature:.1f}°C",
                    'severity': 'critical',
                    'value': metrics.temperature
                })
            elif metrics.temperature >= self.thresholds['temperature_warning']:
                alerts.append({
                    'type': 'temperature_warning',
                    'message': f"High temperature: {metrics.temperature:.1f}°C",
                    'severity': 'warning',
                    'value': metrics.temperature
                })
        
        # Process new alerts
        for alert in alerts:
            alert['timestamp'] = datetime.now().isoformat()
            self._process_alert(alert)
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process and store alert."""
        # Check if this alert is already active
        existing_alert = None
        for active_alert in self.active_alerts:
            if active_alert['type'] == alert['type']:
                existing_alert = active_alert
                break
        
        if existing_alert:
            # Update existing alert
            existing_alert.update(alert)
        else:
            # Add new alert
            self.active_alerts.append(alert)
            logger.warning(f"New alert: {alert['message']}")
        
        # Add to history
        self.alert_history.append(alert.copy())
        
        # Trim history
        if len(self.alert_history) > self.max_alert_history:
            self.alert_history.pop(0)
    
    def _update_integration_status(self):
        """Update integration component status."""
        # This method can be extended to check specific integrations
        pass
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = ((second_half - first_half) / first_half) * 100
        
        if diff_percent > 10:
            return "increasing"
        elif diff_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_performance_score(self, cpu: float, memory: float, disk: float) -> int:
        """Calculate overall performance score (0-100)."""
        # Weighted performance score
        cpu_score = max(0, 100 - cpu)
        memory_score = max(0, 100 - memory)
        disk_score = max(0, 100 - disk)
        
        # Weighted average (CPU and memory are more important)
        overall_score = (cpu_score * 0.4 + memory_score * 0.4 + disk_score * 0.2)
        return int(overall_score)


# Global health monitor instance
_system_health_monitor: Optional[SystemHealthMonitor] = None


def get_system_health_monitor() -> SystemHealthMonitor:
    """Get or create global system health monitor instance."""
    global _system_health_monitor
    if _system_health_monitor is None:
        _system_health_monitor = SystemHealthMonitor()
    return _system_health_monitor


def start_system_health_monitoring():
    """Start global system health monitoring."""
    monitor = get_system_health_monitor()
    monitor.start_monitoring()


def stop_system_health_monitoring():
    """Stop global system health monitoring."""
    monitor = get_system_health_monitor()
    monitor.stop_monitoring()
