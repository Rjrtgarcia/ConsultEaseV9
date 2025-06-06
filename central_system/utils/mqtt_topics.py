"""
Standardized MQTT topic definitions for ConsultEase.

This module provides a centralized place for all MQTT topic definitions
to ensure consistency across the system.
"""

class MQTTTopics:
    """
    MQTT topic definitions for ConsultEase.

    All topics should follow the pattern:
    consultease/<component>/<id>/<action>

    Where:
    - component: The component type (faculty, student, system)
    - id: The ID of the component (faculty ID, student ID, etc.)
    - action: The action being performed (status, requests, etc.)
    """

    # Faculty topics
    FACULTY_STATUS = "consultease/faculty/{faculty_id}/status"
    FACULTY_MAC_STATUS = "consultease/faculty/{faculty_id}/mac_status"
    FACULTY_REQUESTS = "consultease/faculty/{faculty_id}/requests"
    FACULTY_MESSAGES = "consultease/faculty/{faculty_id}/messages"
    FACULTY_RESPONSES = "consultease/faculty/{faculty_id}/responses"
    FACULTY_HEARTBEAT = "consultease/faculty/{faculty_id}/heartbeat"

    # System topics
    SYSTEM_NOTIFICATIONS = "consultease/system/notifications"
    SYSTEM_PING = "consultease/system/ping"

    # Legacy topics (for backward compatibility)
    LEGACY_FACULTY_STATUS = "professor/status"
    LEGACY_FACULTY_MESSAGES = "professor/messages"

    @staticmethod
    def get_faculty_status_topic(faculty_id):
        """Get the topic for faculty status updates."""
        return MQTTTopics.FACULTY_STATUS.format(faculty_id=faculty_id)

    @staticmethod
    def get_faculty_mac_status_topic(faculty_id):
        """Get the topic for faculty MAC address status updates."""
        return MQTTTopics.FACULTY_MAC_STATUS.format(faculty_id=faculty_id)

    @staticmethod
    def get_faculty_requests_topic(faculty_id):
        """Get the topic for faculty consultation requests."""
        return MQTTTopics.FACULTY_REQUESTS.format(faculty_id=faculty_id)

    @staticmethod
    def get_faculty_responses_topic(faculty_id):
        """Get the topic for faculty consultation responses."""
        return MQTTTopics.FACULTY_RESPONSES.format(faculty_id=faculty_id)

    @staticmethod
    def get_faculty_heartbeat_topic(faculty_id):
        """Get the topic for faculty heartbeat messages."""
        return MQTTTopics.FACULTY_HEARTBEAT.format(faculty_id=faculty_id)

    @staticmethod
    def get_faculty_messages_topic(faculty_id):
        """Get the topic for faculty messages."""
        return MQTTTopics.FACULTY_MESSAGES.format(faculty_id=faculty_id)
