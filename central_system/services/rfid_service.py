import logging
import threading
import time
import os
import sys
import subprocess
from PyQt5.QtCore import QObject, pyqtSignal

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RFIDService(QObject):
    """
    RFID Service for reading RFID cards via USB RFID reader.

    This service uses evdev to read input from a USB RFID reader
    which typically behaves like a keyboard.
    """
    # Signal to emit when a card is read
    card_read_signal = pyqtSignal(str)
    # Signal to emit when device status changes
    device_status_changed = pyqtSignal(str, str)  # status, message

    def __init__(self):
        super(RFIDService, self).__init__()
        self.os_platform = sys.platform
        self.device_path = os.environ.get('RFID_DEVICE_PATH', None)

        # Target RFID reader VID/PID
        self.target_vid = "ffff"
        self.target_pid = "0035"

        # Events and callbacks
        self.callbacks = []
        self.running = False
        self.read_thread = None

        # Connect the signal to the notification method to ensure thread safety
        self.card_read_signal.connect(self._notify_callbacks_safe)

        # Try to auto-detect RFID reader on initialization
        if not self.device_path and self.os_platform.startswith('linux'):
            # First try to find the target device by VID/PID
            if not self._find_device_by_vid_pid():
                # If not found by VID/PID, try generic detection
                self._detect_rfid_device()

        logger.info(f"RFID Service initialized (OS: {self.os_platform}, Device: {self.device_path})")

    def _find_device_by_vid_pid(self):
        """
        Find a USB device by VID/PID and determine its input device path.
        """
        try:
            # Use lsusb to find the device
            logger.info(f"Looking for USB device with VID:{self.target_vid} PID:{self.target_pid}")
            lsusb_output = subprocess.check_output(['lsusb'], universal_newlines=True)
            logger.info(f"Available USB devices:\n{lsusb_output}")

            # Look for our target device in lsusb output
            target_line = None
            for line in lsusb_output.split('\n'):
                if f"ID {self.target_vid}:{self.target_pid}" in line:
                    target_line = line
                    logger.info(f"Found target USB device: {line}")
                    break

            if not target_line:
                logger.warning(f"USB device with VID:{self.target_vid} PID:{self.target_pid} not found")
                return False

            # Attempt to find the corresponding input device
            try:
                import evdev
                devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

                # First try checking if any device's physical path contains the VID/PID
                for device in devices:
                    device_info = f"Device: {device.name} ({device.path})"
                    try:
                        phys = device.phys
                        if phys and (self.target_vid in phys.lower() and self.target_pid in phys.lower()):
                            logger.info(f"Found matching device by physical path: {device_info}")
                            self.device_path = device.path
                            return True
                    except Exception as e:
                        logger.debug(f"Error checking device physical path: {e}")

                    # Also log all device info for debugging
                    try:
                        info = f" - phys: {device.phys}"
                        if hasattr(device, 'info') and device.info:
                            info += f" - info: {device.info}"
                        logger.info(f"{device_info} {info}")
                    except Exception:
                        pass

                # If we haven't found it by physical path, try another approach
                # Let's check if there's a device that looks like an HID keyboard
                for device in devices:
                    if (evdev.ecodes.EV_KEY in device.capabilities() and
                        len(device.capabilities().get(evdev.ecodes.EV_KEY, [])) > 10):

                        # Check if this device behaves like a RFID reader
                        # RFID readers typically don't have modifiers like shift/control
                        key_caps = device.capabilities().get(evdev.ecodes.EV_KEY, [])
                        has_numerics = any(k in key_caps for k in range(evdev.ecodes.KEY_0, evdev.ecodes.KEY_9 + 1))
                        has_enter = evdev.ecodes.KEY_ENTER in key_caps

                        if has_numerics and has_enter:
                            logger.info(f"Found potential RFID reader: {device.name} ({device.path})")
                            self.device_path = device.path
                            return True

                logger.warning("No input device matching the target RFID reader found")
                return False

            except ImportError:
                logger.error("evdev library not installed. Please install it with: pip install evdev")
                return False

        except Exception as e:
            logger.error(f"Error finding device by VID/PID: {str(e)}")
            return False

    def _detect_rfid_device(self):
        """
        Auto-detect RFID device on Linux systems.
        """
        try:
            import evdev
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

            # Check all input devices
            for device in devices:
                # Log available devices to help debug
                device_info = f"Found input device: {device.name} ({device.path})"
                capabilities = []

                # Check device capabilities
                if evdev.ecodes.EV_KEY in device.capabilities():
                    capabilities.append("Keyboard")
                if evdev.ecodes.EV_ABS in device.capabilities():
                    capabilities.append("Touchscreen/Pad")
                if evdev.ecodes.EV_REL in device.capabilities():
                    capabilities.append("Mouse/Pointer")

                device_info += f" - Capabilities: {', '.join(capabilities)}"
                logger.info(device_info)

                # Look for devices that might be RFID readers
                # Many RFID readers present as HID keyboard devices
                if (
                    "rfid" in device.name.lower() or
                    "card" in device.name.lower() or
                    "reader" in device.name.lower() or
                    "hid" in device.name.lower() or
                    "usb" in device.name.lower()
                ):
                    # Check if it has keyboard capabilities
                    if evdev.ecodes.EV_KEY in device.capabilities():
                        key_caps = device.capabilities().get(evdev.ecodes.EV_KEY, [])
                        # RFID readers typically have number keys at minimum
                        key_count = len(key_caps)

                        if key_count > 10:  # It should have at least digit keys
                            self.device_path = device.path
                            logger.info(f"Auto-detected RFID reader: {device.name} ({device.path})")
                            return True

            logger.warning("No RFID reader device auto-detected. Will use physical device.")
            return False

        except ImportError:
            logger.error("evdev library not installed. Please install it with: pip install evdev")
            return False
        except Exception as e:
            logger.error(f"Error detecting RFID devices: {str(e)}")
            return False

    def start(self):
        """
        Start the RFID reading service.
        """
        if self.running:
            logger.warning("RFID Service is already running")
            return

        self.running = True

        # Only support Linux platform with physical RFID device
        if not self.os_platform.startswith('linux'):
            logger.error(f"RFID hardware mode not supported on {self.os_platform}")
            raise RuntimeError(f"RFID service requires Linux platform with physical RFID reader")

        # Ensure we have a device path
        if not self.device_path:
            if not self._find_device_by_vid_pid() and not self._detect_rfid_device():
                logger.error("No RFID device detected")
                raise RuntimeError("No RFID device found. Please ensure RFID reader is connected.")

        logger.info("Starting RFID Service with physical device")
        self.read_thread = threading.Thread(target=self._read_rfid_linux, daemon=True)
        self.read_thread.start()

    def stop(self):
        """
        Stop the RFID reading service.
        """
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        logger.info("RFID Service stopped")

    def register_callback(self, callback):
        """
        Register a callback function to be called when an RFID card is read.

        Args:
            callback (callable): Function that takes an RFID UID string as argument
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            callback_name = getattr(callback, '__name__', str(callback))
            logger.info(f"Registered RFID callback: {callback_name}")

    def unregister_callback(self, callback):
        """
        Unregister a previously registered callback.

        Args:
            callback (callable): Function to unregister
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            callback_name = getattr(callback, '__name__', str(callback))
            logger.info(f"Unregistered RFID callback: {callback_name}")

    def _notify_callbacks_safe(self, rfid_uid):
        """
        Thread-safe notification of callbacks via Qt signals.
        Also attempts to look up the student based on the RFID UID.

        Args:
            rfid_uid (str): The RFID UID that was read
        """
        logger.info(f"RFID Service notifying callbacks for UID: {rfid_uid}")

        # CRITICAL: Force a database session refresh to ensure we have the latest data
        try:
            from ..models import get_db
            db = get_db()
            # Force SQLAlchemy to create a new session
            db.close()
            db = get_db(force_new=True)
            logger.info("Forced database session refresh to ensure latest student data")
        except Exception as e:
            logger.error(f"Error refreshing database session: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

        # Attempt to verify the student immediately
        student = None
        try:
            from ..models import Student, get_db  # Lazy import to avoid circular dependencies
            db = get_db()

            # Log the query we're about to execute
            logger.info(f"Looking up student with RFID UID: {rfid_uid}")

            # Try an exact match first
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
                logger.info(f"Student verified by RFIDService: {student.name} with ID: {student.id}")
                # Log the student details for debugging
                logger.info(f"Student details - Name: {student.name}, Department: {student.department}, RFID: {student.rfid_uid}")
            else:
                # Log all students in the database for debugging
                all_students = db.query(Student).all()
                logger.warning(f"No student found for RFID {rfid_uid} by RFIDService")
                logger.info(f"Available students in database: {len(all_students)}")
                for s in all_students:
                    logger.info(f"  - ID: {s.id}, Name: {s.name}, RFID: {s.rfid_uid}")
        except Exception as e:
            logger.error(f"Error verifying student in RFIDService: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            student = None  # Ensure student is None if lookup fails

        # Make a copy of callbacks to avoid issues if callbacks are modified during iteration
        callbacks_to_notify = list(self.callbacks)
        logger.info(f"Number of callbacks to notify: {len(callbacks_to_notify)}")

        # Notify all registered callbacks
        for callback in callbacks_to_notify:
            try:
                if callback is None:
                    logger.warning("Skipping None callback")
                    continue

                callback_name = getattr(callback, '__name__', str(callback))
                logger.info(f"Calling callback: {callback_name} with student: {student is not None}, rfid_uid: {rfid_uid}")
                callback(student, rfid_uid)
            except Exception as e:
                logger.error(f"Error in RFID callback {getattr(callback, '__name__', str(callback))}: {str(e)}")
                import traceback
                logger.error(f"Callback error traceback: {traceback.format_exc()}")

    def _notify_callbacks(self, rfid_uid):
        """
        Emit signal to notify callbacks in a thread-safe way.

        Args:
            rfid_uid (str): The RFID UID that was read
        """
        # Use signal to ensure thread safety
        self.card_read_signal.emit(rfid_uid)

    def _read_rfid_linux(self):
        """
        Read RFID data from Linux device using evdev.
        """
        logger.info(f"Starting RFID reader for device: {self.device_path}")

        try:
            import evdev
            device = evdev.InputDevice(self.device_path)
            logger.info(f"Connected to RFID device: {device.name}")

            # Try to grab the device for exclusive access
            try:
                device.grab()
                logger.info("Gained exclusive access to RFID reader")
            except OSError as e:
                logger.warning(f"Could not gain exclusive access to RFID reader: {e}")

            # Clear any buffered data
            buffered_input = ""

            while self.running:
                try:
                    # Use select to check for input with timeout
                    import select
                    if select.select([device.fd], [], [], 1.0)[0]:
                        for event in device.read():
                            if event.type == evdev.ecodes.EV_KEY:
                                key_event = evdev.categorize(event)
                                if key_event.keystate == evdev.events.KeyEvent.key_down:
                                    key_name = key_event.keycode

                                    # Handle key mappings
                                    if key_name.startswith('KEY_'):
                                        key_name = key_name[4:]  # Remove 'KEY_' prefix

                                    # Check for numeric keys
                                    if key_name.isdigit():
                                        buffered_input += key_name
                                    elif key_name in ['A', 'B', 'C', 'D', 'E', 'F']:
                                        buffered_input += key_name
                                    elif key_name == 'ENTER':
                                        # Complete RFID read
                                        if buffered_input:
                                            rfid_uid = buffered_input.strip().upper()
                                            logger.info(f"RFID card read: {rfid_uid}")
                                            
                                            # Emit the signal to notify callbacks
                                            self.card_read_signal.emit(rfid_uid)
                                            
                                            buffered_input = ""  # Reset buffer
                                    elif key_name in ['BACKSPACE', 'DELETE']:
                                        # Handle corrections
                                        if buffered_input:
                                            buffered_input = buffered_input[:-1]
                                    else:
                                        # Reset buffer on unexpected input
                                        buffered_input = ""

                except OSError as e:
                    if self.running:  # Only log if we're supposed to be running
                        logger.error(f"Device read error: {e}")
                        self._handle_device_failure("Device read error", e)
                        break
                except Exception as e:
                    if self.running:
                        logger.error(f"Unexpected error reading RFID: {e}")
                        break

            # Cleanup
            try:
                device.ungrab()
                logger.info("Released RFID device")
            except:
                pass

        except ImportError:
            logger.error("evdev library not installed. Please install it with: pip install evdev")
            raise RuntimeError("evdev library is required for RFID functionality")
        except Exception as e:
            logger.error(f"Error reading RFID: {str(e)}")
            raise RuntimeError(f"RFID service error: {str(e)}")

    def _handle_device_failure(self, error_message, exception):
        """
        Handle RFID device failures with proper user notification.

        Args:
            error_message (str): Human-readable error message
            exception (Exception): The exception that caused the failure (can be None)
        """
        logger.error(f"RFID Device Failure: {error_message}")
        if exception:
            logger.error(f"Exception details: {str(exception)}")

        # Emit signal to notify UI components about the device failure
        self.device_status_changed.emit("disconnected", error_message)

        # Stop the service
        self.running = False

        # Schedule retry attempts
        self._schedule_device_reconnection()

    def _attempt_device_reconnection(self, device):
        """
        Attempt to reconnect to the RFID device with retry logic.

        Args:
            device: Current device object (may be invalid)

        Returns:
            bool: True if reconnection successful, False otherwise
        """
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting RFID device reconnection (attempt {attempt + 1}/{max_retries})")

                # First try to ungrab if we had grabbed it
                try:
                    device.ungrab()
                except:
                    pass

                # Wait before retry
                time.sleep(retry_delay)

                # Try to reopen the device
                import evdev
                device = evdev.InputDevice(self.device_path)
                logger.info(f"Reconnected to RFID device: {device.name}")

                # Try to grab it again
                try:
                    device.grab()
                    logger.info("Regained exclusive access to RFID reader")
                except:
                    logger.warning("Could not regain exclusive access, but device is connected")

                # Test the device with a simple operation
                device.capabilities()  # This will raise an exception if device is not working

                logger.info("✅ RFID device reconnection successful")
                self.device_status_changed.emit("connected", "RFID device reconnected successfully")
                return True

            except Exception as e:
                logger.warning(f"Reconnection attempt {attempt + 1} failed: {str(e)}")
                retry_delay *= 2  # Exponential backoff

        logger.error("❌ All RFID device reconnection attempts failed")
        return False

    def _schedule_device_reconnection(self):
        """
        Schedule periodic attempts to reconnect to the RFID device.
        """
        logger.info("📅 Device reconnection can be attempted manually through the admin interface")
        logger.info("💡 Check device connection and use 'Refresh RFID Service' if available")

    def retry_device_connection(self):
        """
        Public method to manually retry RFID device connection.
        Can be called from UI components.

        Returns:
            bool: True if reconnection successful, False otherwise
        """
        try:
            logger.info("Attempting to reconnect to RFID device...")

            # Try to detect and connect to device
            if self._detect_rfid_device():
                logger.info("✅ Successfully reconnected to RFID device")
                self.device_status_changed.emit("connected", "RFID device reconnected")

                # Restart the reading thread
                if hasattr(self, 'read_thread') and self.read_thread.is_alive():
                    self.stop()
                    time.sleep(1)

                self.start()
                return True
            else:
                logger.warning("❌ Could not detect RFID device")
                self.device_status_changed.emit("disconnected", "RFID device not detected")
                return False
                
        except Exception as e:
            logger.error(f"Error during RFID device reconnection: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.device_status_changed.emit("disconnected", f"Reconnection failed: {str(e)}")
            return False

    def refresh_student_data(self):
        """
        Refresh student data from the database.
        This ensures newly added students are immediately available for RFID scanning.
        
        Returns:
            list: List of all students in the database
        """
        try:
            from ..models.base import get_db
            from ..models.student import Student
            
            db = get_db()
            students = db.query(Student).all()
            
            # Access student data while session is active to avoid DetachedInstanceError
            student_data = []
            for student in students:
                student_info = {
                    'id': student.id,
                    'name': student.name,
                    'rfid_uid': student.rfid_uid,
                    'department': student.department
                }
                student_data.append(student_info)
            
            db.close()
            
            logger.info(f"Refreshed student data from database: {len(student_data)} students available for RFID scanning")
            
            # Log some details for debugging
            for student in student_data[:5]:  # Log first 5 students
                logger.debug(f"Student available: {student['name']} (RFID: {student['rfid_uid']})")
            
            if len(student_data) > 5:
                logger.debug(f"... and {len(student_data) - 5} more students")
            
            return student_data
            
        except Exception as e:
            logger.error(f"Error refreshing student data: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []

    def simulate_card_read(self, rfid_uid):
        """
        Simulate an RFID card read for testing purposes.
        This method emits the card_read_signal as if a real card was scanned.
        
        Args:
            rfid_uid (str): The RFID UID to simulate
        """
        try:
            if not rfid_uid:
                logger.warning("Cannot simulate RFID read with empty UID")
                return
                
            logger.info(f"Simulating RFID card read: {rfid_uid}")
            
            # Emit the card read signal to trigger normal RFID processing
            self.card_read_signal.emit(rfid_uid)
            
            logger.info(f"Successfully simulated RFID card read: {rfid_uid}")
            
        except Exception as e:
            logger.error(f"Error simulating RFID card read: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def get_device_status(self):
        """
        Get current RFID device status.

        Returns:
            dict: Device status information
        """
        return {
            'device_path': self.device_path,
            'running': self.running,
            'status': 'connected' if self.running else 'disconnected'
        }

# Singleton instance
rfid_service = None

def get_rfid_service():
    """
    Get the singleton RFID service instance.
    """
    global rfid_service
    if rfid_service is None:
        rfid_service = RFIDService()
    return rfid_service