"""
Input validation framework for ConsultEase system.
Provides comprehensive validation for all user inputs to prevent security vulnerabilities
and ensure data integrity, especially important for Raspberry Pi deployment.
"""

import re
import logging
from typing import List, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """
    Comprehensive input validation framework with security focus.
    """

    # RFID UID patterns (common formats)
    RFID_UID_PATTERNS = [
        r'^[A-F0-9]{8}$',      # 4-byte UID (8 hex chars)
        r'^[A-F0-9]{14}$',     # 7-byte UID (14 hex chars)
        r'^[A-F0-9]{16}$',     # 8-byte UID (16 hex chars)
        r'^[A-F0-9]{20}$',     # 10-byte UID (20 hex chars)
    ]

    # BLE ID patterns (UUID format and MAC address format)
    BLE_ID_PATTERN = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    MAC_ADDRESS_PATTERN = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'

    # MQTT topic pattern (alphanumeric, hyphens, underscores, forward slashes)
    MQTT_TOPIC_PATTERN = r'^[a-zA-Z0-9/_-]+$'

    # Email pattern (basic validation)
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Name pattern (letters, spaces, hyphens, apostrophes)
    NAME_PATTERN = r'^[a-zA-Z\s\'-\.]{2,50}$'

    # Department pattern (letters, spaces, hyphens, ampersands)
    DEPARTMENT_PATTERN = r'^[a-zA-Z\s\-&]{2,100}$'

    @staticmethod
    def validate_rfid_uid(uid: str) -> Tuple[bool, List[str]]:
        """
        Validate RFID UID format.

        Args:
            uid: RFID UID string to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not uid:
            errors.append("RFID UID cannot be empty")
            return False, errors

        # Remove any whitespace and convert to uppercase
        uid = uid.strip().upper()

        # Check length constraints
        if len(uid) < 8 or len(uid) > 20:
            errors.append("RFID UID must be between 8 and 20 characters")

        # Check against known patterns
        valid_pattern = False
        for pattern in InputValidator.RFID_UID_PATTERNS:
            if re.match(pattern, uid):
                valid_pattern = True
                break

        if not valid_pattern:
            errors.append("RFID UID must be a valid hexadecimal format (8, 14, 16, or 20 characters)")

        # Check for invalid characters
        if not re.match(r'^[A-F0-9]+$', uid):
            errors.append("RFID UID can only contain hexadecimal characters (0-9, A-F)")

        return len(errors) == 0, errors

    @staticmethod
    def validate_ble_id(ble_id: str) -> Tuple[bool, List[str]]:
        """
        Validate BLE ID (UUID or MAC address) format.

        Args:
            ble_id: BLE ID string to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not ble_id:
            errors.append("BLE ID cannot be empty")
            return False, errors

        # Remove any whitespace
        ble_id = ble_id.strip()

        # Check UUID format or MAC address format
        is_uuid = re.match(InputValidator.BLE_ID_PATTERN, ble_id)
        is_mac = re.match(InputValidator.MAC_ADDRESS_PATTERN, ble_id)

        if not is_uuid and not is_mac:
            errors.append("BLE ID must be a valid UUID format (e.g., 12345678-1234-1234-1234-123456789abc) or MAC address format (e.g., AA:BB:CC:DD:EE:FF)")

        return len(errors) == 0, errors

    @staticmethod
    def validate_mqtt_topic(topic: str) -> Tuple[bool, List[str]]:
        """
        Validate MQTT topic format.

        Args:
            topic: MQTT topic string to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not topic:
            errors.append("MQTT topic cannot be empty")
            return False, errors

        # Remove any whitespace
        topic = topic.strip()

        # Check length constraints
        if len(topic) < 1 or len(topic) > 255:
            errors.append("MQTT topic must be between 1 and 255 characters")

        # Check pattern
        if not re.match(InputValidator.MQTT_TOPIC_PATTERN, topic):
            errors.append("MQTT topic can only contain letters, numbers, hyphens, underscores, and forward slashes")

        # Check for invalid patterns
        if topic.startswith('/') or topic.endswith('/'):
            errors.append("MQTT topic cannot start or end with a forward slash")

        if '//' in topic:
            errors.append("MQTT topic cannot contain consecutive forward slashes")

        return len(errors) == 0, errors

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, List[str]]:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not email:
            errors.append("Email address cannot be empty")
            return False, errors

        # Remove any whitespace
        email = email.strip().lower()

        # Check length constraints
        if len(email) > 254:
            errors.append("Email address is too long (maximum 254 characters)")

        # Check pattern
        if not re.match(InputValidator.EMAIL_PATTERN, email):
            errors.append("Email address format is invalid")

        return len(errors) == 0, errors

    @staticmethod
    def validate_name(name: str) -> Tuple[bool, List[str]]:
        """
        Validate person name format.

        Args:
            name: Name to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not name:
            errors.append("Name cannot be empty")
            return False, errors

        # Remove extra whitespace
        name = ' '.join(name.strip().split())

        # Check length constraints
        if len(name) < 2:
            errors.append("Name must be at least 2 characters long")
        elif len(name) > 50:
            errors.append("Name cannot exceed 50 characters")

        # Check pattern
        if not re.match(InputValidator.NAME_PATTERN, name):
            errors.append("Name can only contain letters, spaces, hyphens, apostrophes, and periods")

        return len(errors) == 0, errors

    @staticmethod
    def validate_department(department: str) -> Tuple[bool, List[str]]:
        """
        Validate department name format.

        Args:
            department: Department name to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not department:
            errors.append("Department cannot be empty")
            return False, errors

        # Remove extra whitespace
        department = ' '.join(department.strip().split())

        # Check length constraints
        if len(department) < 2:
            errors.append("Department name must be at least 2 characters long")
        elif len(department) > 100:
            errors.append("Department name cannot exceed 100 characters")

        # Check pattern
        if not re.match(InputValidator.DEPARTMENT_PATTERN, department):
            errors.append("Department name can only contain letters, spaces, hyphens, and ampersands")

        return len(errors) == 0, errors

    @staticmethod
    def validate_consultation_message(message: str) -> Tuple[bool, List[str]]:
        """
        Validate consultation request message.

        Args:
            message: Consultation message to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if not message:
            errors.append("Consultation message cannot be empty")
            return False, errors

        # Remove extra whitespace
        message = message.strip()

        # Check length constraints
        if len(message) < 10:
            errors.append("Consultation message must be at least 10 characters long")
        elif len(message) > 1000:
            errors.append("Consultation message cannot exceed 1000 characters")

        # Check for potentially harmful content
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed'
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                errors.append("Consultation message contains potentially harmful content")
                break

        return len(errors) == 0, errors

    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 255, allow_html: bool = False) -> str:
        """
        Comprehensive input sanitization to prevent injection attacks.

        Args:
            input_str: String to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow basic HTML tags (default: False)

        Returns:
            Sanitized string
        """
        if not input_str:
            return ""

        # Remove extra whitespace
        sanitized = ' '.join(input_str.strip().split())

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].strip()

        if not allow_html:
            # Comprehensive HTML/XML escaping
            sanitized = sanitized.replace('&', '&amp;')
            sanitized = sanitized.replace('<', '&lt;')
            sanitized = sanitized.replace('>', '&gt;')
            sanitized = sanitized.replace('"', '&quot;')
            sanitized = sanitized.replace("'", '&#x27;')
            sanitized = sanitized.replace('/', '&#x2F;')

            # Remove potential script injection patterns
            script_patterns = [
                r'javascript:', r'vbscript:', r'onload=', r'onerror=', r'onclick=',
                r'onmouseover=', r'onfocus=', r'onblur=', r'onchange=', r'onsubmit=',
                r'<script', r'</script>', r'<iframe', r'</iframe>', r'<object', r'</object>',
                r'<embed', r'</embed>', r'<link', r'<meta', r'<style', r'</style>',
                r'expression\s*\(', r'url\s*\(', r'@import', r'behavior\s*:'
            ]

            for pattern in script_patterns:
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

        # Remove potential SQL injection patterns
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
            r'(--|#|/\*|\*/)',
            r'(\bOR\b.*=.*\bOR\b)',
            r'(\bAND\b.*=.*\bAND\b)',
            r'(\'.*\bOR\b.*\')',
            r'(\".*\bOR\b.*\")',
            r'(\;.*\b(SELECT|INSERT|UPDATE|DELETE)\b)'
        ]

        for pattern in sql_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        return sanitized

    @staticmethod
    def validate_mqtt_topic(topic: str) -> tuple[bool, list[str]]:
        """
        Validate MQTT topic name to prevent injection attacks.

        Args:
            topic: MQTT topic to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not topic:
            errors.append("MQTT topic cannot be empty")
            return False, errors

        if len(topic) > 255:
            errors.append("MQTT topic too long (max 255 characters)")

        # Check for invalid MQTT topic characters
        invalid_chars = ['+', '#', '\x00']
        for char in invalid_chars:
            if char in topic:
                errors.append(f"MQTT topic contains invalid character: {char}")

        # Check for topic injection patterns
        injection_patterns = [
            r'\.\./+',  # Path traversal
            r'/\.\.',   # Path traversal
            r'[<>"\']', # HTML/XML injection
            r'[\x00-\x1F\x7F]',  # Control characters
        ]

        for pattern in injection_patterns:
            if re.search(pattern, topic):
                errors.append("MQTT topic contains potentially harmful characters")
                break

        # Validate topic structure
        if topic.startswith('/') or topic.endswith('/'):
            errors.append("MQTT topic should not start or end with '/'")

        if '//' in topic:
            errors.append("MQTT topic should not contain empty levels")

        return len(errors) == 0, errors

    @staticmethod
    def validate_file_path(file_path: str) -> tuple[bool, list[str]]:
        """
        Validate file path to prevent directory traversal attacks.

        Args:
            file_path: File path to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        if not file_path:
            errors.append("File path cannot be empty")
            return False, errors

        # Check for directory traversal patterns
        traversal_patterns = [
            r'\.\./+',
            r'/\.\.',
            r'\.\.\\',
            r'\\\.\.',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'%252e%252e%252f',
            r'%252e%252e%255c'
        ]

        for pattern in traversal_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                errors.append("File path contains directory traversal patterns")
                break

        # Check for null bytes
        if '\x00' in file_path:
            errors.append("File path contains null bytes")

        # Check for absolute paths (should be relative)
        if file_path.startswith('/') or (len(file_path) > 1 and file_path[1] == ':'):
            errors.append("File path should be relative, not absolute")

        return len(errors) == 0, errors

    @staticmethod
    def sanitize_mqtt_payload(payload: str, max_length: int = 1024) -> str:
        """
        Sanitize MQTT payload to prevent injection attacks.

        Args:
            payload: MQTT payload to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized payload
        """
        if not payload:
            return ""

        # Basic sanitization
        sanitized = InputValidator.sanitize_input(payload, max_length, allow_html=False)

        # Additional MQTT-specific sanitization
        # Remove potential command injection patterns
        command_patterns = [
            r'[;&|`$()]',  # Shell metacharacters
            r'\\[rnt]',    # Escape sequences
        ]

        for pattern in command_patterns:
            sanitized = re.sub(pattern, '', sanitized)

        return sanitized


def validate_and_raise(validator_func, value: Any, field_name: str) -> Any:
    """
    Validate input and raise ValidationError if invalid.

    Args:
        validator_func: Validation function to call
        value: Value to validate
        field_name: Name of the field being validated

    Returns:
        The validated value

    Raises:
        ValidationError: If validation fails
    """
    is_valid, errors = validator_func(value)
    if not is_valid:
        error_msg = f"Validation failed for {field_name}: {'; '.join(errors)}"
        logger.warning(error_msg)
        raise ValidationError(error_msg)

    return value


# Convenience functions for common validations
def validate_rfid_uid_safe(uid: str) -> str:
    """Validate RFID UID and raise exception if invalid."""
    return validate_and_raise(InputValidator.validate_rfid_uid, uid, "RFID UID")

def validate_ble_id_safe(ble_id: str) -> str:
    """Validate BLE ID and raise exception if invalid."""
    return validate_and_raise(InputValidator.validate_ble_id, ble_id, "BLE ID")

def validate_mqtt_topic_safe(topic: str) -> str:
    """Validate MQTT topic and raise exception if invalid."""
    return validate_and_raise(InputValidator.validate_mqtt_topic, topic, "MQTT topic")

def validate_email_safe(email: str) -> str:
    """Validate email and raise exception if invalid."""
    return validate_and_raise(InputValidator.validate_email, email, "email address")

def validate_name_safe(name: str) -> str:
    """Validate name and raise exception if invalid."""
    return validate_and_raise(InputValidator.validate_name, name, "name")

def validate_department_safe(department: str) -> str:
    """Validate department and raise exception if invalid."""
    return validate_and_raise(InputValidator.validate_department, department, "department")
