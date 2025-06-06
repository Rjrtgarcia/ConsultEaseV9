"""
Faculty Response Controller for ConsultEase system.
Handles faculty responses (ACKNOWLEDGE, BUSY) from faculty desk units.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..models.base import get_db
from ..models.consultation import Consultation, ConsultationStatus
from ..utils.mqtt_utils import subscribe_to_topic, publish_mqtt_message
from ..utils.mqtt_topics import MQTTTopics

logger = logging.getLogger(__name__)


class FacultyResponseController:
    """
    Controller for handling faculty responses from desk units.
    """

    def __init__(self):
        """
        Initialize the faculty response controller.
        """
        self.callbacks = []

    def start(self):
        """
        Start the faculty response controller and subscribe to faculty response topics.
        """
        logger.info("Starting Faculty Response controller")
        
        # Add debug logging to confirm subscription setup
        logger.info("🔔 Subscribing to faculty response topics...")

        # Subscribe to faculty response updates using async MQTT service
        try:
            subscribe_to_topic("consultease/faculty/+/responses", self.handle_faculty_response)
            logger.info("✅ Successfully subscribed to: consultease/faculty/+/responses")
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to faculty responses: {e}")

        # Subscribe to faculty heartbeat for NTP sync status
        try:
            subscribe_to_topic("consultease/faculty/+/heartbeat", self.handle_faculty_heartbeat)
            logger.info("✅ Successfully subscribed to: consultease/faculty/+/heartbeat")
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to faculty heartbeat: {e}")
            
        logger.info("🎯 Faculty Response Controller started and waiting for messages...")

    def stop(self):
        """
        Stop the faculty response controller.
        """
        logger.info("Stopping Faculty Response controller")

    def register_callback(self, callback):
        """
        Register a callback to be called when a faculty response is received.

        Args:
            callback (callable): Function that takes response data as argument
        """
        self.callbacks.append(callback)
        logger.info(f"Registered Faculty Response controller callback: {callback.__name__}")

    def _notify_callbacks(self, response_data):
        """
        Notify all registered callbacks with the response data.

        Args:
            response_data (dict): Faculty response data
        """
        for callback in self.callbacks:
            try:
                callback(response_data)
            except Exception as e:
                logger.error(f"Error in Faculty Response controller callback: {str(e)}")

    def handle_faculty_response(self, topic: str, data: Any):
        """
        Handle faculty response from MQTT.

        Args:
            topic (str): MQTT topic
            data (dict or str): Response data
        """
        # DEBUG: Log every message received to diagnose MQTT connectivity
        logger.info(f"🔥 FACULTY RESPONSE HANDLER TRIGGERED - Topic: {topic}, Data Type: {type(data)}")
        logger.info(f"🔥 Raw Data: {data}")
        
        try:
            # Parse response data
            if isinstance(data, str):
                try:
                    response_data = json.loads(data)
                    logger.info(f"🔥 Parsed JSON data: {response_data}")
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in faculty response: {data}")
                    return
            elif isinstance(data, dict):
                response_data = data
                logger.info(f"🔥 Dict data received: {response_data}")
            else:
                logger.error(f"Invalid data type for faculty response: {type(data)}")
                return

            # Extract faculty ID from topic
            faculty_id = None
            try:
                faculty_id = int(topic.split("/")[2])
                logger.info(f"🔥 Extracted faculty ID: {faculty_id}")
            except (IndexError, ValueError):
                logger.error(f"Could not extract faculty ID from topic: {topic}")
                return

            # Validate required fields
            required_fields = ['faculty_id', 'response_type', 'message_id']
            for field in required_fields:
                if field not in response_data:
                    logger.error(f"Missing required field '{field}' in faculty response")
                    return

            response_type = response_data.get('response_type')
            message_id = response_data.get('message_id')
            faculty_name = response_data.get('faculty_name', 'Unknown')

            logger.info(f"Received {response_type} response from faculty {faculty_id} ({faculty_name}) for message {message_id}")

            # Process the response
            success = self._process_faculty_response(response_data)

            if success:
                # Notify callbacks
                self._notify_callbacks(response_data)

                # Publish notification about the response
                notification = {
                    'type': 'faculty_response',
                    'faculty_id': faculty_id,
                    'faculty_name': faculty_name,
                    'response_type': response_type,
                    'message_id': message_id,
                    'timestamp': datetime.now().isoformat()
                }
                publish_mqtt_message(MQTTTopics.SYSTEM_NOTIFICATIONS, notification)

        except Exception as e:
            logger.error(f"Error handling faculty response: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def handle_faculty_heartbeat(self, topic: str, data: Any):
        """
        Handle faculty heartbeat messages for NTP sync status and system health.

        Args:
            topic (str): MQTT topic
            data (dict or str): Heartbeat data
        """
        try:
            # Parse heartbeat data
            if isinstance(data, str):
                try:
                    heartbeat_data = json.loads(data)
                except json.JSONDecodeError:
                    logger.debug(f"Non-JSON heartbeat data: {data}")
                    return
            elif isinstance(data, dict):
                heartbeat_data = data
            else:
                return

            # Extract faculty ID from topic
            faculty_id = None
            try:
                faculty_id = int(topic.split("/")[2])
            except (IndexError, ValueError):
                return

            # Log NTP sync status if present
            if 'ntp_sync_status' in heartbeat_data:
                ntp_status = heartbeat_data['ntp_sync_status']
                if ntp_status in ['FAILED', 'SYNCING']:
                    logger.warning(f"Faculty {faculty_id} NTP sync status: {ntp_status}")
                elif ntp_status == 'SYNCED':
                    logger.debug(f"Faculty {faculty_id} NTP sync: {ntp_status}")

            # Log system health issues
            if 'free_heap' in heartbeat_data:
                free_heap = heartbeat_data.get('free_heap', 0)
                if free_heap < 50000:  # Less than 50KB free
                    logger.warning(f"Faculty {faculty_id} low memory: {free_heap} bytes")

        except Exception as e:
            logger.debug(f"Error processing faculty heartbeat: {str(e)}")

    def _process_faculty_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Process faculty response and update consultation status.

        Args:
            response_data (dict): Faculty response data. Expected to contain:
                                  'faculty_id': ID of the faculty responding (from payload)
                                  'message_id': consultation_id being responded to
                                  'response_type': e.g., "ACKNOWLEDGE", "REJECTED", "COMPLETED"

        Returns:
            bool: True if processed successfully
        """
        try:
            faculty_id_from_payload = response_data.get('faculty_id')
            response_type = response_data.get('response_type')
            consultation_id_from_response = response_data.get('message_id')

            if not consultation_id_from_response:
                logger.error("Faculty response missing 'message_id' (consultation_id).")
                return False
            
            if not faculty_id_from_payload: # Also ensure faculty_id is in payload
                logger.error("Faculty response missing 'faculty_id' in payload.")
                return False

            # CRITICAL FIX: Convert consultation_id from string to integer
            # ESP32 sends consultation_id as string, but database expects integer
            try:
                consultation_id_int = int(consultation_id_from_response)
                logger.debug(f"Converted consultation_id from '{consultation_id_from_response}' (string) to {consultation_id_int} (int)")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid consultation_id format: '{consultation_id_from_response}' cannot be converted to integer: {e}")
                return False

            # CRITICAL FIX: Convert faculty_id from string to integer for comparison
            try:
                faculty_id_int = int(faculty_id_from_payload)
                logger.debug(f"Converted faculty_id from '{faculty_id_from_payload}' (string) to {faculty_id_int} (int)")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid faculty_id format: '{faculty_id_from_payload}' cannot be converted to integer: {e}")
                return False

            db = get_db()
            try:
                # Use the converted integer consultation_id for database query
                consultation = db.query(Consultation).filter(Consultation.id == consultation_id_int).first()

                if not consultation:
                    logger.warning(f"Consultation ID {consultation_id_int} (converted from '{consultation_id_from_response}') not found in database.")
                    return False

                # Verification - compare as integers
                if consultation.faculty_id != faculty_id_int:
                    logger.warning(f"Faculty ID mismatch for consultation {consultation.id}. "
                                   f"Response payload for faculty {faculty_id_int} (converted from '{faculty_id_from_payload}'), "
                                   f"but consultation belongs to faculty {consultation.faculty_id}. Ignoring response.")
                    return False

                if consultation.status != ConsultationStatus.PENDING:
                    logger.warning(f"Consultation {consultation.id} is no longer PENDING (current status: {consultation.status.value}). "
                                   f"Response '{response_type}' may be late or redundant. Ignoring response.")
                    return False

                logger.info(f"Processing response '{response_type}' for PENDING consultation {consultation.id} (Faculty: {consultation.faculty_id})")

                new_status_enum: Optional[ConsultationStatus] = None
                if response_type == "ACKNOWLEDGE" or response_type == "ACCEPTED":
                    new_status_enum = ConsultationStatus.ACCEPTED
                elif response_type == "BUSY" or response_type == "UNAVAILABLE":
                    new_status_enum = ConsultationStatus.BUSY
                elif response_type == "REJECTED" or response_type == "DECLINED": # Allow "DECLINED"
                    new_status_enum = ConsultationStatus.CANCELLED
                elif response_type == "COMPLETED":
                    new_status_enum = ConsultationStatus.COMPLETED

                if new_status_enum:
                    # Import ConsultationController locally or ensure it's available via __init__
                    from .consultation_controller import ConsultationController as SystemConsultationController
                    cc = SystemConsultationController()
                    updated_consultation = cc.update_consultation_status(consultation.id, new_status_enum)
                    
                    if updated_consultation:
                        logger.info(f"✅ Successfully updated consultation {consultation.id} to status {new_status_enum.value} via ConsultationController.")
                        # Add consultation_id and student_id to response_data for callbacks, if not already there
                        response_data['consultation_id'] = consultation.id 
                        response_data['student_id'] = consultation.student_id
                        return True
                    else:
                        logger.error(f"Failed to update consultation {consultation.id} to {new_status_enum.value} using ConsultationController.")
                        return False
                else:
                    logger.warning(f"Unknown or unhandled response_type: '{response_type}' for consultation {consultation.id}. Status not changed.")
                    return False
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Critical error in _process_faculty_response: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def get_response_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about faculty responses.

        Returns:
            dict: Response statistics
        """
        try:
            db = get_db()
            try:
                # Get response statistics from the database
                total_acknowledged = db.query(Consultation).filter(
                    Consultation.status == ConsultationStatus.ACCEPTED
                ).count()

                total_busy = db.query(Consultation).filter(
                    Consultation.status == ConsultationStatus.BUSY
                ).count()

                total_declined = db.query(Consultation).filter(
                    Consultation.status == ConsultationStatus.CANCELLED
                ).count()

                total_pending = db.query(Consultation).filter(
                    Consultation.status == ConsultationStatus.PENDING
                ).count()

                total_completed = db.query(Consultation).filter(
                    Consultation.status == ConsultationStatus.COMPLETED
                ).count()

                total_responded = total_acknowledged + total_busy + total_declined
                total_all = total_responded + total_pending + total_completed

                return {
                    'total_acknowledged': total_acknowledged,
                    'total_busy': total_busy,
                    'total_declined': total_declined,
                    'total_completed': total_completed,
                    'total_pending': total_pending,
                    'total_responded': total_responded,
                    'response_rate': (total_responded / max(1, total_all)) * 100
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error getting response statistics: {str(e)}")
            return {
                'total_acknowledged': 0,
                'total_busy': 0,
                'total_declined': 0,
                'total_completed': 0,
                'total_pending': 0,
                'total_responded': 0,
                'response_rate': 0
            }


# Global controller instance
_faculty_response_controller: Optional[FacultyResponseController] = None


def get_faculty_response_controller() -> FacultyResponseController:
    """Get the global faculty response controller instance."""
    global _faculty_response_controller
    if _faculty_response_controller is None:
        _faculty_response_controller = FacultyResponseController()
    return _faculty_response_controller
