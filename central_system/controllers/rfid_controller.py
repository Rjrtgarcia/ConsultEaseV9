import logging
from ..services import get_rfid_service
from ..models import Student, get_db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RFIDController:
    """
    Controller for handling RFID card scanning and student verification.
    """

    def __init__(self):
        """
        Initialize the RFID controller.
        """
        self.rfid_service = get_rfid_service()
        self.callbacks = []

    def start(self):
        """
        Start the RFID service and register callback.
        """
        logger.info("Starting RFID controller")
        self.rfid_service.register_callback(self.on_rfid_read)
        self.rfid_service.start()

    def stop(self):
        """
        Stop the RFID service and unregister callbacks.
        """
        logger.info("Stopping RFID controller")
        # Unregister our callback from the RFID service
        try:
            self.rfid_service.unregister_callback(self.on_rfid_read)
        except Exception as e:
            logger.error(f"Error unregistering RFID callback: {str(e)}")

        # Stop the RFID service
        self.rfid_service.stop()

    def register_callback(self, callback):
        """
        Register a callback to be called when a student is verified.

        Args:
            callback (callable): Function that takes a Student object as argument
        """
        self.callbacks.append(callback)
        logger.info(f"Registered RFID controller callback: {callback.__name__}")

    def _notify_callbacks(self, student, rfid_uid, error_message=None):
        """
        Notify all callbacks with the student and RFID information.

        Args:
            student: The authenticated student object or None if not authenticated
            rfid_uid (str): The RFID UID that was read or None on error
            error_message (str, optional): Error message if authentication failed
        """
        for callback in self.callbacks:
            try:
                # Check if callback accepts error_message parameter
                import inspect
                params = inspect.signature(callback).parameters

                if len(params) >= 3:
                    # Callback accepts error_message
                    callback(student, rfid_uid, error_message)
                else:
                    # Callback doesn't accept error_message, use original signature
                    callback(student, rfid_uid)

            except Exception as e:
                logger.error(f"Error in RFID callback: {str(e)}")

    def on_rfid_read(self, student, rfid_uid):
        """
        Callback for RFID read events.

        Args:
            student: Student object if already validated, None otherwise
            rfid_uid (str): The RFID UID that was read
        """
        logger.info(f"RFID read: {rfid_uid}")

        # If we already have a validated student object, use it
        if student:
            self.handle_authenticated_student(student)
            return

        # Otherwise, look up the student in the database
        try:
            # Try to find student with this RFID in the database
            student = self.verify_student(rfid_uid)

            if student:
                # Student found, handle authentication
                self.handle_authenticated_student(student)
            else:
                # No student found with this RFID
                logger.warning(f"No student found with RFID: {rfid_uid}")
                self.handle_authentication_failure("Student not found")
        except Exception as e:
            logger.error(f"Error authenticating student: {str(e)}")
            self.handle_authentication_failure(f"Error: {str(e)}")

    def verify_student(self, rfid_uid):
        """
        Verify a student by RFID UID.

        Args:
            rfid_uid (str): RFID UID to verify

        Returns:
            Student: Student object if verified, None otherwise
        """
        try:
            db = get_db()

            # Try exact match first
            logger.info(f"Looking up student with RFID UID: {rfid_uid}")
            student = db.query(Student).filter(Student.rfid_uid == rfid_uid).first()

            # If no exact match, try case-insensitive match
            if not student:
                logger.info(f"No exact match found, trying case-insensitive match for RFID: {rfid_uid}")
                # For PostgreSQL
                try:
                    student = db.query(Student).filter(Student.rfid_uid.ilike(rfid_uid)).first()
                except:
                    # For SQLite
                    student = db.query(Student).filter(Student.rfid_uid.lower() == rfid_uid.lower()).first()

            if student:
                logger.info(f"Student verified: {student.name} with ID: {student.id}")
            else:
                # Log all students in the database for debugging
                all_students = db.query(Student).all()
                logger.warning(f"No student found for RFID {rfid_uid}")
                logger.info(f"Available students in database: {len(all_students)}")
                for s in all_students:
                    logger.info(f"  - ID: {s.id}, Name: {s.name}, RFID: {s.rfid_uid}")

            return student
        except Exception as e:
            logger.error(f"Error verifying student: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def refresh_student_data(self):
        """
        Refresh student data from the database.
        This ensures newly added students are immediately available for RFID scanning.

        Returns:
            list: List of all students in the database
        """
        try:
            db = get_db()
            students = db.query(Student).all()
            logger.info(f"Refreshed student data, found {len(students)} students")
            return students
        except Exception as e:
            logger.error(f"Error refreshing student data: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def get_device_status(self):
        """
        Get RFID device status.
        
        Returns:
            dict: Device status information
        """
        if self.rfid_service:
            return self.rfid_service.get_device_status()
        return {
            'device_path': None,
            'running': False,
            'status': 'disconnected'
        }

    def retry_connection(self):
        """
        Retry RFID device connection.

        Returns:
            bool: True if reconnection successful
        """
        if self.rfid_service:
            return self.rfid_service.retry_device_connection()
        return False

    def handle_authenticated_student(self, student):
        """
        Handle successful student authentication.

        Args:
            student: The authenticated student object
        """
        logger.info(f"Student authenticated: {student.name} (ID: {student.id})")

        # Notify callbacks with authenticated student
        self._notify_callbacks(student, student.rfid_uid)

        # Play success sound or visual feedback if available
        try:
            if hasattr(self, 'ui') and hasattr(self.ui, 'play_success_sound'):
                self.ui.play_success_sound()
        except Exception as e:
            logger.error(f"Error playing success sound: {str(e)}")

    def handle_authentication_failure(self, error_message):
        """
        Handle failed student authentication.

        Args:
            error_message (str): The error message explaining the failure
        """
        logger.warning(f"Authentication failed: {error_message}")

        # Notify callbacks with failure
        self._notify_callbacks(None, None, error_message)

        # Play error sound or visual feedback if available
        try:
            if hasattr(self, 'ui') and hasattr(self.ui, 'play_error_sound'):
                self.ui.play_error_sound()
        except Exception as e:
            logger.error(f"Error playing error sound: {str(e)}")