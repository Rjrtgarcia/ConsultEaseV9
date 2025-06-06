"""
Enhanced MQTT Message Router for ConsultEase.
Provides intelligent message routing, filtering, and transformation.
"""

import logging
import json
import time
import threading
from typing import Dict, List, Callable, Any, Optional, Pattern
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class RouteAction(Enum):
    """Route action types."""
    FORWARD = "forward"
    TRANSFORM = "transform"
    FILTER = "filter"
    DUPLICATE = "duplicate"
    AGGREGATE = "aggregate"


@dataclass
class MessageRoute:
    """Message routing configuration."""
    name: str
    pattern: Pattern
    action: RouteAction
    target_topics: List[str] = field(default_factory=list)
    transform_func: Optional[Callable] = None
    filter_func: Optional[Callable] = None
    priority: MessagePriority = MessagePriority.NORMAL
    rate_limit: Optional[float] = None  # messages per second
    enabled: bool = True


@dataclass
class MessageStats:
    """Message statistics tracking."""
    total_received: int = 0
    total_routed: int = 0
    total_filtered: int = 0
    total_errors: int = 0
    last_message_time: Optional[datetime] = None
    messages_per_topic: Dict[str, int] = field(default_factory=dict)
    errors_per_topic: Dict[str, int] = field(default_factory=dict)


class MQTTRouter:
    """
    Enhanced MQTT message router with intelligent routing capabilities.
    """
    
    def __init__(self, mqtt_service):
        """
        Initialize MQTT router.
        
        Args:
            mqtt_service: MQTT service instance for publishing
        """
        self.mqtt_service = mqtt_service
        self.routes: Dict[str, MessageRoute] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.stats = MessageStats()
        
        # Rate limiting
        self.rate_limiters: Dict[str, Dict[str, float]] = {}  # route_name -> {last_time, count}
        
        # Message aggregation
        self.aggregation_buffers: Dict[str, List[Dict]] = {}
        self.aggregation_timers: Dict[str, threading.Timer] = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Setup default routes
        self._setup_default_routes()
        
        logger.info("MQTT router initialized")
    
    def add_route(self, route: MessageRoute):
        """
        Add a message route.
        
        Args:
            route: MessageRoute configuration
        """
        with self.lock:
            self.routes[route.name] = route
            logger.info(f"Added MQTT route: {route.name} -> {route.action.value}")
    
    def remove_route(self, route_name: str):
        """Remove a message route."""
        with self.lock:
            if route_name in self.routes:
                del self.routes[route_name]
                logger.info(f"Removed MQTT route: {route_name}")
    
    def add_handler(self, topic_pattern: str, handler: Callable):
        """
        Add a message handler for a topic pattern.
        
        Args:
            topic_pattern: Topic pattern (supports wildcards)
            handler: Handler function
        """
        with self.lock:
            if topic_pattern not in self.message_handlers:
                self.message_handlers[topic_pattern] = []
            self.message_handlers[topic_pattern].append(handler)
            logger.debug(f"Added message handler for pattern: {topic_pattern}")
    
    def route_message(self, topic: str, payload: Any, qos: int = 1) -> bool:
        """
        Route a message through the routing system.
        
        Args:
            topic: Original topic
            payload: Message payload
            qos: Quality of service
            
        Returns:
            bool: True if message was routed successfully
        """
        with self.lock:
            self.stats.total_received += 1
            self.stats.last_message_time = datetime.now()
            
            # Update topic statistics
            if topic not in self.stats.messages_per_topic:
                self.stats.messages_per_topic[topic] = 0
            self.stats.messages_per_topic[topic] += 1
            
            try:
                # Find matching routes
                matching_routes = self._find_matching_routes(topic)
                
                if not matching_routes:
                    # No routes found, use default handlers
                    return self._handle_with_default_handlers(topic, payload)
                
                # Process each matching route
                success = True
                for route in matching_routes:
                    if not self._process_route(route, topic, payload, qos):
                        success = False
                
                if success:
                    self.stats.total_routed += 1
                
                return success
                
            except Exception as e:
                logger.error(f"Error routing message for topic {topic}: {e}")
                self.stats.total_errors += 1
                self._update_error_stats(topic)
                return False
    
    def _setup_default_routes(self):
        """Setup default routing rules."""
        # Faculty status updates
        self.add_route(MessageRoute(
            name="faculty_status_route",
            pattern=re.compile(r"consultease/faculty/\d+/(status|mac_status)"),
            action=RouteAction.DUPLICATE,
            target_topics=[
                "consultease/notifications/faculty_status",
                "consultease/dashboard/updates"
            ],
            priority=MessagePriority.HIGH
        ))
        self.add_handler(r"consultease/faculty/\d+/(status|mac_status)", self._handle_faculty_status_update)
        
        # Consultation requests
        self.add_route(MessageRoute(
            name="consultation_request_route",
            pattern=re.compile(r"consultease/consultation/request"),
            action=RouteAction.TRANSFORM,
            transform_func=self._transform_consultation_request,
            target_topics=["consultease/faculty/{faculty_id}/consultation"],
            priority=MessagePriority.CRITICAL
        ))
        
        # System notifications aggregation
        self.add_route(MessageRoute(
            name="system_notifications_aggregate",
            pattern=re.compile(r"consultease/system/.*"),
            action=RouteAction.AGGREGATE,
            target_topics=["consultease/system/aggregated"],
            rate_limit=1.0  # Max 1 aggregated message per second
        ))
        
        # ESP32 heartbeat filtering
        self.add_route(MessageRoute(
            name="esp32_heartbeat_filter",
            pattern=re.compile(r"consultease/esp32/\d+/heartbeat"),
            action=RouteAction.FILTER,
            filter_func=self._filter_heartbeat_messages,
            rate_limit=0.1  # Max 1 heartbeat per 10 seconds per device
        ))
    
    def _find_matching_routes(self, topic: str) -> List[MessageRoute]:
        """Find routes that match the given topic."""
        matching = []
        for route in self.routes.values():
            if route.enabled and route.pattern.match(topic):
                matching.append(route)
        
        # Sort by priority
        matching.sort(key=lambda r: r.priority.value, reverse=True)
        return matching
    
    def _process_route(self, route: MessageRoute, topic: str, payload: Any, qos: int) -> bool:
        """Process a message through a specific route."""
        try:
            # Check rate limiting
            if route.rate_limit and not self._check_rate_limit(route.name, route.rate_limit):
                logger.debug(f"Rate limit exceeded for route: {route.name}")
                return True  # Not an error, just rate limited
            
            # Process based on action type
            if route.action == RouteAction.FORWARD:
                return self._forward_message(route, topic, payload, qos)
            elif route.action == RouteAction.TRANSFORM:
                return self._transform_message(route, topic, payload, qos)
            elif route.action == RouteAction.FILTER:
                return self._filter_message(route, topic, payload, qos)
            elif route.action == RouteAction.DUPLICATE:
                return self._duplicate_message(route, topic, payload, qos)
            elif route.action == RouteAction.AGGREGATE:
                return self._aggregate_message(route, topic, payload, qos)
            else:
                logger.warning(f"Unknown route action: {route.action}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing route {route.name}: {e}")
            return False
    
    def _forward_message(self, route: MessageRoute, topic: str, payload: Any, qos: int) -> bool:
        """Forward message to target topics."""
        success = True
        for target_topic in route.target_topics:
            try:
                # Replace placeholders in target topic
                resolved_topic = self._resolve_topic_placeholders(target_topic, topic, payload)
                self.mqtt_service.publish_async(resolved_topic, payload, qos)
            except Exception as e:
                logger.error(f"Error forwarding to {target_topic}: {e}")
                success = False
        return success
    
    def _transform_message(self, route: MessageRoute, topic: str, payload: Any, qos: int) -> bool:
        """Transform and forward message."""
        if not route.transform_func:
            logger.warning(f"No transform function for route: {route.name}")
            return False
        
        try:
            transformed_payload = route.transform_func(topic, payload)
            if transformed_payload is None:
                return True  # Transform function filtered the message
            
            success = True
            for target_topic in route.target_topics:
                try:
                    resolved_topic = self._resolve_topic_placeholders(target_topic, topic, payload)
                    self.mqtt_service.publish_async(resolved_topic, transformed_payload, qos)
                except Exception as e:
                    logger.error(f"Error publishing transformed message to {target_topic}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error transforming message: {e}")
            return False
    
    def _filter_message(self, route: MessageRoute, topic: str, payload: Any, qos: int) -> bool:
        """Filter message based on filter function."""
        if not route.filter_func:
            return True  # No filter, pass through
        
        try:
            should_pass = route.filter_func(topic, payload)
            if should_pass:
                return self._forward_message(route, topic, payload, qos)
            else:
                self.stats.total_filtered += 1
                return True  # Filtered, but not an error
                
        except Exception as e:
            logger.error(f"Error filtering message: {e}")
            return False
    
    def _duplicate_message(self, route: MessageRoute, topic: str, payload: Any, qos: int) -> bool:
        """Duplicate message to multiple topics."""
        return self._forward_message(route, topic, payload, qos)
    
    def _aggregate_message(self, route: MessageRoute, topic: str, payload: Any, qos: int) -> bool:
        """Aggregate messages and publish periodically."""
        try:
            # Add to aggregation buffer
            if route.name not in self.aggregation_buffers:
                self.aggregation_buffers[route.name] = []
            
            self.aggregation_buffers[route.name].append({
                'topic': topic,
                'payload': payload,
                'timestamp': datetime.now().isoformat(),
                'qos': qos
            })
            
            # Set timer for aggregation if not already set
            if route.name not in self.aggregation_timers:
                timer = threading.Timer(5.0, self._flush_aggregation_buffer, args=[route])
                timer.start()
                self.aggregation_timers[route.name] = timer
            
            return True
            
        except Exception as e:
            logger.error(f"Error aggregating message: {e}")
            return False
    
    def _flush_aggregation_buffer(self, route: MessageRoute):
        """Flush aggregation buffer and publish aggregated message."""
        try:
            with self.lock:
                if route.name in self.aggregation_buffers:
                    messages = self.aggregation_buffers.pop(route.name)
                    if route.name in self.aggregation_timers:
                        del self.aggregation_timers[route.name]
                    
                    if messages:
                        aggregated_payload = {
                            'type': 'aggregated_messages',
                            'count': len(messages),
                            'messages': messages,
                            'aggregation_time': datetime.now().isoformat()
                        }
                        
                        for target_topic in route.target_topics:
                            self.mqtt_service.publish_async(target_topic, aggregated_payload)
                        
                        logger.debug(f"Flushed {len(messages)} aggregated messages for route: {route.name}")
                        
        except Exception as e:
            logger.error(f"Error flushing aggregation buffer: {e}")
    
    def _check_rate_limit(self, route_name: str, rate_limit: float) -> bool:
        """Check if message passes rate limiting."""
        current_time = time.time()
        
        if route_name not in self.rate_limiters:
            self.rate_limiters[route_name] = {'last_time': current_time, 'count': 1}
            return True
        
        limiter = self.rate_limiters[route_name]
        time_diff = current_time - limiter['last_time']
        
        if time_diff >= 1.0:  # Reset counter every second
            limiter['last_time'] = current_time
            limiter['count'] = 1
            return True
        
        if limiter['count'] < rate_limit:
            limiter['count'] += 1
            return True
        
        return False
    
    def _resolve_topic_placeholders(self, target_topic: str, original_topic: str, payload: Any) -> str:
        """Resolve placeholders in target topic."""
        resolved = target_topic
        
        # Extract faculty ID from original topic
        faculty_id_match = re.search(r'faculty/(\d+)', original_topic)
        if faculty_id_match:
            resolved = resolved.replace('{faculty_id}', faculty_id_match.group(1))
        
        # Extract other placeholders from payload
        if isinstance(payload, dict):
            for key, value in payload.items():
                placeholder = f'{{{key}}}'
                if placeholder in resolved:
                    resolved = resolved.replace(placeholder, str(value))
        
        return resolved
    
    def _handle_with_default_handlers(self, topic: str, payload: Any) -> bool:
        """Handle message with registered handlers."""
        handled = False
        
        for pattern, handlers in self.message_handlers.items():
            if self._topic_matches_pattern(topic, pattern):
                for handler in handlers:
                    try:
                        handler(topic, payload)
                        handled = True
                    except Exception as e:
                        logger.error(f"Error in message handler for {pattern}: {e}")
        
        return handled
    
    def _topic_matches_pattern(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern (supports MQTT wildcards)."""
        # Convert MQTT wildcards to regex
        regex_pattern = pattern.replace('+', '[^/]+').replace('#', '.*')
        return re.match(f"^{regex_pattern}$", topic) is not None
    
    def _transform_consultation_request(self, topic: str, payload: Any) -> Optional[Dict]:
        """Transform consultation request message."""
        if not isinstance(payload, dict):
            return None
        
        # Add routing metadata
        transformed = payload.copy()
        transformed['routing'] = {
            'original_topic': topic,
            'routed_at': datetime.now().isoformat(),
            'priority': 'high'
        }
        
        return transformed
    
    def _filter_heartbeat_messages(self, topic: str, payload: Any) -> bool:
        """Filter heartbeat messages to reduce noise."""
        # Only pass through heartbeats with important status changes
        if isinstance(payload, dict):
            status = payload.get('status', '')
            if status in ['error', 'warning', 'startup', 'shutdown']:
                return True
        
        return False  # Filter out regular heartbeats
    
    def _update_error_stats(self, topic: str):
        """Update error statistics."""
        if topic not in self.stats.errors_per_topic:
            self.stats.errors_per_topic[topic] = 0
        self.stats.errors_per_topic[topic] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        with self.lock:
            return {
                'total_received': self.stats.total_received,
                'total_routed': self.stats.total_routed,
                'total_filtered': self.stats.total_filtered,
                'total_errors': self.stats.total_errors,
                'last_message_time': self.stats.last_message_time.isoformat() if self.stats.last_message_time else None,
                'messages_per_topic': dict(self.stats.messages_per_topic),
                'errors_per_topic': dict(self.stats.errors_per_topic),
                'active_routes': len([r for r in self.routes.values() if r.enabled]),
                'total_routes': len(self.routes)
            }
    
    def get_route_info(self) -> List[Dict[str, Any]]:
        """Get information about all routes."""
        with self.lock:
            return [
                {
                    'name': route.name,
                    'pattern': route.pattern.pattern,
                    'action': route.action.value,
                    'target_topics': route.target_topics,
                    'priority': route.priority.value,
                    'rate_limit': route.rate_limit,
                    'enabled': route.enabled
                }
                for route in self.routes.values()
            ]

    def _handle_faculty_status_update(self, topic: str, payload: Any):
        """Handle faculty status updates and update the database."""
        try:
            logger.debug(f"Handling faculty status update for topic {topic}: {payload}")
            # Extract faculty_id from topic
            match = re.search(r"consultease/faculty/(\d+)/status", topic)
            if not match:
                match = re.search(r"consultease/faculty/(\d+)/mac_status", topic) # Check mac_status topic as well
            
            if match:
                faculty_id = int(match.group(1))
                status_str = payload.get("status", "").upper()
                # Detailed status can also be used if needed
                # detailed_status_str = payload.get("detailed_status", "").upper()

                availability = None
                if status_str == "AVAILABLE" or status_str == "PRESENT":
                    availability = "Available"
                elif status_str == "AWAY" or status_str == "OFFLINE": # Consider AWAY and OFFLINE as Unavailable
                    availability = "Unavailable"
                elif "BUSY" in status_str: # If status contains BUSY
                    availability = "Busy"
                
                if availability:
                    from ..models.faculty import Faculty  # Delayed import
                    from ..models.base import get_db # Delayed import

                    with get_db() as db:
                        faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
                        if faculty:
                            logger.info(f"Updating faculty {faculty_id} availability to {availability}")
                            faculty.availability = availability
                            faculty.last_seen = datetime.now() # Update last_seen timestamp
                            db.commit()
                            logger.info(f"Faculty {faculty_id} availability updated to {availability} in database.")
                        else:
                            logger.warning(f"Faculty with ID {faculty_id} not found in database.")
                else:
                    logger.warning(f"Could not determine availability from status: {status_str} for faculty {faculty_id}")
            else:
                logger.warning(f"Could not extract faculty_id from topic: {topic}")
        except Exception as e:
            logger.error(f"Error handling faculty status update for topic {topic}: {e}")
            # Optionally, update error stats for this specific handler
            self._update_error_stats(topic) # Use existing method if appropriate


# Global router instance
_mqtt_router: Optional[MQTTRouter] = None


def get_mqtt_router(mqtt_service=None) -> Optional[MQTTRouter]:
    """Get or create global MQTT router instance."""
    global _mqtt_router
    if _mqtt_router is None and mqtt_service:
        _mqtt_router = MQTTRouter(mqtt_service)
    return _mqtt_router


def set_mqtt_router(router: MQTTRouter):
    """Set global MQTT router instance."""
    global _mqtt_router
    _mqtt_router = router
