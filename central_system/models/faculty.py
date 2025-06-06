from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .base import Base
import os
import re
import logging

logger = logging.getLogger(__name__)

class Faculty(Base):
    """
    Faculty model.
    Represents a faculty member in the system.
    """
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    ble_id = Column(String, unique=True, index=True)
    image_path = Column(String, nullable=True)  # Path to faculty image
    status = Column(Boolean, default=False)  # False = Unavailable, True = Available
    always_available = Column(Boolean, default=False)  # If True, faculty is always shown as available
    # NOTE: The room column is referenced in several places but has been removed from the model.
    # The code uses getattr(faculty, 'room', None) to safely handle this attribute's absence.
    # room = Column(String, nullable=True)  # Room where faculty is located
    last_seen = Column(DateTime, default=func.now())
    ntp_sync_status = Column(String, default='PENDING')  # NTP sync status from desk unit
    grace_period_active = Column(Boolean, default=False)  # Whether grace period is active
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Faculty {self.name}>"

    def to_dict(self):
        """
        Convert model instance to dictionary.
        """
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "email": self.email,
            "ble_id": self.ble_id,
            "image_path": self.image_path,
            "status": self.status,
            "always_available": self.always_available,
            "room": getattr(self, 'room', None),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "ntp_sync_status": self.ntp_sync_status,
            "grace_period_active": self.grace_period_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def get_image_path(self):
        """
        Get the full path to the faculty image.
        If no image is set, returns None.
        """
        if not self.image_path:
            return None

        # Check if the path is absolute
        if os.path.isabs(self.image_path):
            return self.image_path

        # Otherwise, assume it's relative to the images directory
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        images_dir = os.path.join(base_dir, 'images', 'faculty')

        # Create the directory if it doesn't exist
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        return os.path.join(images_dir, self.image_path)

    @staticmethod
    def validate_name(name):
        """
        Validate faculty name.

        Args:
            name (str): Faculty name to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not name or not isinstance(name, str):
            return False

        # Name should be at least 2 characters and contain only letters, spaces, dots, and hyphens
        if len(name.strip()) < 2:
            return False

        # Check for valid characters (letters, spaces, dots, hyphens, and apostrophes)
        pattern = r'^[A-Za-z\s.\'-]+$'
        return bool(re.match(pattern, name))

    @staticmethod
    def validate_email(email):
        """
        Validate email format.

        Args:
            email (str): Email to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False

        # Basic email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_ble_id(ble_id):
        """
        Validate BLE ID format (UUID or MAC address).

        Args:
            ble_id (str): BLE ID to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not ble_id or not isinstance(ble_id, str):
            return False

        # Check for UUID format
        uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        # Check for MAC address format (supports both : and - separators)
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'

        return bool(re.match(uuid_pattern, ble_id) or re.match(mac_pattern, ble_id))

    @staticmethod
    def normalize_mac_address(mac_address):
        """
        Normalize MAC address format to uppercase with colon separators.

        Args:
            mac_address (str): MAC address to normalize

        Returns:
            str: Normalized MAC address or original if not a MAC address
        """
        if not mac_address or not isinstance(mac_address, str):
            return mac_address

        # Check if it's a MAC address format
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if re.match(mac_pattern, mac_address):
            # Convert to uppercase and use colon separators
            return mac_address.upper().replace('-', ':')

        return mac_address

    @classmethod
    def create(cls, db, name, department, email, ble_id=None, **kwargs):
        """
        Create a new faculty with validation.

        Args:
            db: Database session
            name (str): Faculty name
            department (str): Faculty department
            email (str): Faculty email
            ble_id (str, optional): BLE ID for presence detection
            **kwargs: Additional attributes

        Returns:
            Faculty: Created faculty instance

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if not cls.validate_name(name):
            raise ValueError("Invalid faculty name. Name must be at least 2 characters and contain only letters, spaces, dots, and hyphens.")

        if not department or not isinstance(department, str) or len(department.strip()) < 2:
            raise ValueError("Invalid department. Department must be at least 2 characters.")

        if not cls.validate_email(email):
            raise ValueError("Invalid email format.")

        if ble_id and not cls.validate_ble_id(ble_id):
            raise ValueError("Invalid BLE ID format. Must be a valid UUID or MAC address.")

        # Check if email already exists
        existing = db.query(cls).filter(cls.email == email).first()
        if existing:
            raise ValueError(f"Faculty with email {email} already exists.")

        # Check if BLE ID already exists (if provided)
        if ble_id:
            existing = db.query(cls).filter(cls.ble_id == ble_id).first()
            if existing:
                raise ValueError(f"Faculty with BLE ID {ble_id} already exists.")

        # Create faculty
        faculty = cls(
            name=name,
            department=department,
            email=email,
            ble_id=ble_id,
            **kwargs
        )

        db.add(faculty)
        db.flush()  # Flush to get the ID

        logger.info(f"Created faculty: {faculty}")
        return faculty