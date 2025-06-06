"""
System Coordinator for ConsultEase.
Manages service lifecycle, health monitoring, and system integration.
"""

import logging
import threading
import time
import signal
import sys
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ServiceState(Enum):
    """Service state enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    RECOVERING = "recovering"


@dataclass
class ServiceInfo:
    """Service information container."""
    name: str
    state: ServiceState = ServiceState.STOPPED
    start_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    error_count: int = 0
    restart_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    health_check_interval: float = 30.0  # seconds
    max_restart_attempts: int = 3
    restart_delay: float = 5.0  # seconds


class SystemCoordinator:
    """
    Coordinates system services and manages their lifecycle.
    Provides centralized service management and health monitoring.
    """
    
    def __init__(self):
        """Initialize system coordinator."""
        self.services: Dict[str, ServiceInfo] = {}
        self.service_instances: Dict[str, Any] = {}
        self.startup_callbacks: Dict[str, Callable] = {}
        self.shutdown_callbacks: Dict[str, Callable] = {}
        self.health_check_callbacks: Dict[str, Callable] = {}
        
        # Coordination state
        self.is_running = False
        self.shutdown_requested = False
        self.coordinator_thread: Optional[threading.Thread] = None
        
        # Health monitoring
        self.health_monitor_thread: Optional[threading.Thread] = None
        self.health_check_interval = 10.0  # seconds
        
        # Error handling
        self.error_handlers: Dict[str, Callable] = {}
        self.system_error_count = 0
        self.max_system_errors = 10
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        logger.info("System coordinator initialized")
    
    def register_service(self, name: str, dependencies: List[str] = None,
                        startup_callback: Callable = None,
                        shutdown_callback: Callable = None,
                        health_check_callback: Callable = None,
                        health_check_interval: float = 30.0,
                        max_restart_attempts: int = 3) -> ServiceInfo:
        """
        Register a service with the coordinator.
        
        Args:
            name: Service name
            dependencies: List of service names this service depends on
            startup_callback: Function to call when starting the service
            shutdown_callback: Function to call when stopping the service
            health_check_callback: Function to call for health checks
            health_check_interval: Interval between health checks in seconds
            max_restart_attempts: Maximum restart attempts before giving up
            
        Returns:
            ServiceInfo: Service information object
        """
        service_info = ServiceInfo(
            name=name,
            dependencies=dependencies or [],
            health_check_interval=health_check_interval,
            max_restart_attempts=max_restart_attempts
        )
        
        self.services[name] = service_info
        
        if startup_callback:
            self.startup_callbacks[name] = startup_callback
        if shutdown_callback:
            self.shutdown_callbacks[name] = shutdown_callback
        if health_check_callback:
            self.health_check_callbacks[name] = health_check_callback
        
        logger.info(f"Registered service: {name} with dependencies: {dependencies}")
        return service_info
    
    def start_system(self) -> bool:
        """
        Start the entire system in dependency order.
        
        Returns:
            bool: True if system started successfully
        """
        if self.is_running:
            logger.warning("System is already running")
            return True
        
        logger.info("Starting ConsultEase system...")
        
        try:
            # Calculate startup order based on dependencies
            startup_order = self._calculate_startup_order()
            
            # Start services in order
            for service_name in startup_order:
                if not self._start_service(service_name):
                    logger.error(f"Failed to start service: {service_name}")
                    self._emergency_shutdown()
                    return False
            
            # Start coordinator and health monitoring
            self.is_running = True
            self._start_coordinator_thread()
            self._start_health_monitoring()
            
            logger.info("ConsultEase system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            self._emergency_shutdown()
            return False
    
    def stop_system(self) -> bool:
        """
        Stop the entire system gracefully.
        
        Returns:
            bool: True if system stopped successfully
        """
        if not self.is_running:
            logger.warning("System is not running")
            return True
        
        logger.info("Stopping ConsultEase system...")
        self.shutdown_requested = True
        
        try:
            # Stop health monitoring
            self._stop_health_monitoring()
            
            # Calculate shutdown order (reverse of startup)
            startup_order = self._calculate_startup_order()
            shutdown_order = list(reversed(startup_order))
            
            # Stop services in reverse order
            for service_name in shutdown_order:
                self._stop_service(service_name)
            
            # Stop coordinator
            self.is_running = False
            if self.coordinator_thread and self.coordinator_thread.is_alive():
                self.coordinator_thread.join(timeout=5.0)
            
            logger.info("ConsultEase system stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """
        Restart a specific service.
        
        Args:
            service_name: Name of service to restart
            
        Returns:
            bool: True if service restarted successfully
        """
        if service_name not in self.services:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        logger.info(f"Restarting service: {service_name}")
        
        # Stop service
        self._stop_service(service_name)
        
        # Wait a moment
        time.sleep(self.services[service_name].restart_delay)
        
        # Start service
        return self._start_service(service_name)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            dict: System status information
        """
        service_statuses = {}
        for name, service in self.services.items():
            service_statuses[name] = {
                'state': service.state.value,
                'start_time': service.start_time.isoformat() if service.start_time else None,
                'last_health_check': service.last_health_check.isoformat() if service.last_health_check else None,
                'error_count': service.error_count,
                'restart_count': service.restart_count,
                'dependencies': service.dependencies
            }
        
        return {
            'system_running': self.is_running,
            'shutdown_requested': self.shutdown_requested,
            'system_error_count': self.system_error_count,
            'services': service_statuses,
            'uptime': self._get_system_uptime()
        }
    
    def _calculate_startup_order(self) -> List[str]:
        """Calculate service startup order based on dependencies."""
        ordered = []
        visited = set()
        temp_visited = set()
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            # Visit dependencies first
            service = self.services.get(service_name)
            if service:
                for dep in service.dependencies:
                    if dep in self.services:
                        visit(dep)
                    else:
                        logger.warning(f"Dependency {dep} not registered for service {service_name}")
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            ordered.append(service_name)
        
        # Visit all services
        for service_name in self.services:
            if service_name not in visited:
                visit(service_name)
        
        logger.debug(f"Calculated startup order: {ordered}")
        return ordered
    
    def _start_service(self, service_name: str) -> bool:
        """Start a specific service."""
        service = self.services.get(service_name)
        if not service:
            logger.error(f"Service not found: {service_name}")
            return False
        
        if service.state == ServiceState.RUNNING:
            logger.debug(f"Service {service_name} is already running")
            return True
        
        logger.info(f"Starting service: {service_name}")
        service.state = ServiceState.STARTING
        
        try:
            # Check dependencies
            for dep_name in service.dependencies:
                dep_service = self.services.get(dep_name)
                if not dep_service or dep_service.state != ServiceState.RUNNING:
                    logger.error(f"Dependency {dep_name} is not running for service {service_name}")
                    service.state = ServiceState.ERROR
                    return False
            
            # Call startup callback
            startup_callback = self.startup_callbacks.get(service_name)
            if startup_callback:
                result = startup_callback()
                if result is False:
                    logger.error(f"Startup callback failed for service: {service_name}")
                    service.state = ServiceState.ERROR
                    return False
                elif hasattr(result, '__call__'):
                    # Store service instance if callback returns an object
                    self.service_instances[service_name] = result
            
            # Mark as running
            service.state = ServiceState.RUNNING
            service.start_time = datetime.now()
            service.last_health_check = datetime.now()
            
            logger.info(f"Service started successfully: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting service {service_name}: {e}")
            service.state = ServiceState.ERROR
            service.error_count += 1
            return False
    
    def _stop_service(self, service_name: str) -> bool:
        """Stop a specific service."""
        service = self.services.get(service_name)
        if not service:
            logger.error(f"Service not found: {service_name}")
            return False
        
        if service.state == ServiceState.STOPPED:
            logger.debug(f"Service {service_name} is already stopped")
            return True
        
        logger.info(f"Stopping service: {service_name}")
        service.state = ServiceState.STOPPING
        
        try:
            # Call shutdown callback
            shutdown_callback = self.shutdown_callbacks.get(service_name)
            if shutdown_callback:
                shutdown_callback()
            
            # Remove service instance
            if service_name in self.service_instances:
                del self.service_instances[service_name]
            
            # Mark as stopped
            service.state = ServiceState.STOPPED
            service.start_time = None
            
            logger.info(f"Service stopped successfully: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping service {service_name}: {e}")
            service.state = ServiceState.ERROR
            return False
    
    def _start_coordinator_thread(self):
        """Start the coordinator monitoring thread."""
        self.coordinator_thread = threading.Thread(
            target=self._coordinator_loop,
            name="SystemCoordinator",
            daemon=True
        )
        self.coordinator_thread.start()
    
    def _start_health_monitoring(self):
        """Start health monitoring thread."""
        self.health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            name="HealthMonitor",
            daemon=True
        )
        self.health_monitor_thread.start()
    
    def _stop_health_monitoring(self):
        """Stop health monitoring thread."""
        if self.health_monitor_thread and self.health_monitor_thread.is_alive():
            self.health_monitor_thread.join(timeout=5.0)
    
    def _coordinator_loop(self):
        """Main coordinator monitoring loop."""
        while self.is_running and not self.shutdown_requested:
            try:
                # Monitor system state
                self._check_system_health()
                
                # Handle any pending service restarts
                self._handle_service_recovery()
                
                # Sleep
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in coordinator loop: {e}")
                self.system_error_count += 1
                
                if self.system_error_count >= self.max_system_errors:
                    logger.critical("Too many system errors, initiating emergency shutdown")
                    self._emergency_shutdown()
                    break
    
    def _health_monitor_loop(self):
        """Health monitoring loop."""
        while self.is_running and not self.shutdown_requested:
            try:
                current_time = datetime.now()
                
                for service_name, service in self.services.items():
                    if service.state == ServiceState.RUNNING:
                        # Check if health check is due
                        if (not service.last_health_check or 
                            current_time - service.last_health_check >= timedelta(seconds=service.health_check_interval)):
                            
                            self._perform_health_check(service_name)
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
    
    def _perform_health_check(self, service_name: str):
        """Perform health check for a service."""
        service = self.services.get(service_name)
        health_check = self.health_check_callbacks.get(service_name)
        
        if not service or not health_check:
            return
        
        try:
            is_healthy = health_check()
            service.last_health_check = datetime.now()
            
            if not is_healthy:
                logger.warning(f"Health check failed for service: {service_name}")
                service.error_count += 1
                
                # Consider restart if too many failures
                if service.error_count >= 3 and service.restart_count < service.max_restart_attempts:
                    logger.info(f"Scheduling restart for unhealthy service: {service_name}")
                    service.state = ServiceState.RECOVERING
            else:
                # Reset error count on successful health check
                service.error_count = 0
                
        except Exception as e:
            logger.error(f"Error performing health check for {service_name}: {e}")
            service.error_count += 1
    
    def _handle_service_recovery(self):
        """Handle service recovery and restarts."""
        for service_name, service in self.services.items():
            if service.state == ServiceState.RECOVERING:
                if service.restart_count < service.max_restart_attempts:
                    logger.info(f"Attempting to restart service: {service_name}")
                    service.restart_count += 1
                    
                    if self.restart_service(service_name):
                        logger.info(f"Service restarted successfully: {service_name}")
                    else:
                        logger.error(f"Failed to restart service: {service_name}")
                else:
                    logger.error(f"Service {service_name} exceeded max restart attempts")
                    service.state = ServiceState.ERROR
    
    def _check_system_health(self):
        """Check overall system health."""
        critical_services_down = 0
        
        for service_name, service in self.services.items():
            if service.state in [ServiceState.ERROR, ServiceState.STOPPED]:
                if service_name in ['database', 'mqtt', 'ui']:  # Critical services
                    critical_services_down += 1
        
        if critical_services_down > 0:
            logger.warning(f"{critical_services_down} critical services are down")
    
    def _emergency_shutdown(self):
        """Perform emergency system shutdown."""
        logger.critical("Performing emergency system shutdown")
        self.shutdown_requested = True
        self.is_running = False
        
        # Force stop all services
        for service_name in self.services:
            try:
                self._stop_service(service_name)
            except Exception as e:
                logger.error(f"Error during emergency shutdown of {service_name}: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.stop_system()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _get_system_uptime(self) -> Optional[str]:
        """Get system uptime."""
        if not self.is_running:
            return None
        
        # Find earliest service start time
        earliest_start = None
        for service in self.services.values():
            if service.start_time:
                if not earliest_start or service.start_time < earliest_start:
                    earliest_start = service.start_time
        
        if earliest_start:
            uptime = datetime.now() - earliest_start
            return str(uptime).split('.')[0]  # Remove microseconds
        
        return None


# Global coordinator instance
_system_coordinator: Optional[SystemCoordinator] = None


def get_system_coordinator() -> SystemCoordinator:
    """Get the global system coordinator instance."""
    global _system_coordinator
    if _system_coordinator is None:
        _system_coordinator = SystemCoordinator()
    return _system_coordinator
