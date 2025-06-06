import logging
import datetime
from ..models import Consultation, ConsultationStatus, get_db
from ..utils.mqtt_utils import publish_consultation_request, publish_mqtt_message
from ..utils.mqtt_topics import MQTTTopics
from ..utils.cache_manager import invalidate_consultation_cache
from ..services.consultation_queue_service import get_consultation_queue_service, MessagePriority
from sqlalchemy.orm import joinedload
import json

# Set up logging
logger = logging.getLogger(__name__)

class ConsultationController:
    """
    Controller for managing consultation requests.
    """

    def __init__(self):
        """
        Initialize the consultation controller.
        """
        self.callbacks = []
        self.queue_service = get_consultation_queue_service()

    def start(self):
        """
        Start the consultation controller.
        """
        logger.info("Starting Consultation controller")
        # Start the consultation queue service
        self.queue_service.start()
        # Async MQTT service is managed globally, no need to connect here

    def stop(self):
        """
        Stop the consultation controller.
        """
        logger.info("Stopping Consultation controller")

    def register_callback(self, callback):
        """
        Register a callback to be called when a consultation status changes.

        Args:
            callback (callable): Function that takes a Consultation object as argument
        """
        self.callbacks.append(callback)
        logger.info(f"Registered Consultation controller callback: {callback.__name__}")

    def _notify_callbacks(self, consultation):
        """
        Notify all registered callbacks with the updated consultation information.

        Args:
            consultation (Consultation): Updated consultation object
        """
        for callback in self.callbacks:
            try:
                callback(consultation)
            except Exception as e:
                logger.error(f"Error in Consultation controller callback: {str(e)}")

    def create_consultation(self, student_id, faculty_id, request_message, course_code=None):
        """
        Create a new consultation request.

        Args:
            student_id (int): Student ID
            faculty_id (int): Faculty ID
            request_message (str): Consultation request message
            course_code (str, optional): Course code

        Returns:
            Consultation: New consultation object or None if error
        """
        db = get_db()
        try:
            logger.info(f"Creating new consultation request (Student: {student_id}, Faculty: {faculty_id})")

            # Create new consultation
            consultation = Consultation(
                student_id=student_id,
                faculty_id=faculty_id,
                request_message=request_message,
                course_code=course_code,
                status=ConsultationStatus.PENDING,
                requested_at=datetime.datetime.now()
            )

            db.add(consultation)
            db.commit()

            logger.info(f"Created consultation request: {consultation.id} (Student: {student_id}, Faculty: {faculty_id})")

            # Publish consultation using the optimized method with offline queuing
            publish_success = self._publish_consultation(consultation)

            if publish_success:
                logger.info(f"Successfully published consultation request {consultation.id} to faculty desk unit")
            else:
                # Try to queue the consultation for offline faculty
                queue_success = self.queue_service.queue_consultation_request(consultation, MessagePriority.NORMAL)
                if queue_success:
                    logger.info(f"Queued consultation request {consultation.id} for offline faculty {faculty_id}")
                else:
                    logger.error(f"Failed to publish or queue consultation request {consultation.id}")

            # Invalidate consultation cache for both student and faculty
            try:
                invalidate_consultation_cache(student_id)
                invalidate_consultation_cache(faculty_id)
            except Exception as e:
                logger.warning(f"Failed to invalidate consultation cache: {str(e)}")

            # Notify callbacks
            self._notify_callbacks(consultation)

            return consultation

        except Exception as e:
            logger.error(f"Error creating consultation: {str(e)}")
            db.rollback()
            return None
        finally:
            # Ensure database session is always closed
            db.close()

    def _publish_consultation(self, consultation):
        """
        Publish consultation to MQTT using async service.

        Args:
            consultation (Consultation): Consultation object to publish
        """
        try:
            # Get a new database session and fetch the consultation with all related objects
            db = get_db(force_new=True)

            # Instead of refreshing, query for the consultation by ID to ensure it's attached to this session
            consultation_id = consultation.id
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()

            if not consultation:
                logger.error(f"Consultation with ID {consultation_id} not found in database")
                return False

            # Explicitly load the related objects to avoid lazy loading issues
            student = consultation.student
            faculty = consultation.faculty

            if not student:
                logger.error(f"Student not found for consultation {consultation_id}")
                return False

            if not faculty:
                logger.error(f"Faculty not found for consultation {consultation_id}")
                return False

            # Prepare consultation data for async publishing
            consultation_data = {
                'id': consultation.id,
                'student_id': student.id,
                'student_name': student.name,
                'student_department': student.department,
                'faculty_id': faculty.id,
                'faculty_name': faculty.name,
                'request_message': consultation.request_message,
                'course_code': consultation.course_code,
                'status': consultation.status.value,
                'requested_at': consultation.requested_at.isoformat() if consultation.requested_at else None
            }

            logger.info(f"Publishing consultation request {consultation.id} for faculty {faculty.id} using async MQTT")

            # Use the async MQTT utility function
            success = publish_consultation_request(consultation_data)

            # Also publish to legacy topic for backward compatibility
            message = f"Student: {student.name}\n"
            if consultation.course_code:
                message += f"Course: {consultation.course_code}\n"
            message += f"Request: {consultation.request_message}"

            legacy_topic = MQTTTopics.LEGACY_FACULTY_MESSAGES
            legacy_success = publish_mqtt_message(legacy_topic, message, qos=2)

            # Publish to faculty-specific plain text topic
            faculty_messages_topic = MQTTTopics.get_faculty_messages_topic(faculty_id)
            faculty_success = publish_mqtt_message(faculty_messages_topic, message, qos=2)

            # Close the database session
            db.close()

            overall_success = success or legacy_success or faculty_success
            if overall_success:
                logger.info(f"Successfully published consultation request {consultation.id} using async MQTT")
            else:
                logger.error(f"Failed to publish consultation request {consultation.id} using async MQTT")

            return overall_success
        except Exception as e:
            logger.error(f"Error publishing consultation: {str(e)}")
            return False

    def update_consultation_status(self, consultation_id, status):
        """
        Update consultation status.

        Args:
            consultation_id (int): Consultation ID
            status (ConsultationStatus): New status

        Returns:
            Consultation: Updated consultation object or None if error
        """
        db = get_db()
        try:
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()

            if not consultation:
                logger.error(f"Consultation not found: {consultation_id}")
                return None

            # Store old status for logging
            old_status = consultation.status

            # Update status and timestamp
            consultation.status = status

            if status == ConsultationStatus.ACCEPTED:
                consultation.accepted_at = datetime.datetime.now()
            elif status == ConsultationStatus.BUSY:
                consultation.busy_at = datetime.datetime.now()
            elif status == ConsultationStatus.COMPLETED:
                consultation.completed_at = datetime.datetime.now()
            elif status == ConsultationStatus.CANCELLED:
                # No specific timestamp for cancellation, but we could add one if needed
                pass

            db.commit()

            logger.info(f"Updated consultation status: {consultation.id} ({old_status.value} -> {status.value})")

            # Don't republish consultation as this confuses the faculty desk unit
            # The faculty already responded, no need to send it back to them
            
            # Invalidate cache for both student and faculty
            try:
                invalidate_consultation_cache(consultation.student_id)
                invalidate_consultation_cache(consultation.faculty_id)
                logger.debug(f"Invalidated consultation cache for student {consultation.student_id} and faculty {consultation.faculty_id}")
            except Exception as e:
                logger.warning(f"Failed to invalidate consultation cache: {str(e)}")

            # Notify callbacks with the updated consultation
            self._notify_callbacks(consultation)

            # Publish consultation status update to MQTT
            try:
                topic = f"consultease/consultations/{consultation.id}/status"
                payload_dict = {
                    'consultation_id': consultation.id,
                    'status': status.value,
                    'student_id': consultation.student_id,
                    'faculty_id': consultation.faculty_id,
                    'requested_at': consultation.requested_at.isoformat() if consultation.requested_at else None,
                    'updated_at': datetime.datetime.now().isoformat() # Add a timestamp for the update itself
                }
                payload = json.dumps(payload_dict)
                if publish_mqtt_message(topic, payload, qos=1):
                    logger.info(f"Published consultation status update to MQTT topic {topic}")
                else:
                    logger.warning(f"Failed to publish consultation status update to MQTT topic {topic}")
            except Exception as e:
                logger.error(f"Error publishing consultation status update to MQTT: {str(e)}")

            # If the status is CANCELLED, send an additional specific notification to the faculty unit
            if status == ConsultationStatus.CANCELLED and consultation.faculty_id:
                try:
                    faculty_topic = f"consultease/faculty/{consultation.faculty_id}/messages"
                    # Payload for faculty unit about the cancellation
                    cancellation_payload_dict = {
                        'type': 'consultation_cancellation',  # To distinguish from new requests
                        'consultation_id': consultation.id,
                        'message': f"Consultation request ID {consultation.id} has been cancelled."
                    }
                    cancellation_payload = json.dumps(cancellation_payload_dict)
                    
                    if publish_mqtt_message(faculty_topic, cancellation_payload, qos=1):
                        logger.info(f"Published cancellation notification to faculty MQTT topic {faculty_topic} for consultation {consultation.id}")
                    else:
                        logger.warning(f"Failed to publish cancellation notification to faculty MQTT topic {faculty_topic} for consultation {consultation.id}")
                except Exception as e:
                    logger.error(f"Error publishing cancellation notification to faculty MQTT: {str(e)}")

            return consultation

        except Exception as e:
            logger.error(f"Error updating consultation status: {str(e)}")
            db.rollback()
            return None
        finally:
            # Always close the database session
            # ✅ CRITICAL FIX: Always close the database session
            db.close()

    def cancel_consultation(self, consultation_id):
        """
        Cancel a consultation request.

        Args:
            consultation_id (int): Consultation ID

        Returns:
            Consultation: Updated consultation object or None if error
        """
        return self.update_consultation_status(consultation_id, ConsultationStatus.CANCELLED)

    def get_consultations(self, student_id=None, faculty_id=None, status=None):
        """
        Get consultations, optionally filtered by student, faculty, or status.

        Args:
            student_id (int, optional): Filter by student ID
            faculty_id (int, optional): Filter by faculty ID
            status (ConsultationStatus, optional): Filter by status

        Returns:
            list: List of Consultation objects
        """
        db = get_db()
        try:
            query = db.query(Consultation).options(
                joinedload(Consultation.faculty),
                joinedload(Consultation.student)
            )

            # Apply filters
            if student_id is not None:
                query = query.filter(Consultation.student_id == student_id)

            if faculty_id is not None:
                query = query.filter(Consultation.faculty_id == faculty_id)

            if status is not None:
                query = query.filter(Consultation.status == status)

            # Order by requested_at (newest first)
            query = query.order_by(Consultation.requested_at.desc())

            # Execute query
            consultations = query.all()

            return consultations

        except Exception as e:
            logger.error(f"Error getting consultations: {str(e)}")
            return []
        finally:
            # ✅ FIXED: Ensure database session is always closed
            db.close()

    def get_consultation_by_id(self, consultation_id):
        """
        Get a consultation by ID.

        Args:
            consultation_id (int): Consultation ID

        Returns:
            Consultation: Consultation object or None if not found
        """
        db = get_db()
        try:
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            return consultation
        except Exception as e:
            logger.error(f"Error getting consultation by ID: {str(e)}")
            return None
        finally:
            # ✅ FIXED: Ensure database session is always closed
            db.close()

    def test_faculty_desk_connection(self, faculty_id):
        """
        Test the connection to a faculty desk unit by sending a test message.

        Args:
            faculty_id (int): Faculty ID to test

        Returns:
            bool: True if the test message was sent successfully, False otherwise
        """
        try:
            # Get faculty information
            db = get_db()
            from ..models import Faculty
            faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()

            if not faculty:
                logger.error(f"Faculty not found: {faculty_id}")
                return False

            # Create a test message
            message = f"Test message from ConsultEase central system.\nTimestamp: {datetime.datetime.now().isoformat()}"

            # Publish to faculty-specific topic using standardized format
            faculty_requests_topic = MQTTTopics.get_faculty_requests_topic(faculty_id)
            payload = {
                'id': 0,
                'student_id': 0,
                'student_name': "System Test",
                'student_department': "System",
                'faculty_id': faculty_id,
                'faculty_name': faculty.name,
                'request_message': message,
                'course_code': "TEST",
                'status': "test",
                'requested_at': datetime.datetime.now().isoformat(),
                'message': message
            }

            # Publish using async MQTT service
            success_json = publish_mqtt_message(faculty_requests_topic, payload)

            # Publish to legacy plain text topic for backward compatibility
            success_text = publish_mqtt_message(MQTTTopics.LEGACY_FACULTY_MESSAGES, message, qos=2)

            # Publish to faculty-specific plain text topic
            faculty_messages_topic = MQTTTopics.get_faculty_messages_topic(faculty_id)
            success_faculty = publish_mqtt_message(faculty_messages_topic, message, qos=2)

            logger.info(f"Test message sent to faculty desk unit {faculty_id} ({faculty.name}) using async MQTT")
            logger.info(f"JSON topic success: {success_json}, Text topic success: {success_text}, Faculty topic success: {success_faculty}")

            return success_json or success_text or success_faculty
        except Exception as e:
            logger.error(f"Error testing faculty desk connection: {str(e)}")
            return False