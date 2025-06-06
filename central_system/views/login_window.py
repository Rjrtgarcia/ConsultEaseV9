from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QIcon
import os

from .base_window import BaseWindow
from central_system.utils.theme import ConsultEaseTheme

class LoginWindow(BaseWindow):
    """
    Login window for student RFID authentication.
    """
    # Signal to notify when a student is authenticated
    student_authenticated = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up logging
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing LoginWindow")

        self.init_ui()

        # Initialize state variables
        self.rfid_reading = False
        self.scanning_timer = QTimer(self)
        self.scanning_timer.timeout.connect(self.update_scanning_animation)
        self.scanning_animation_frame = 0

        # The left panel is no longer needed since we moved the simulate button
        # to the scanning frame

    def init_ui(self):
        """
        Initialize the login UI components.
        """
        # Set up main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create content widget with proper margin
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(50, 30, 50, 30)
        content_layout.setSpacing(20)

        # Dark header background
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {ConsultEaseTheme.PRIMARY_COLOR}; color: {ConsultEaseTheme.TEXT_LIGHT};")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("ConsultEase")
        title_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_XXLARGE}pt; font-weight: bold; color: {ConsultEaseTheme.TEXT_LIGHT};")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)

        # Instruction label
        instruction_label = QLabel("Please scan your RFID card to authenticate")
        instruction_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_LARGE}pt; color: {ConsultEaseTheme.TEXT_LIGHT};")
        instruction_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(instruction_label)

        # Add header to main layout
        main_layout.addWidget(header_frame, 0)

        # Content area - white background
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #f5f5f5;")
        content_frame_layout = QVBoxLayout(content_frame)
        content_frame_layout.setContentsMargins(50, 50, 50, 50)

        # RFID scanning indicator
        self.scanning_frame = QFrame()
        self.scanning_frame.setStyleSheet(f'''
            QFrame {{
                background-color: {ConsultEaseTheme.BG_SECONDARY};
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_LARGE}px;
                border: 2px solid #ccc;
            }}
        ''')
        scanning_layout = QVBoxLayout(self.scanning_frame)
        scanning_layout.setContentsMargins(30, 30, 30, 30)
        scanning_layout.setSpacing(20)

        self.scanning_status_label = QLabel("Ready to Scan")
        self.scanning_status_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_XLARGE}pt; color: {ConsultEaseTheme.SECONDARY_COLOR};")
        self.scanning_status_label.setAlignment(Qt.AlignCenter)
        scanning_layout.addWidget(self.scanning_status_label)

        self.rfid_icon_label = QLabel()
        # Ideally, we would have an RFID icon image here
        self.rfid_icon_label.setText("🔄")
        self.rfid_icon_label.setStyleSheet(f"font-size: 48pt; color: {ConsultEaseTheme.SECONDARY_COLOR};")
        self.rfid_icon_label.setAlignment(Qt.AlignCenter)
        scanning_layout.addWidget(self.rfid_icon_label)

        # Add manual RFID input field
        manual_input_layout = QHBoxLayout()

        self.rfid_input = QLineEdit()
        self.rfid_input.setPlaceholderText("Enter RFID manually")
        self.rfid_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid #ccc;
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_NORMAL}px;
                padding: {ConsultEaseTheme.PADDING_NORMAL}px;
                font-size: {ConsultEaseTheme.FONT_SIZE_NORMAL}pt;
                background-color: {ConsultEaseTheme.BG_PRIMARY};
                min-height: {ConsultEaseTheme.TOUCH_MIN_HEIGHT}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ConsultEaseTheme.PRIMARY_COLOR};
            }}
        """)
        self.rfid_input.returnPressed.connect(self.handle_manual_rfid_entry)
        manual_input_layout.addWidget(self.rfid_input, 3)

        submit_button = QPushButton("Submit")
        submit_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ConsultEaseTheme.PRIMARY_COLOR};
                color: {ConsultEaseTheme.TEXT_LIGHT};
                border: none;
                padding: {ConsultEaseTheme.PADDING_NORMAL}px {ConsultEaseTheme.PADDING_LARGE}px;
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_NORMAL}px;
                font-weight: bold;
                min-height: {ConsultEaseTheme.TOUCH_MIN_HEIGHT}px;
            }}
            QPushButton:hover {{
                background-color: #1a4b7c;
            }}
        """)
        submit_button.clicked.connect(self.handle_manual_rfid_entry)
        manual_input_layout.addWidget(submit_button, 1)

        scanning_layout.addLayout(manual_input_layout)

        content_frame_layout.addWidget(self.scanning_frame, 1)

        # Add content to main layout
        main_layout.addWidget(content_frame, 1)

        # Footer with admin login button
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"background-color: {ConsultEaseTheme.PRIMARY_COLOR};")
        footer_frame.setFixedHeight(70)
        footer_layout = QHBoxLayout(footer_frame)

        # Admin login button
        admin_button = QPushButton("Admin Login")
        admin_button.setStyleSheet(f'''
            QPushButton {{
                background-color: {ConsultEaseTheme.BG_DARK};
                color: {ConsultEaseTheme.TEXT_LIGHT};
                border: none;
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_NORMAL}px;
                padding: {ConsultEaseTheme.PADDING_NORMAL}px {ConsultEaseTheme.PADDING_LARGE}px;
                max-width: 200px;
                min-height: {ConsultEaseTheme.TOUCH_MIN_HEIGHT}px;
            }}
            QPushButton:hover {{
                background-color: #3a4b5c;
            }}
        ''')
        admin_button.clicked.connect(self.admin_login)

        footer_layout.addStretch()
        footer_layout.addWidget(admin_button)
        footer_layout.addStretch()

        main_layout.addWidget(footer_frame, 0)

        # Set the main layout to a widget and make it the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def showEvent(self, event):
        """Override showEvent"""
        super().showEvent(event)

        # Refresh RFID service to ensure it has the latest student data
        try:
            from ..services import get_rfid_service
            rfid_service = get_rfid_service()
            rfid_service.refresh_student_data()
            self.logger.info("Refreshed RFID service student data when login window shown")
        except Exception as e:
            self.logger.error(f"Error refreshing RFID service: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Start RFID scanning when the window is shown
        self.logger.info("LoginWindow shown, starting RFID scanning")
        self.start_rfid_scanning()

        # Focus the RFID input field for manual entry
        self.rfid_input.setFocus()

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)

    def start_rfid_scanning(self):
        """
        Start the RFID scanning animation and process.
        """
        # Refresh RFID service to ensure it has the latest student data
        try:
            from ..services import get_rfid_service
            rfid_service = get_rfid_service()
            rfid_service.refresh_student_data()
            self.logger.info("Refreshed RFID service student data when starting RFID scanning")
        except Exception as e:
            self.logger.error(f"Error refreshing RFID service: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

        self.rfid_reading = True
        self.scanning_status_label.setText("Scanning...")
        self.scanning_status_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_XLARGE}pt; color: {ConsultEaseTheme.SECONDARY_COLOR};")
        self.scanning_frame.setStyleSheet(f'''
            QFrame {{
                background-color: {ConsultEaseTheme.BG_SECONDARY};
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_LARGE}px;
                border: 2px solid {ConsultEaseTheme.SECONDARY_COLOR};
            }}
        ''')
        self.scanning_timer.start(500)  # Update animation every 500ms

    def stop_rfid_scanning(self):
        """
        Stop the RFID scanning animation.
        """
        self.rfid_reading = False
        self.scanning_timer.stop()
        self.scanning_status_label.setText("Ready to Scan")
        self.scanning_status_label.setStyleSheet(f"font-size: {ConsultEaseTheme.FONT_SIZE_XLARGE}pt; color: {ConsultEaseTheme.SECONDARY_COLOR};")
        self.scanning_frame.setStyleSheet(f'''
            QFrame {{
                background-color: {ConsultEaseTheme.BG_SECONDARY};
                border-radius: {ConsultEaseTheme.BORDER_RADIUS_LARGE}px;
                border: 2px solid #ccc;
            }}
        ''')
        self.rfid_icon_label.setText("🔄")

    def update_scanning_animation(self):
        """
        Update the scanning animation frames.
        """
        animations = ["🔄", "🔁", "🔃", "🔂"]
        self.scanning_animation_frame = (self.scanning_animation_frame + 1) % len(animations)
        self.rfid_icon_label.setText(animations[self.scanning_animation_frame])

    def handle_rfid_read(self, rfid_uid, student=None):
        """
        Handle RFID read event.

        Args:
            rfid_uid (str): The RFID UID that was read
            student (object, optional): Student object if already validated
        """
        self.logger.info(f"LoginWindow.handle_rfid_read called with rfid_uid: {rfid_uid}, student: {student}")

        # Stop scanning animation
        self.stop_rfid_scanning()

        # If student is not provided, try to look it up directly
        if not student and rfid_uid:
            try:
                # First refresh the RFID service to ensure it has the latest student data
                try:
                    from ..services import get_rfid_service
                    rfid_service = get_rfid_service()
                    rfid_service.refresh_student_data()
                    self.logger.info("Refreshed RFID service student data before looking up student")
                except Exception as e:
                    self.logger.error(f"Error refreshing RFID service: {str(e)}")

                from ..models import Student, get_db
                db = get_db()

                # Try exact match first
                self.logger.info(f"Looking up student with RFID UID: {rfid_uid}")
                student = db.query(Student).filter(Student.rfid_uid == rfid_uid).first()

                # If no exact match, try case-insensitive match
                if not student:
                    self.logger.info(f"No exact match found, trying case-insensitive match for RFID: {rfid_uid}")
                    # For PostgreSQL
                    try:
                        student = db.query(Student).filter(Student.rfid_uid.ilike(rfid_uid)).first()
                    except:
                        # For SQLite
                        student = db.query(Student).filter(Student.rfid_uid.lower() == rfid_uid.lower()).first()

                if student:
                    self.logger.info(f"LoginWindow: Found student directly: {student.name} with RFID: {rfid_uid}")
                else:
                    # Log all students in the database for debugging
                    all_students = db.query(Student).all()
                    self.logger.warning(f"No student found for RFID {rfid_uid}")
                    self.logger.info(f"Available students in database: {len(all_students)}")
                    for s in all_students:
                        self.logger.info(f"  - ID: {s.id}, Name: {s.name}, RFID: {s.rfid_uid}")
            except Exception as e:
                self.logger.error(f"LoginWindow: Error looking up student: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")

        if student:
            # Authentication successful
            self.logger.info(f"Authentication successful for student: {student.name} with ID: {student.id}")

            # Convert student object to safe dictionary format to avoid DetachedInstanceError
            try:
                student_data = {
                    'id': student.id,
                    'name': student.name,
                    'department': student.department,
                    'rfid_uid': student.rfid_uid,
                    'created_at': student.created_at.isoformat() if student.created_at else None,
                    'updated_at': student.updated_at.isoformat() if student.updated_at else None
                }
                self.logger.info(f"Converted student to safe data format: {student_data}")
            except Exception as e:
                self.logger.error(f"Error converting student to safe format: {e}")
                # Fallback to basic data
                student_data = {
                    'id': getattr(student, 'id', None),
                    'name': getattr(student, 'name', 'Unknown'),
                    'department': getattr(student, 'department', 'Unknown'),
                    'rfid_uid': getattr(student, 'rfid_uid', ''),
                    'created_at': None,
                    'updated_at': None
                }

            self.show_success(f"Welcome, {student_data['name']}!")

            # Log the emission of the signal
            self.logger.info(f"LoginWindow: Emitting student_authenticated signal for {student_data['name']}")

            # Emit the signal to navigate to the dashboard with safe student data
            self.student_authenticated.emit(student_data)

            # Also emit a change_window signal as a backup
            self.logger.info(f"LoginWindow: Emitting change_window signal for dashboard")
            self.change_window.emit("dashboard", student_data)

            # Force a delay to ensure the signals are processed
            QTimer.singleShot(500, lambda: self._force_dashboard_navigation(student_data))
        else:
            # Authentication failed
            self.logger.warning(f"Authentication failed for RFID: {rfid_uid}")
            self.show_error("RFID card not recognized. Please try again or contact an administrator.")

    def _force_dashboard_navigation(self, student_data):
        """
        Force navigation to dashboard as a fallback.

        Args:
            student_data (dict): Student data dictionary
        """
        self.logger.info("Forcing dashboard navigation as fallback")
        self.change_window.emit("dashboard", student_data)

    def show_success(self, message):
        """
        Show success message and visual feedback.
        """
        self.scanning_status_label.setText("Authenticated")
        self.scanning_status_label.setStyleSheet("font-size: 20pt; color: #4caf50;")
        self.scanning_frame.setStyleSheet('''
            QFrame {
                background-color: #e8f5e9;
                border-radius: 10px;
                border: 2px solid #4caf50;
            }
        ''')
        self.rfid_icon_label.setText("✅")

        # Show message in a popup
        QMessageBox.information(self, "Authentication Success", message)

    def show_error(self, message):
        """
        Show error message and visual feedback.
        """
        self.scanning_status_label.setText("Error")
        self.scanning_status_label.setStyleSheet("font-size: 20pt; color: #f44336;")
        self.scanning_frame.setStyleSheet('''
            QFrame {
                background-color: #ffebee;
                border-radius: 10px;
                border: 2px solid #f44336;
            }
        ''')
        self.rfid_icon_label.setText("❌")

        # Show error in a popup
        QMessageBox.warning(self, "Authentication Error", message)

        # Reset after a delay
        QTimer.singleShot(3000, self.stop_rfid_scanning)

    def admin_login(self):
        """
        Show admin login dialog.
        """
        self.change_window.emit("admin_login", None)

    def handle_manual_rfid_entry(self):
        """
        Handle manual RFID entry from the input field.
        """
        rfid_uid = self.rfid_input.text().strip()
        if rfid_uid:
            self.logger.info(f"Manual RFID entry: {rfid_uid}")
            self.rfid_input.clear()
            self.start_rfid_scanning()

            # Process the manually entered RFID UID directly
            try:
                self.logger.info(f"Processing manually entered RFID UID: {rfid_uid}")
                # Directly handle the RFID read without simulation
                QTimer.singleShot(500, lambda: self.handle_rfid_read(rfid_uid, None))
            except Exception as e:
                self.logger.error(f"Error processing manual RFID entry: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")

                # If there's an error, directly handle the RFID read
                self.logger.info(f"Directly handling RFID read due to error: {rfid_uid}")
                QTimer.singleShot(1000, lambda: self.handle_rfid_read(rfid_uid, None))

# Create a script to ensure the keyboard works on Raspberry Pi
def create_keyboard_setup_script():
    """
    Create a script to set up the virtual keyboard on the Raspberry Pi.
    This should be called when deploying the application.
    """
    # This function has been removed as keyboard integration is no longer needed
    pass