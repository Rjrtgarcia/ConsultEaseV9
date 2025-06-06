"""
Consultation Request Queue Service for ConsultEase system.
Handles queuing of consultation requests when faculty desk units are offline.
"""

import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import os

from ..models.base import get_db
from ..models.consultation import Consultation, ConsultationStatus
from ..models.faculty import Faculty
from ..utils.mqtt_utils import publish_mqtt_message
from ..utils.mqtt_topics import MQTTTopics

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    EXPIRED = "expired"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class QueuedConsultationRequest:
    """Represents a queued consultation request."""
    id: str
    consultation_id: int
    faculty_id: int
    student_id: int
    message: str
    course_code: Optional[str]
    priority: MessagePriority
    status: MessageStatus
    created_at: datetime
    retry_count: int
    next_retry: Optional[datetime]
    expires_at: datetime
    last_error: Optional[str] = None


class ConsultationQueueService:
    """
    Service for managing consultation request queues when faculty units are offline.
    """

    def __init__(self, db_path: str = "consultation_queue.db"):
        """
        Initialize the consultation queue service.

        Args:
            db_path: Path to SQLite database for persistent storage
        """
        self.db_path = db_path
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        self.faculty_online_status = {}  # Track faculty online status
        self.max_retry_attempts = 3
        self.retry_interval = timedelta(minutes=5)
        self.message_expiry = timedelta(hours=2)
        
        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database for queue persistence."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS queued_requests (
                        id TEXT PRIMARY KEY,
                        consultation_id INTEGER NOT NULL,
                        faculty_id INTEGER NOT NULL,
                        student_id INTEGER NOT NULL,
                        message TEXT NOT NULL,
                        course_code TEXT,
                        priority INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        retry_count INTEGER DEFAULT 0,
                        next_retry TEXT,
                        expires_at TEXT NOT NULL,
                        last_error TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_faculty_status 
                    ON queued_requests(faculty_id, status)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_next_retry 
                    ON queued_requests(next_retry)
                """)
                
                conn.commit()
                logger.info("Consultation queue database initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize queue database: {e}")
            raise

    def start(self):
        """Start the consultation queue service."""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        logger.info("Consultation Queue Service started")

    def stop(self):
        """Stop the consultation queue service."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Consultation Queue Service stopped")

    def queue_consultation_request(self, consultation: Consultation, priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Queue a consultation request for offline faculty.

        Args:
            consultation: Consultation object to queue
            priority: Message priority level

        Returns:
            bool: True if queued successfully
        """
        try:
            # Check if faculty is online
            if self.is_faculty_online(consultation.faculty_id):
                logger.debug(f"Faculty {consultation.faculty_id} is online, not queuing")
                return False

            # Create queued request
            request_id = f"{consultation.id}_{int(time.time())}"
            queued_request = QueuedConsultationRequest(
                id=request_id,
                consultation_id=consultation.id,
                faculty_id=consultation.faculty_id,
                student_id=consultation.student_id,
                message=consultation.request_message,
                course_code=consultation.course_code,
                priority=priority,
                status=MessageStatus.PENDING,
                created_at=datetime.now(),
                retry_count=0,
                next_retry=datetime.now(),
                expires_at=datetime.now() + self.message_expiry
            )

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO queued_requests 
                    (id, consultation_id, faculty_id, student_id, message, course_code, 
                     priority, status, created_at, retry_count, next_retry, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    queued_request.id,
                    queued_request.consultation_id,
                    queued_request.faculty_id,
                    queued_request.student_id,
                    queued_request.message,
                    queued_request.course_code,
                    queued_request.priority.value,
                    queued_request.status.value,
                    queued_request.created_at.isoformat(),
                    queued_request.retry_count,
                    queued_request.next_retry.isoformat(),
                    queued_request.expires_at.isoformat()
                ))
                conn.commit()

            logger.info(f"Queued consultation request {request_id} for offline faculty {consultation.faculty_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to queue consultation request: {e}")
            return False

    def update_faculty_status(self, faculty_id: int, is_online: bool):
        """
        Update faculty online status and trigger queue processing if coming online.

        Args:
            faculty_id: Faculty ID
            is_online: Whether faculty is online
        """
        with self.lock:
            previous_status = self.faculty_online_status.get(faculty_id, False)
            self.faculty_online_status[faculty_id] = is_online

            if not previous_status and is_online:
                # Faculty came online, process their queue
                logger.info(f"Faculty {faculty_id} came online, processing queued requests")
                self._process_faculty_queue(faculty_id)

    def is_faculty_online(self, faculty_id: int) -> bool:
        """
        Check if faculty is currently online.

        Args:
            faculty_id: Faculty ID

        Returns:
            bool: True if faculty is online
        """
        with self.lock:
            return self.faculty_online_status.get(faculty_id, False)

    def _process_faculty_queue(self, faculty_id: int):
        """
        Process all pending requests for a specific faculty.

        Args:
            faculty_id: Faculty ID to process queue for
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM queued_requests 
                    WHERE faculty_id = ? AND status = ? 
                    ORDER BY priority DESC, created_at ASC
                """, (faculty_id, MessageStatus.PENDING.value))

                requests = cursor.fetchall()

            for request_data in requests:
                request = self._row_to_request(request_data)
                if self._send_consultation_request(request):
                    self._mark_request_sent(request.id)
                else:
                    self._mark_request_failed(request.id, "Failed to send to faculty desk unit")

        except Exception as e:
            logger.error(f"Error processing faculty {faculty_id} queue: {e}")

    def _send_consultation_request(self, request: QueuedConsultationRequest) -> bool:
        """
        Send consultation request to faculty desk unit.

        Args:
            request: Queued consultation request

        Returns:
            bool: True if sent successfully
        """
        try:
            # Get faculty information
            db = get_db()
            try:
                faculty = db.query(Faculty).filter(Faculty.id == request.faculty_id).first()
                if not faculty:
                    logger.error(f"Faculty {request.faculty_id} not found")
                    return False

                # Prepare message data
                message_data = {
                    "consultation_id": request.consultation_id,
                    "student_id": request.student_id,
                    "faculty_id": request.faculty_id,
                    "faculty_name": faculty.name,
                    "message": request.message,
                    "course_code": request.course_code,
                    "timestamp": datetime.now().isoformat(),
                    "priority": request.priority.name
                }

                # Send to faculty-specific topic
                faculty_topic = MQTTTopics.get_faculty_messages_topic(request.faculty_id)
                success = publish_mqtt_message(faculty_topic, request.message, qos=2)

                if success:
                    logger.info(f"Sent queued consultation request {request.id} to faculty {request.faculty_id}")
                    return True
                else:
                    logger.warning(f"Failed to send queued request {request.id}")
                    return False

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error sending consultation request {request.id}: {e}")
            return False

    def _worker_loop(self):
        """Main worker loop for processing queued requests."""
        while self.running:
            try:
                # Process retry attempts
                self._process_retry_queue()
                
                # Clean up expired requests
                self._cleanup_expired_requests()
                
                # Sleep for a short interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in consultation queue worker loop: {e}")
                time.sleep(60)  # Wait longer on error

    def _process_retry_queue(self):
        """Process requests that are ready for retry."""
        try:
            now = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM queued_requests 
                    WHERE status = ? AND next_retry <= ? AND retry_count < ?
                    ORDER BY priority DESC, next_retry ASC
                """, (MessageStatus.FAILED.value, now.isoformat(), self.max_retry_attempts))

                requests = cursor.fetchall()

            for request_data in requests:
                request = self._row_to_request(request_data)
                
                # Check if faculty is online
                if self.is_faculty_online(request.faculty_id):
                    if self._send_consultation_request(request):
                        self._mark_request_sent(request.id)
                    else:
                        self._increment_retry_count(request.id)

        except Exception as e:
            logger.error(f"Error processing retry queue: {e}")

    def _cleanup_expired_requests(self):
        """Remove expired requests from the queue."""
        try:
            now = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM queued_requests 
                    WHERE expires_at <= ? OR 
                          (status = ? AND retry_count >= ?)
                """, (now.isoformat(), MessageStatus.FAILED.value, self.max_retry_attempts))
                
                deleted_count = cursor.rowcount
                conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired consultation requests")

        except Exception as e:
            logger.error(f"Error cleaning up expired requests: {e}")

    def get_queue_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the consultation queue.

        Returns:
            dict: Queue statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(retry_count) as avg_retries
                    FROM queued_requests 
                    GROUP BY status
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = {
                        'count': row[1],
                        'avg_retries': row[2] or 0
                    }

                # Get faculty-specific stats
                cursor = conn.execute("""
                    SELECT faculty_id, COUNT(*) as pending_count
                    FROM queued_requests 
                    WHERE status = ?
                    GROUP BY faculty_id
                """, (MessageStatus.PENDING.value,))
                
                faculty_stats = {row[0]: row[1] for row in cursor.fetchall()}

                return {
                    'status_breakdown': stats,
                    'faculty_pending': faculty_stats,
                    'total_online_faculty': sum(1 for online in self.faculty_online_status.values() if online),
                    'total_tracked_faculty': len(self.faculty_online_status)
                }

        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {}


# Global service instance
_consultation_queue_service: Optional[ConsultationQueueService] = None


def get_consultation_queue_service() -> ConsultationQueueService:
    """Get the global consultation queue service instance."""
    global _consultation_queue_service
    if _consultation_queue_service is None:
        _consultation_queue_service = ConsultationQueueService()
    return _consultation_queue_service
