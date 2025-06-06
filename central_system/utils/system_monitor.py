"""
System monitoring utilities for ConsultEase.
Monitors system resources, performance metrics, and health status.
"""
import logging
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    uptime_seconds: float


@dataclass
class ServiceStatus:
    """Service status information."""
    name: str
    status: str  # 'running', 'stopped', 'error'
    pid: Optional[int]
    memory_mb: float
    cpu_percent: float
    last_check: datetime


class SystemMonitor:
    """
    System monitoring class for tracking performance and health.
    """
    
    def __init__(self, monitoring_interval=30):
        """
        Initialize system monitor.
        
        Args:
            monitoring_interval: Seconds between monitoring checks
        """
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        self.monitor_thread = None
        self.metrics_history = []
        self.max_history_size = 100  # Keep last 100 readings
        self.service_statuses = {}
        self.alerts = []
        self.max_alerts = 50
        
        # Thresholds for alerts
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        
        # Network baseline (will be set on first reading)
        self.network_baseline = None
        
    def start_monitoring(self):
        """Start system monitoring in background thread."""
        if self.is_monitoring:
            logger.warning("System monitoring is already running")
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System monitoring started")
        
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
        
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                
                # Store metrics
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Update service statuses
                self._update_service_statuses()
                
                # Sleep until next check
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
                
    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_free_gb = disk.free / (1024**3)
        
        # Network usage
        network = psutil.net_io_counters()
        
        # Process count
        process_count = len(psutil.pids())
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_percent=disk_percent,
            disk_free_gb=disk_free_gb,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            process_count=process_count,
            uptime_seconds=uptime_seconds
        )
        
    def _check_alerts(self, metrics: SystemMetrics):
        """Check for alert conditions."""
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.cpu_threshold:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'timestamp': metrics.timestamp,
                'value': metrics.cpu_percent
            })
            
        # Memory alert
        if metrics.memory_percent > self.memory_threshold:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'timestamp': metrics.timestamp,
                'value': metrics.memory_percent
            })
            
        # Disk alert
        if metrics.disk_percent > self.disk_threshold:
            alerts.append({
                'type': 'disk_high',
                'severity': 'critical',
                'message': f'High disk usage: {metrics.disk_percent:.1f}%',
                'timestamp': metrics.timestamp,
                'value': metrics.disk_percent
            })
            
        # Low memory alert
        if metrics.memory_available_gb < 0.5:  # Less than 500MB available
            alerts.append({
                'type': 'memory_low',
                'severity': 'critical',
                'message': f'Low available memory: {metrics.memory_available_gb:.1f}GB',
                'timestamp': metrics.timestamp,
                'value': metrics.memory_available_gb
            })
            
        # Low disk space alert
        if metrics.disk_free_gb < 1.0:  # Less than 1GB free
            alerts.append({
                'type': 'disk_low',
                'severity': 'critical',
                'message': f'Low disk space: {metrics.disk_free_gb:.1f}GB free',
                'timestamp': metrics.timestamp,
                'value': metrics.disk_free_gb
            })
            
        # Add alerts to history
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"SYSTEM ALERT: {alert['message']}")
            
        # Trim alerts history
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
            
    def _update_service_statuses(self):
        """Update status of key services."""
        services_to_check = [
            'consultease',
            'postgresql',
            'mosquitto',
            'squeekboard'
        ]
        
        for service_name in services_to_check:
            try:
                status = self._check_service_status(service_name)
                self.service_statuses[service_name] = status
            except Exception as e:
                logger.error(f"Error checking service {service_name}: {e}")
                self.service_statuses[service_name] = ServiceStatus(
                    name=service_name,
                    status='error',
                    pid=None,
                    memory_mb=0,
                    cpu_percent=0,
                    last_check=datetime.now()
                )
                
    def _check_service_status(self, service_name: str) -> ServiceStatus:
        """Check status of a specific service."""
        try:
            # Try to find process by name
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    if service_name.lower() in proc.info['name'].lower():
                        processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            if processes:
                # Use the first matching process
                proc = processes[0]
                return ServiceStatus(
                    name=service_name,
                    status='running',
                    pid=proc.pid,
                    memory_mb=proc.memory_info().rss / (1024 * 1024),
                    cpu_percent=proc.cpu_percent(),
                    last_check=datetime.now()
                )
            else:
                return ServiceStatus(
                    name=service_name,
                    status='stopped',
                    pid=None,
                    memory_mb=0,
                    cpu_percent=0,
                    last_check=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error checking service {service_name}: {e}")
            return ServiceStatus(
                name=service_name,
                status='error',
                pid=None,
                memory_mb=0,
                cpu_percent=0,
                last_check=datetime.now()
            )
            
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
        
    def get_metrics_history(self, minutes: int = 30) -> List[SystemMetrics]:
        """Get metrics history for the specified time period."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
    def get_service_statuses(self) -> Dict[str, ServiceStatus]:
        """Get current service statuses."""
        return self.service_statuses.copy()
        
    def get_recent_alerts(self, minutes: int = 60) -> List[Dict]:
        """Get recent alerts."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [a for a in self.alerts if a['timestamp'] >= cutoff_time]
        
    def get_system_health_summary(self) -> Dict:
        """Get overall system health summary."""
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return {'status': 'unknown', 'message': 'No metrics available'}
            
        # Determine overall health
        critical_alerts = [a for a in self.get_recent_alerts(10) if a['severity'] == 'critical']
        warning_alerts = [a for a in self.get_recent_alerts(10) if a['severity'] == 'warning']
        
        if critical_alerts:
            status = 'critical'
            message = f'{len(critical_alerts)} critical issue(s) detected'
        elif warning_alerts:
            status = 'warning'
            message = f'{len(warning_alerts)} warning(s) detected'
        elif (current_metrics.cpu_percent < 50 and 
              current_metrics.memory_percent < 70 and 
              current_metrics.disk_percent < 80):
            status = 'excellent'
            message = 'All systems operating normally'
        else:
            status = 'good'
            message = 'System operating within normal parameters'
            
        return {
            'status': status,
            'message': message,
            'cpu_percent': current_metrics.cpu_percent,
            'memory_percent': current_metrics.memory_percent,
            'disk_percent': current_metrics.disk_percent,
            'uptime_hours': current_metrics.uptime_seconds / 3600,
            'critical_alerts': len(critical_alerts),
            'warning_alerts': len(warning_alerts)
        }


# Global system monitor instance
_system_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Get the global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor


def start_system_monitoring():
    """Start system monitoring."""
    monitor = get_system_monitor()
    monitor.start_monitoring()


def stop_system_monitoring():
    """Stop system monitoring."""
    monitor = get_system_monitor()
    monitor.stop_monitoring()


def get_system_health() -> Dict:
    """Get current system health summary."""
    monitor = get_system_monitor()
    return monitor.get_system_health_summary()
