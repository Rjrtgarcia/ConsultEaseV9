from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGridLayout, QScrollArea, QFrame,
                               QLineEdit, QComboBox, QMessageBox, QTextEdit,
                               QSplitter, QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap

import os
import logging
import time
from .base_window import BaseWindow
from .consultation_panel import ConsultationPanel
from ..utils.ui_components import FacultyCard
from ..ui.pooled_faculty_card import get_faculty_card_manager
from ..utils.ui_performance import (
from ..services.mqtt_service import AsyncMQTTService # Added for MQTT service
    get_ui_batcher, get_widget_state_manager, SmartRefreshManager,
    batch_ui_update, timed_ui_update
)

# Set up logging
logger = logging.getLogger(__name__)



class ConsultationRequestForm(QFrame):
    """
    Form to request a consultation with a faculty member.
    """
    request_submitted = pyqtSignal(object, str, str)

    def __init__(self, faculty=None, parent=None):
        super().__init__(parent)
        self.faculty = faculty
        self.init_ui()

    def init_ui(self):
        """
        Initialize the consultation request form UI.
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('''
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 10px;
            }
        ''')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Form title
        title_label = QLabel("Request Consultation")
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Faculty information
        if self.faculty:
            # Create a layout for faculty info with image
            faculty_info_layout = QHBoxLayout()

            # Faculty image
            image_label = QLabel()
            image_label.setFixedSize(60, 60)
            image_label.setStyleSheet("border: 1px solid #ddd; border-radius: 30px; background-color: white;")
            image_label.setScaledContents(True)

            # Try to load faculty image
            if hasattr(self.faculty, 'get_image_path') and self.faculty.image_path:
                try:
                    image_path = self.faculty.get_image_path()
                    if image_path and os.path.exists(image_path):
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            image_label.setPixmap(pixmap)
                except Exception as e:
                    logger.error(f"Error loading faculty image in consultation form: {str(e)}")

            faculty_info_layout.addWidget(image_label)

            # Faculty text info
            faculty_info = QLabel(f"Faculty: {self.faculty.name} ({self.faculty.department})")
            faculty_info.setStyleSheet("font-size: 14pt;")
            faculty_info_layout.addWidget(faculty_info)
            faculty_info_layout.addStretch()

            main_layout.addLayout(faculty_info_layout)
        else:
            # If no faculty is selected, show a dropdown
            faculty_label = QLabel("Select Faculty:")
            faculty_label.setStyleSheet("font-size: 14pt;")
            main_layout.addWidget(faculty_label)

            self.faculty_combo = QComboBox()
            self.faculty_combo.setStyleSheet("font-size: 14pt; padding: 8px;")
            # Faculty options would be populated separately
            main_layout.addWidget(self.faculty_combo)

        # Course code input
        course_label = QLabel("Course Code (optional):")
        course_label.setStyleSheet("font-size: 14pt;")
        main_layout.addWidget(course_label)

        self.course_input = QLineEdit()
        self.course_input.setStyleSheet("font-size: 14pt; padding: 8px;")
        main_layout.addWidget(self.course_input)

        # Message input
        message_label = QLabel("Consultation Details:")
        message_label.setStyleSheet("font-size: 14pt;")
        main_layout.addWidget(message_label)

        self.message_input = QTextEdit()
        self.message_input.setStyleSheet("font-size: 14pt; padding: 8px;")
        self.message_input.setMinimumHeight(150)
        main_layout.addWidget(self.message_input)

        # Submit button
        button_layout = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet('''
            QPushButton {
                background-color: #f44336;
                min-width: 120px;
            }
        ''')
        cancel_button.clicked.connect(self.cancel_request)

        submit_button = QPushButton("Submit Request")
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #4caf50;
                min-width: 120px;
            }
        ''')
        submit_button.clicked.connect(self.submit_request)

        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(submit_button)

        main_layout.addLayout(button_layout)

    def set_faculty(self, faculty):
        """
        Set the faculty for the consultation request.
        """
        self.faculty = faculty
        self.init_ui()

    def set_faculty_options(self, faculties):
        """
        Set the faculty options for the dropdown.
        Only show available faculty members.
        """
        if hasattr(self, 'faculty_combo'):
            self.faculty_combo.clear()
            available_count = 0

            for faculty in faculties:
                # Only add available faculty to the dropdown
                if hasattr(faculty, 'status') and faculty.status:
                    self.faculty_combo.addItem(f"{faculty.name} ({faculty.department})", faculty)
                    available_count += 1

            # Show a message if no faculty is available
            if available_count == 0:
                self.faculty_combo.addItem("No faculty members are currently available", None)

    def get_selected_faculty(self):
        """
        Get the selected faculty from the dropdown.
        """
        if hasattr(self, 'faculty_combo') and self.faculty_combo.count() > 0:
            return self.faculty_combo.currentData()
        return self.faculty

    def submit_request(self):
        """
        Handle the submission of the consultation request.
        """
        faculty = self.get_selected_faculty()
        if not faculty:
            QMessageBox.warning(self, "Consultation Request", "Please select a faculty member.")
            return

        # Check if faculty is available
        if hasattr(faculty, 'status') and not faculty.status:
            QMessageBox.warning(self, "Consultation Request",
                               f"Faculty {faculty.name} is currently unavailable. Please select an available faculty member.")
            return

        message = self.message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Consultation Request", "Please enter consultation details.")
            return

        course_code = self.course_input.text().strip()

        # Emit signal with the request details
        self.request_submitted.emit(faculty, message, course_code)

    def cancel_request(self):
        """
        Cancel the consultation request.
        """
        self.message_input.clear()
        self.course_input.clear()
        self.setVisible(False)

class DashboardWindow(BaseWindow):
    """
    Main dashboard window with faculty availability display and consultation request functionality.
    """
    # Signal to handle consultation request
    consultation_requested = pyqtSignal(object, str, str)
    request_ui_refresh = pyqtSignal()

    def __init__(self, student=None, parent=None):
        self.student = student
        self.faculty_list = []
        self.consultation_panel = None
        self.mqtt_service = AsyncMQTTService()
        try:
            self.mqtt_service.connect()
            logger.info("MQTT Service connected in DashboardWindow.")
        except Exception as e:
            logger.error(f"Failed to connect MQTT service in DashboardWindow: {e}")
        
        # Set up real-time consultation status updates
        self.setup_real_time_updates()
        
        super().__init__(parent)
        self.init_ui()

        # Set up smart refresh manager for optimized faculty status updates
        self.smart_refresh = SmartRefreshManager(base_interval=180000, max_interval=600000)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_faculty_status)
        self.refresh_timer.start(180000)  # Start with 3 minutes

        # Set up real-time MQTT subscription for faculty status updates
        self.setup_realtime_updates()

        # UI performance utilities
        self.ui_batcher = get_ui_batcher()
        self.widget_state_manager = get_widget_state_manager()

        # Connect the UI refresh signal
        self.request_ui_refresh.connect(self.refresh_faculty_status)

        # Faculty card manager for pooling
        self.faculty_card_manager = get_faculty_card_manager()

        # Track faculty data for efficient comparison
        self._last_faculty_hash = None

        # Loading state management
        self._is_loading = False
        self._loading_widget = None

        # Log student info for debugging
        if student:
            # Handle both student object and student data dictionary
            if isinstance(student, dict):
                student_id = student.get('id', 'Unknown')
                student_name = student.get('name', 'Unknown')
                student_rfid = student.get('rfid_uid', 'Unknown')
            else:
                # Legacy support for student objects
                student_id = getattr(student, 'id', 'Unknown')
                student_name = getattr(student, 'name', 'Unknown')
                student_rfid = getattr(student, 'rfid_uid', 'Unknown')
            logger.info(f"Dashboard initialized with student: ID={student_id}, Name={student_name}, RFID={student_rfid}")
        else:
            logger.warning("Dashboard initialized without student information")

    def init_ui(self):
        """
        Initialize the dashboard UI.
        """
        # Main layout with splitter
        main_layout = QVBoxLayout()

        # Header with welcome message and student info - improved styling
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        header_layout.setContentsMargins(20, 15, 20, 15)

        if self.student:
            # Handle both student object and student data dictionary
            if isinstance(self.student, dict):
                student_name = self.student.get('name', 'Student')
            else:
                # Legacy support for student objects
                student_name = getattr(self.student, 'name', 'Student')
            welcome_label = QLabel(f"Welcome, {student_name}")
        else:
            welcome_label = QLabel("Welcome to ConsultEase")

        # Enhanced header styling for consistency with admin dashboard
        welcome_label.setStyleSheet("""
            QLabel {
                font-size: 28pt;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px 20px;
                background-color: #ecf0f1;
                border-radius: 10px;
                margin: 10px 0;
                min-height: 60px;
            }
        """)
        header_layout.addWidget(welcome_label)

        # Logout button - larger size for better usability
        logout_button = QPushButton("Logout")
        logout_button.setFixedSize(90, 35)  # Increased size for better touch interaction
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 6px;
                font-size: 12pt;  /* Increased font size */
                font-weight: bold;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background-color: #a82315;
                transform: scale(0.98);
            }
        """)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)

        main_layout.addLayout(header_layout)

        # Main content with faculty grid and consultation form
        content_splitter = QSplitter(Qt.Horizontal)

        # Get screen size to set proportional initial sizes
        screen_size = QApplication.desktop().screenGeometry()
        screen_width = screen_size.width()

        # Faculty availability grid
        faculty_widget = QWidget()
        faculty_layout = QVBoxLayout(faculty_widget)

        # Search and filter controls in a more touch-friendly layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Search input with icon and better styling
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 2px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(5, 0, 5, 0)
        search_layout.setSpacing(5)

        search_icon = QLabel()
        try:
            search_icon_pixmap = QPixmap("resources/icons/search.png")
            if not search_icon_pixmap.isNull():
                search_icon.setPixmap(search_icon_pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except:
            # If icon not available, use text
            search_icon.setText("🔍")

        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or department")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 12px 8px;
                font-size: 14pt;
                min-height: 44px;
                background-color: transparent;
            }
            QLineEdit:focus {
                background-color: #f8f9fa;
            }
        """)
        self.search_input.textChanged.connect(self.filter_faculty)
        search_layout.addWidget(self.search_input)

        filter_layout.addWidget(search_frame, 3)  # Give search more space

        # Filter dropdown with better styling
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 2px;
            }
        """)
        filter_inner_layout = QHBoxLayout(filter_frame)
        filter_inner_layout.setContentsMargins(5, 0, 5, 0)
        filter_inner_layout.setSpacing(5)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("font-size: 12pt;")
        filter_inner_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All", None)
        self.filter_combo.addItem("Available Only", True)
        self.filter_combo.addItem("Unavailable Only", False)
        self.filter_combo.setStyleSheet("""
            QComboBox {
                border: none;
                padding: 12px 8px;
                font-size: 14pt;
                min-height: 44px;
                background-color: transparent;
            }
            QComboBox:focus {
                background-color: #f8f9fa;
            }
            QComboBox::drop-down {
                width: 30px;
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        self.filter_combo.currentIndexChanged.connect(self.filter_faculty)
        filter_inner_layout.addWidget(self.filter_combo)

        filter_layout.addWidget(filter_frame, 2)  # Give filter less space

        faculty_layout.addLayout(filter_layout)

        # Faculty grid in a scroll area with improved spacing and alignment
        self.faculty_grid = QGridLayout()
        self.faculty_grid.setSpacing(15)  # Reduced spacing between cards for better use of space
        self.faculty_grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Align to top and center horizontally
        self.faculty_grid.setContentsMargins(10, 10, 10, 10)  # Reduced margins around the grid

        # Create a scroll area for the faculty grid
        faculty_scroll = QScrollArea()
        faculty_scroll.setWidgetResizable(True)
        faculty_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        faculty_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        faculty_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #f0f0f0;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Create a container widget for the faculty grid
        faculty_scroll_content = QWidget()
        faculty_scroll_content.setLayout(self.faculty_grid)
        faculty_scroll_content.setStyleSheet("background-color: transparent;")

        # Set the scroll area widget
        faculty_scroll.setWidget(faculty_scroll_content)

        # Ensure scroll area starts at the top
        faculty_scroll.verticalScrollBar().setValue(0)

        # Store the scroll area for later reference
        self.faculty_scroll = faculty_scroll

        faculty_layout.addWidget(faculty_scroll)

        # Consultation panel with request form and history
        self.consultation_panel = ConsultationPanel(student=self.student, mqtt_service=self.mqtt_service, parent=self)
        self.consultation_panel.consultation_requested.connect(self.handle_consultation_request)
        self.consultation_panel.consultation_cancelled.connect(self.handle_consultation_cancel)

        # Add widgets to splitter
        content_splitter.addWidget(faculty_widget)
        content_splitter.addWidget(self.consultation_panel)

        # Set splitter sizes proportionally to screen width
        content_splitter.setSizes([int(screen_width * 0.6), int(screen_width * 0.4)])

        # Save splitter state when it changes
        content_splitter.splitterMoved.connect(self.save_splitter_state)

        # Store the splitter for later reference
        self.content_splitter = content_splitter

        # Try to restore previous splitter state
        self.restore_splitter_state()

        # Add the splitter to the main layout
        main_layout.addWidget(content_splitter)

        # Schedule a scroll to top after the UI is fully loaded
        QTimer.singleShot(100, self._scroll_faculty_to_top)

        # Set the main layout to a widget and make it the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def populate_faculty_grid_safe(self, faculty_data_list):
        """
        Populate the faculty grid with faculty cards using safe data dictionaries.
        Optimized for performance with batch processing.

        Args:
            faculty_data_list (list): List of faculty data dictionaries
        """
        # Store faculty data list for later reference
        self._last_faculty_data_list = faculty_data_list
        
        # Log faculty data for debugging
        logger.info(f"Populating faculty grid (safe) with {len(faculty_data_list) if faculty_data_list else 0} faculty members")

        # Temporarily disable updates to reduce flickering and improve performance
        self.setUpdatesEnabled(False)

        try:
            # Clear existing grid efficiently using pooled cards
            self._clear_faculty_grid_pooled()

            # Handle empty faculty list
            if not faculty_data_list:
                logger.info("No faculty members found - showing empty state message")
                self._show_empty_faculty_message()
                return

            # Calculate optimal number of columns based on screen width
            screen_width = QApplication.desktop().screenGeometry().width()

            # Fixed card width (matches the width set in FacultyCard)
            card_width = 280

            # Grid spacing
            spacing = 15

            # Get the actual width of the faculty grid container
            grid_container_width = self.faculty_grid.parentWidget().width()
            if grid_container_width <= 0:
                grid_container_width = int(screen_width * 0.6)

            # Account for grid margins
            grid_container_width -= 30

            # Calculate how many cards can fit in a row
            max_cols = max(1, int(grid_container_width / (card_width + spacing)))

            # Adjust for very small screens
            if screen_width < 800:
                max_cols = 1

            # Add faculty cards to grid
            row, col = 0, 0
            containers = []

            logger.info(f"Creating faculty cards for {len(faculty_data_list)} faculty members")

            for faculty_data in faculty_data_list:
                try:
                    # Validate faculty_data
                    if not isinstance(faculty_data, dict):
                        logger.error(f"Invalid faculty_data type: {type(faculty_data)}")
                        continue
                        
                    if 'id' not in faculty_data or 'name' not in faculty_data:
                        logger.error(f"Missing required fields in faculty_data: {faculty_data}")
                        continue

                    # Create a container widget to center the card
                    container = QWidget()
                    container.setStyleSheet("background-color: transparent;")
                    container_layout = QHBoxLayout(container)
                    container_layout.setContentsMargins(0, 0, 0, 0)
                    container_layout.setAlignment(Qt.AlignCenter)

                    logger.debug(f"Creating card for faculty {faculty_data['name']}: available={faculty_data.get('available', False)}")

                    # Get pooled faculty card
                    card = self.faculty_card_manager.get_faculty_card(
                        faculty_data,
                        consultation_callback=lambda f_data=faculty_data: self.show_consultation_form_safe(f_data)
                    )

                    # Connect consultation signal if it exists
                    if hasattr(card, 'consultation_requested'):
                        # Use faculty_data dictionary instead of faculty object to avoid type mismatch
                        card.consultation_requested.connect(lambda f_data=faculty_data: self.show_consultation_form_safe(f_data))

                    # Add card to container
                    container_layout.addWidget(card)

                    # Store container for batch processing
                    containers.append((container, row, col))

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    logger.debug(f"Successfully created card for faculty {faculty_data['name']}")

                except Exception as e:
                    faculty_name = faculty_data.get('name', 'Unknown') if isinstance(faculty_data, dict) else 'Unknown'
                    logger.error(f"Error creating faculty card for {faculty_name}: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue

            # Add all containers to the grid at once
            for container, r, c in containers:
                self.faculty_grid.addWidget(container, r, c)

            # Log successful population
            logger.info(f"Successfully populated faculty grid with {len(containers)} faculty cards")

        finally:
            # Re-enable updates after all changes are made
            self.setUpdatesEnabled(True)

    def show_consultation_form_safe(self, faculty_data):
        """
        Show consultation form using safe faculty data dictionary.

        Args:
            faculty_data (dict or int): Faculty data dictionary or faculty ID
        """
        try:
            # Handle case where faculty_data might be an integer (faculty ID)
            if isinstance(faculty_data, int):
                logger.debug(f"Received faculty ID {faculty_data}, need to fetch faculty data")
                # Try to get faculty data from current faculty list
                faculty_id = faculty_data
                
                # Find faculty data in the currently loaded faculty list
                target_faculty_data = None
                if hasattr(self, '_last_faculty_data_list') and self._last_faculty_data_list:
                    for f_data in self._last_faculty_data_list:
                        if f_data.get('id') == faculty_id:
                            target_faculty_data = f_data
                            break
                
                if target_faculty_data:
                    faculty_data = target_faculty_data
                else:
                    logger.error(f"Could not find faculty data for ID {faculty_id}")
                    return
            
            # Ensure faculty_data is a dictionary
            if not isinstance(faculty_data, dict):
                logger.error(f"Invalid faculty_data type: {type(faculty_data)}. Expected dict or int.")
                return
                
            # Validate required fields
            required_fields = ['id', 'name']
            for field in required_fields:
                if field not in faculty_data:
                    logger.error(f"Missing required field '{field}' in faculty_data")
                    return

            # Create a mock faculty object for compatibility
            class MockFaculty:
                def __init__(self, data):
                    self.id = data['id']
                    self.name = data['name']
                    self.department = data.get('department', 'Unknown Department')
                    self.status = data.get('status', 'Unknown')
                    self.email = data.get('email', '')
                    self.room = data.get('room', None)

            mock_faculty = MockFaculty(faculty_data)
            self.show_consultation_form(mock_faculty)
            
        except Exception as e:
            faculty_name = "Unknown"
            if isinstance(faculty_data, dict):
                faculty_name = faculty_data.get('name', 'Unknown')
            elif isinstance(faculty_data, int):
                faculty_name = f"Faculty ID {faculty_data}"
            
            logger.error(f"Error showing consultation form for faculty {faculty_name}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _extract_safe_faculty_data(self, faculty_data_list):
        """
        Extract relevant data from safe faculty data for comparison.

        Args:
            faculty_data_list (list): List of faculty data dictionaries

        Returns:
            str: Hash of faculty data for efficient comparison
        """
        import hashlib
        # Create a string representation of all relevant faculty data
        data_str = ""
        for f_data in sorted(faculty_data_list, key=lambda x: x['id']):  # Sort for consistent hashing
            data_str += f"{f_data['id']}:{f_data['name']}:{f_data['status']}:{f_data.get('department', '')};"

        # Return hash for efficient comparison
        return hashlib.md5(data_str.encode()).hexdigest()

    def populate_faculty_grid(self, faculties):
        """
        Populate the faculty grid with faculty cards.
        Optimized for performance with batch processing and reduced UI updates.

        Args:
            faculties (list): List of faculty objects
        """
        # Log faculty data for debugging
        logger.info(f"Populating faculty grid with {len(faculties) if faculties else 0} faculty members")
        if faculties:
            for faculty in faculties:
                try:
                    # Access attributes safely to avoid DetachedInstanceError
                    faculty_name = faculty.name
                    faculty_status = faculty.status
                    faculty_always_available = getattr(faculty, 'always_available', False)
                    logger.debug(f"Faculty: {faculty_name}, Status: {faculty_status}, Always Available: {faculty_always_available}")
                except Exception as e:
                    logger.warning(f"Error accessing faculty attributes: {e}")
                    continue

        # Temporarily disable updates to reduce flickering and improve performance
        self.setUpdatesEnabled(False)

        try:
            # Clear existing grid efficiently using pooled cards
            self._clear_faculty_grid_pooled()

            # Handle empty faculty list
            if not faculties:
                logger.info("No faculty members found - showing empty state message")
                self._show_empty_faculty_message()
                return

            # Calculate optimal number of columns based on screen width
            screen_width = QApplication.desktop().screenGeometry().width()

            # Fixed card width (matches the width set in FacultyCard)
            card_width = 280  # Updated to match the improved FacultyCard width

            # Grid spacing (matches the spacing set in faculty_grid)
            spacing = 15

            # Get the actual width of the faculty grid container
            grid_container_width = self.faculty_grid.parentWidget().width()
            if grid_container_width <= 0:  # If not yet available, estimate based on screen
                grid_container_width = int(screen_width * 0.6)  # 60% of screen for faculty grid

            # Account for grid margins
            grid_container_width -= 30  # 15px left + 15px right margin

            # Calculate how many cards can fit in a row, accounting for spacing
            max_cols = max(1, int(grid_container_width / (card_width + spacing)))

            # Adjust for very small screens
            if screen_width < 800:
                max_cols = 1  # Force single column on very small screens

            # Add faculty cards to grid with centering containers
            row, col = 0, 0

            # Create all widgets first before adding to layout (batch processing)
            containers = []

            logger.info(f"Creating faculty cards for {len(faculties)} faculty members")

            for faculty in faculties:
                try:
                    # Create a container widget to center the card
                    container = QWidget()
                    container.setStyleSheet("background-color: transparent;")
                    container_layout = QHBoxLayout(container)
                    container_layout.setContentsMargins(0, 0, 0, 0)
                    container_layout.setAlignment(Qt.AlignCenter)

                    # Convert faculty object to dictionary format expected by FacultyCard
                    # Access all attributes at once to avoid DetachedInstanceError
                    faculty_id = faculty.id
                    faculty_name = faculty.name
                    faculty_department = faculty.department
                    faculty_status = faculty.status
                    faculty_always_available = getattr(faculty, 'always_available', False)
                    faculty_email = getattr(faculty, 'email', '')
                    faculty_room = getattr(faculty, 'room', None)

                    faculty_data = {
                        'id': faculty_id,
                        'name': faculty_name,
                        'department': faculty_department,
                        'available': faculty_status,
                        'status': 'Available' if faculty_status else 'Unavailable',
                        'email': faculty_email,
                        'room': faculty_room
                    }

                    logger.debug(f"Creating card for faculty {faculty.name}: available={faculty_data['available']}, status={faculty_data['status']}")

                    # Get pooled faculty card
                    card = self.faculty_card_manager.get_faculty_card(
                        faculty_data,
                        consultation_callback=lambda f_data=faculty_data: self.show_consultation_form_safe(f_data)
                    )

                    # Connect consultation signal if it exists
                    if hasattr(card, 'consultation_requested'):
                        # Use faculty_data dictionary instead of faculty object to avoid type mismatch
                        card.consultation_requested.connect(lambda f_data=faculty_data: self.show_consultation_form_safe(f_data))

                    # Add card to container
                    container_layout.addWidget(card)

                    # Store container for batch processing
                    containers.append((container, row, col))

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

                    logger.debug(f"Successfully created card for faculty {faculty.name}")

                except Exception as e:
                    logger.error(f"Error creating faculty card for {faculty.name}: {e}")
                    continue

            # Now add all containers to the grid at once
            for container, r, c in containers:
                self.faculty_grid.addWidget(container, r, c)

            # Log successful population
            logger.info(f"Successfully populated faculty grid with {len(containers)} faculty cards")

        finally:
            # Re-enable updates after all changes are made
            self.setUpdatesEnabled(True)

    def _show_empty_faculty_message(self):
        """
        Show a message when no faculty members are available.
        """
        logger.info("Showing empty faculty message")

        # Create a message widget
        message_widget = QWidget()
        message_widget.setMinimumHeight(300)  # Ensure it's visible
        message_layout = QVBoxLayout(message_widget)
        message_layout.setAlignment(Qt.AlignCenter)
        message_layout.setSpacing(20)

        # Title
        title_label = QLabel("No Faculty Members Available")
        title_label.setObjectName("empty_state_title")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel#empty_state_title {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px;
                padding: 20px;
            }
        """)
        message_layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Faculty members need to be added through the admin dashboard.\nOnce added, they will appear here when available for consultation.\n\nPlease contact your administrator to add faculty members.")
        desc_label.setObjectName("empty_state_desc")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel#empty_state_desc {
                font-size: 18px;
                color: #7f8c8d;
                margin: 10px 20px;
                padding: 20px;
                line-height: 1.6;
                background-color: #f8f9fa;
                border-radius: 10px;
                border: 2px solid #e9ecef;
            }
        """)
        message_layout.addWidget(desc_label)

        # Add some spacing
        message_layout.addStretch()

        # Add the message widget to the grid - span all columns
        self.faculty_grid.addWidget(message_widget, 0, 0, 1, self.faculty_grid.columnCount() if self.faculty_grid.columnCount() > 0 else 1)

    def _show_loading_indicator(self):
        """
        Show a loading indicator while faculty data is being fetched.
        """
        if self._is_loading:
            return  # Already showing loading indicator

        self._is_loading = True
        logger.debug("Showing loading indicator")

        # Create loading widget
        loading_widget = QWidget()
        loading_widget.setMinimumHeight(200)
        loading_layout = QVBoxLayout(loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        loading_layout.setSpacing(15)

        # Loading animation (simple text-based)
        loading_label = QLabel("Loading Faculty Information...")
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #3498db;
                padding: 20px;
            }
        """)
        loading_layout.addWidget(loading_label)

        # Progress indicator
        progress_label = QLabel("Please wait while we fetch the latest faculty data...")
        progress_label.setAlignment(Qt.AlignCenter)
        progress_label.setWordWrap(True)
        progress_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding: 10px;
            }
        """)
        loading_layout.addWidget(progress_label)

        # Store reference and add to grid
        self._loading_widget = loading_widget
        self.faculty_grid.addWidget(loading_widget, 0, 0, 1, 1)

    def _hide_loading_indicator(self):
        """
        Hide the loading indicator.
        """
        if not self._is_loading or not self._loading_widget:
            return

        logger.debug("Hiding loading indicator")

        # Remove loading widget from grid
        self.faculty_grid.removeWidget(self._loading_widget)
        self._loading_widget.deleteLater()
        self._loading_widget = None
        self._is_loading = False

    def _show_error_message(self, error_text):
        """
        Show an error message in the faculty grid.

        Args:
            error_text (str): Error message to display
        """
        logger.info(f"Showing error message: {error_text}")

        # Clear existing grid first
        self._clear_faculty_grid_pooled()

        # Create error widget
        error_widget = QWidget()
        error_widget.setMinimumHeight(250)
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignCenter)
        error_layout.setSpacing(15)

        # Error title
        error_title = QLabel("⚠️ Error Loading Faculty Data")
        error_title.setAlignment(Qt.AlignCenter)
        error_title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #e74c3c;
                padding: 15px;
            }
        """)
        error_layout.addWidget(error_title)

        # Error message
        error_message = QLabel(error_text)
        error_message.setAlignment(Qt.AlignCenter)
        error_message.setWordWrap(True)
        error_message.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7f8c8d;
                padding: 10px 20px;
                background-color: #fdf2f2;
                border: 2px solid #f5c6cb;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        error_layout.addWidget(error_message)

        # Retry instruction
        retry_label = QLabel("The system will automatically retry in a few moments.\nIf the problem persists, please contact your administrator.")
        retry_label.setAlignment(Qt.AlignCenter)
        retry_label.setWordWrap(True)
        retry_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #95a5a6;
                padding: 10px;
                font-style: italic;
            }
        """)
        error_layout.addWidget(retry_label)

        # Add to grid
        self.faculty_grid.addWidget(error_widget, 0, 0, 1, 1)

    def filter_faculty(self):
        """
        Filter faculty grid based on search text and filter selection.
        Uses a debounce mechanism to prevent excessive updates.
        """
        # Cancel any pending filter operation
        if hasattr(self, '_filter_timer') and self._filter_timer.isActive():
            self._filter_timer.stop()

        # Create a new timer for debouncing
        if not hasattr(self, '_filter_timer'):
            self._filter_timer = QTimer(self)
            self._filter_timer.setSingleShot(True)
            self._filter_timer.timeout.connect(self._perform_filter)

        # Start the timer - will trigger _perform_filter after 300ms
        self._filter_timer.start(300)

    def _perform_filter(self):
        """
        Perform filtering with proper error handling.
        """
        try:
            from ..controllers import FacultyController
            
            filter_text = self.search_input.text().strip().lower()
            show_available = self.filter_combo.currentData()
            
            faculty_controller = FacultyController()
            faculties = faculty_controller.get_all_faculty()
            
            # Convert to safe faculty data format
            safe_faculties = []
            for faculty in faculties:
                faculty_data = {
                    'id': faculty.id,
                    'name': faculty.name,
                    'department': faculty.department,
                    'available': faculty.status,
                    'status': 'Available' if faculty.status else 'Unavailable',
                    'email': faculty.email,
                    'room': getattr(faculty, 'room', None)
                }
                safe_faculties.append(faculty_data)
            
            # Apply filters
            if filter_text:
                safe_faculties = [f for f in safe_faculties if filter_text in f['name'].lower() or filter_text in f['department'].lower()]
            
            if show_available:
                safe_faculties = [f for f in safe_faculties if f['available']]
            
            # Use safe population method
            self.populate_faculty_grid_safe(safe_faculties)
            
        except Exception as e:
            logger.error(f"Error performing filter: {str(e)}")
            self._show_error_message(f"Filter error: {str(e)}")

    def refresh_faculty_status(self):
        """
        Refresh faculty status with improved error handling and caching.
        """
        try:
            # Import faculty controller
            from ..controllers import FacultyController

            # Get faculty controller
            faculty_controller = FacultyController()

            # Get all faculty
            faculties = faculty_controller.get_all_faculty()

            # Convert to safe faculty data format
            safe_faculties = []
            for faculty in faculties:
                faculty_data = {
                    'id': faculty.id,
                    'name': faculty.name,
                    'department': faculty.department,
                    'available': faculty.status,
                    'status': 'Available' if faculty.status else 'Unavailable',
                    'email': faculty.email,
                    'room': getattr(faculty, 'room', None)
                }
                safe_faculties.append(faculty_data)

            # Check if data has changed before updating
            new_hash = self._extract_safe_faculty_data(safe_faculties)
            if hasattr(self, '_last_faculty_hash') and self._last_faculty_hash == new_hash:
                logger.debug("Faculty data unchanged, skipping UI update")
                return

            # Update the grid using safe method
            self.populate_faculty_grid_safe(safe_faculties)

            # Store current faculty data for future comparison
            self._last_faculty_data_list = safe_faculties
            self._last_faculty_hash = new_hash

            # Also update the consultation panel with the latest faculty options (convert back to objects)
            if hasattr(self, 'consultation_panel'):
                self.consultation_panel.set_faculty_options(faculties)
                logger.debug("Refreshed consultation panel faculty options in refresh_faculty_status")

            # Ensure scroll area starts at the top
            if hasattr(self, 'faculty_scroll') and self.faculty_scroll:
                self.faculty_scroll.verticalScrollBar().setValue(0)

        except Exception as e:
            logger.error(f"Error refreshing faculty status: {str(e)}")
            self._show_error_message(f"Failed to refresh faculty list: {str(e)}")

    def _extract_faculty_data(self, faculties):
        """
        Extract relevant data from faculty objects for comparison.

        Args:
            faculties (list): List of faculty objects

        Returns:
            str: Hash of faculty data for efficient comparison
        """
        import hashlib
        # Create a string representation of all relevant faculty data
        data_str = ""
        for f in sorted(faculties, key=lambda x: x.id):  # Sort for consistent hashing
            try:
                # Access attributes safely to avoid DetachedInstanceError
                faculty_id = f.id
                faculty_name = f.name
                faculty_status = f.status
                faculty_department = getattr(f, 'department', '')
                data_str += f"{faculty_id}:{faculty_name}:{faculty_status}:{faculty_department};"
            except Exception as e:
                logger.warning(f"Error accessing faculty attributes for hashing: {e}")
                # Use a fallback representation
                data_str += f"error:{e};"

        # Return hash for efficient comparison
        return hashlib.md5(data_str.encode()).hexdigest()

    def _compare_faculty_data(self, old_hash, new_faculties):
        """
        Compare old and new faculty data to detect changes using hash comparison.

        Args:
            old_hash (str): Previous faculty data hash
            new_faculties (list): New faculty objects

        Returns:
            bool: True if data is the same, False if there are changes
        """
        if old_hash is None:
            return False  # First time, consider as changed

        # Extract hash from new faculty objects
        new_hash = self._extract_faculty_data(new_faculties)

        return old_hash == new_hash

    def show_consultation_form(self, faculty_or_id):
        """
        Show the consultation request form for a specific faculty.

        Args:
            faculty_or_id (object or int): Faculty object or Faculty ID
        """
        logger.debug(f"show_consultation_form called with: {faculty_or_id} (type: {type(faculty_or_id)})")
        faculty_object = None

        if isinstance(faculty_or_id, int):
            logger.info(f"show_consultation_form received faculty ID: {faculty_or_id}. Fetching object.")
            try:
                from ..controllers import FacultyController # Local import to avoid circular dependency issues at module load
                fc = FacultyController()
                faculty_object = fc.get_faculty_by_id(faculty_or_id)
                if not faculty_object:
                    logger.warning(f"Faculty with ID {faculty_or_id} not found by controller.")
                    self.show_notification(
                        f"Faculty with ID {faculty_or_id} not found.",
                        "error"
                    )
                    return
            except Exception as e:
                logger.error(f"Error fetching faculty by ID {faculty_or_id} in show_consultation_form: {str(e)}")
                self.show_notification(
                    f"Error retrieving details for faculty ID {faculty_or_id}.",
                    "error"
                )
                return
        elif hasattr(faculty_or_id, 'status') and hasattr(faculty_or_id, 'name') and hasattr(faculty_or_id, 'id'): # Basic check for Faculty-like object
            logger.debug("show_consultation_form received a faculty-like object.")
            faculty_object = faculty_or_id
        else:
            logger.error(f"show_consultation_form called with invalid/unexpected type: {type(faculty_or_id)}, value: {faculty_or_id}")
            self.show_notification("An unexpected error occurred while trying to show the consultation form. Invalid faculty data.", "error")
            return

        # Now use faculty_object for the rest of the method
        if not faculty_object.status:
            self.show_notification(
                f"Faculty {faculty_object.name} (ID: {faculty_object.id}) is currently unavailable for consultation.",
                "error"
            )
            return

        # Also populate the dropdown with all available faculty
        try:
            from ..controllers import FacultyController # Local import
            faculty_controller = FacultyController()
            available_faculty = faculty_controller.get_all_faculty(filter_available=True)

            # Set the faculty and faculty options in the consultation panel
            self.consultation_panel.set_faculty(faculty_object) # Use the validated/fetched object
            self.consultation_panel.set_faculty_options(available_faculty)
        except Exception as e:
            logger.error(f"Error loading available faculty for consultation form: {str(e)}")
            self.show_notification("Error preparing consultation form.", "error")

    def handle_consultation_request(self, faculty, message, course_code):
        """
        Handle consultation request submission.

        Args:
            faculty (object): Faculty object
            message (str): Consultation request message
            course_code (str): Optional course code
        """
        try:
            # Import consultation controller
            from ..controllers import ConsultationController

            # Get consultation controller
            consultation_controller = ConsultationController()

            # Create consultation
            if self.student:
                # Get student ID from either object or dictionary
                if isinstance(self.student, dict):
                    student_id = self.student.get('id')
                else:
                    # Legacy support for student objects
                    student_id = getattr(self.student, 'id', None)

                if not student_id:
                    logger.error("Cannot create consultation: student ID not available")
                    QMessageBox.warning(
                        self,
                        "Consultation Request",
                        "Unable to submit consultation request. Student information is incomplete."
                    )
                    return

                consultation = consultation_controller.create_consultation(
                    student_id=student_id,
                    faculty_id=faculty.id,
                    request_message=message,
                    course_code=course_code
                )

                if consultation:
                    # Show confirmation
                    QMessageBox.information(
                        self,
                        "Consultation Request",
                        f"Your consultation request with {faculty.name} has been submitted."
                    )

                    # Refresh the consultation history
                    self.consultation_panel.refresh_history()
                else:
                    QMessageBox.warning(
                        self,
                        "Consultation Request",
                        f"Failed to submit consultation request. Please try again."
                    )
            else:
                # No student logged in
                QMessageBox.warning(
                    self,
                    "Consultation Request",
                    "You must be logged in to submit a consultation request."
                )
        except Exception as e:
            logger.error(f"Error creating consultation: {str(e)}")
            QMessageBox.warning(
                self,
                "Consultation Request",
                f"An error occurred while submitting your consultation request: {str(e)}"
            )

    def handle_consultation_cancel(self, consultation_id):
        """
        Handle consultation cancellation.

        Args:
            consultation_id (int): ID of the consultation to cancel
        """
        try:
            # Import consultation controller
            from ..controllers import ConsultationController

            # Get consultation controller
            consultation_controller = ConsultationController()

            # Cancel consultation
            consultation = consultation_controller.cancel_consultation(consultation_id)

            if consultation:
                # Show confirmation
                QMessageBox.information(
                    self,
                    "Consultation Cancelled",
                    f"Your consultation request has been cancelled."
                )

                # Refresh the consultation history
                self.consultation_panel.refresh_history()
            else:
                QMessageBox.warning(
                    self,
                    "Consultation Cancellation",
                    f"Failed to cancel consultation request. Please try again."
                )
        except Exception as e:
            logger.error(f"Error cancelling consultation: {str(e)}")
            QMessageBox.warning(
                self,
                "Consultation Cancellation",
                f"An error occurred while cancelling your consultation request: {str(e)}"
            )

    def save_splitter_state(self):
        """
        Save the current splitter state to settings.
        """
        try:
            # Import QSettings
            from PyQt5.QtCore import QSettings

            # Create settings object
            settings = QSettings("ConsultEase", "Dashboard")

            # Save splitter state
            settings.setValue("splitter_state", self.content_splitter.saveState())
            settings.setValue("splitter_sizes", self.content_splitter.sizes())

            logger.debug("Saved splitter state")
        except Exception as e:
            logger.error(f"Error saving splitter state: {e}")

    def restore_splitter_state(self):
        """
        Restore the splitter state from settings.
        """
        try:
            # Import QSettings
            from PyQt5.QtCore import QSettings

            # Create settings object
            settings = QSettings("ConsultEase", "Dashboard")

            # Restore splitter state if available
            if settings.contains("splitter_state"):
                state = settings.value("splitter_state")
                if state:
                    self.content_splitter.restoreState(state)
                    logger.debug("Restored splitter state")

            # Fallback to sizes if state restoration fails
            elif settings.contains("splitter_sizes"):
                sizes = settings.value("splitter_sizes")
                if sizes:
                    self.content_splitter.setSizes(sizes)
                    logger.debug("Restored splitter sizes")
        except Exception as e:
            logger.error(f"Error restoring splitter state: {e}")
            # Use default sizes as fallback
            screen_width = QApplication.desktop().screenGeometry().width()
            self.content_splitter.setSizes([int(screen_width * 0.6), int(screen_width * 0.4)])

    def closeEvent(self, event):
        """
        Handle window close event to disconnect MQTT service.
        """
        try:
            if hasattr(self, 'mqtt_service') and self.mqtt_service:
                self.mqtt_service.disconnect()
                logger.info("MQTT Service disconnected in DashboardWindow.")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT service in DashboardWindow: {e}")
        super().closeEvent(event)

    def logout(self):
        """
        Handle logout button click.
        """
        # Save splitter state before logout
        self.save_splitter_state()

        self.change_window.emit("login", None)

    def show_notification(self, message, message_type="info"):
        """
        Show a notification message to the user using the standardized notification system.

        Args:
            message (str): Message to display
            message_type (str): Type of message ('success', 'error', 'warning', or 'info')
        """
        try:
            # Import notification manager
            from ..utils.notification import NotificationManager

            # Map message types
            type_mapping = {
                "success": NotificationManager.SUCCESS,
                "error": NotificationManager.ERROR,
                "warning": NotificationManager.WARNING,
                "info": NotificationManager.INFO
            }

            # Get standardized message type
            std_type = type_mapping.get(message_type.lower(), NotificationManager.INFO)

            # Show notification using the manager
            title = message_type.capitalize()
            if message_type == "error":
                title = "Error"
            elif message_type == "success":
                title = "Success"
            elif message_type == "warning":
                title = "Warning"
            else:
                title = "Information"

            NotificationManager.show_message(self, title, message, std_type)

        except ImportError:
            # Fallback to basic message boxes if notification manager is not available
            logger.warning("NotificationManager not available, using basic message boxes")
            if message_type == "success":
                QMessageBox.information(self, "Success", message)
            elif message_type == "error":
                QMessageBox.warning(self, "Error", message)
            elif message_type == "warning":
                QMessageBox.warning(self, "Warning", message)
            else:
                QMessageBox.information(self, "Information", message)

    def _scroll_faculty_to_top(self):
        """
        Scroll the faculty grid to the top.
        This is called after the UI is fully loaded to ensure faculty cards are visible.
        """
        if hasattr(self, 'faculty_scroll') and self.faculty_scroll:
            self.faculty_scroll.verticalScrollBar().setValue(0)
            logger.debug("Scrolled faculty grid to top")

    def _clear_faculty_grid_pooled(self):
        """
        Clear the faculty grid efficiently using pooled cards.
        """
        # Return all active faculty cards to the pool
        self.faculty_card_manager.clear_all_cards()

        # Clear the grid layout
        while self.faculty_grid.count():
            item = self.faculty_grid.takeAt(0)
            if item.widget():
                # Don't delete the widget, it's managed by the pool
                item.widget().setParent(None)

    def showEvent(self, event):
        """
        Handle window show event to trigger initial faculty data loading.
        """
        # Call parent showEvent first
        super().showEvent(event)

        # Load faculty data immediately when the window is first shown
        # Only do this if we haven't loaded faculty data yet
        if not hasattr(self, '_initial_load_done') or not self._initial_load_done:
            logger.info("Dashboard window shown - triggering initial faculty data load")
            self._initial_load_done = True

            # Schedule the initial faculty load after a short delay to ensure UI is ready
            QTimer.singleShot(100, self._perform_initial_faculty_load)

    def _perform_initial_faculty_load(self):
        """
        Perform the initial load of faculty data.
        """
        try:
            from ..controllers import FacultyController

            faculty_controller = FacultyController()
            faculties = faculty_controller.get_all_faculty()

            # Convert to safe faculty data format
            safe_faculties = []
            for faculty in faculties:
                faculty_data = {
                    'id': faculty.id,
                    'name': faculty.name,
                    'department': faculty.department,
                    'available': faculty.status,
                    'status': 'Available' if faculty.status else 'Unavailable',
                    'email': faculty.email,
                    'room': getattr(faculty, 'room', None)
                }
                safe_faculties.append(faculty_data)

            if safe_faculties:
                self.populate_faculty_grid_safe(safe_faculties)
                self._last_faculty_data_list = safe_faculties
                self._last_faculty_hash = self._extract_safe_faculty_data(safe_faculties)
                
                # Update consultation panel options with object versions
                if hasattr(self, 'consultation_panel'):
                    self.consultation_panel.set_faculty_options(faculties)
            else:
                self._show_empty_faculty_message()

        except Exception as e:
            logger.error(f"Error in initial faculty load: {str(e)}")
            self._show_error_message(f"Failed to load faculty data: {str(e)}")
        finally:
            self._hide_loading_indicator()

    def closeEvent(self, event):
        """
        Handle window close event with proper cleanup.
        """
        # Clean up faculty card manager
        if hasattr(self, 'faculty_card_manager'):
            self.faculty_card_manager.clear_all_cards()

        # Save splitter state before closing
        self.save_splitter_state()

        # Unsubscribe from MQTT topics
        self.cleanup_realtime_updates()

        # Call parent close event
        super().closeEvent(event)

    def setup_realtime_updates(self):
        """Set up real-time MQTT subscriptions for faculty status updates."""
        try:
            from ..utils.mqtt_utils import subscribe_to_topic
            from ..utils.mqtt_topics import MQTTTopics
            
            # Subscribe to faculty status updates
            subscribe_to_topic("consultease/faculty/+/status_update", self.handle_realtime_status_update)
            subscribe_to_topic(MQTTTopics.SYSTEM_NOTIFICATIONS, self.handle_system_notification)
            
            logger.info("Real-time faculty status updates enabled")
        except Exception as e:
            logger.error(f"Failed to set up real-time updates: {e}")

    def cleanup_realtime_updates(self):
        """Clean up MQTT subscriptions on window close."""
        try:
            # Nothing to do here as MQTT subscriptions are handled at the service level
            # and will be automatically removed when the application exits
            pass
        except Exception as e:
            logger.error(f"Error cleaning up MQTT subscriptions: {e}")

    def handle_realtime_status_update(self, topic, data):
        """
        Handle real-time faculty status updates from MQTT.
        
        Args:
            topic (str): MQTT topic
            data (dict): Status update data
        """
        try:
            logger.info(f"[MQTT DASHBOARD HANDLER] handle_realtime_status_update - Topic: {topic}, Data: {data}")
            logger.debug(f"Received real-time faculty status update: {data}")
            
            # Extract faculty ID and status
            faculty_id = data.get('faculty_id')
            new_status = data.get('status')
            
            if faculty_id is None or new_status is None:
                logger.warning(f"Invalid faculty status update: {data}")
                return
                
            # Find and update the corresponding faculty card
            card_updated = self.update_faculty_card_status(faculty_id, new_status)

            # If the card was visible and updated, or even if not (status might affect filters),
            # trigger a full refresh to ensure data consistency across the dashboard.
            # This will re-fetch from DB, re-populate grid, and update consultation panel options.
            logger.debug(f"Realtime update for faculty {faculty_id} processed, card_updated: {card_updated}. Triggering full UI refresh.")
            # Use QTimer.singleShot to schedule the refresh in the next event loop iteration.
            # This can help coalesce multiple rapid updates and avoid immediate heavy refresh on every single MQTT message.
            self.request_ui_refresh.emit()
            
        except Exception as e:
            logger.error(f"Error handling real-time status update: {e}")

    def handle_system_notification(self, topic, data):
        """
        Handle system notifications from MQTT.
        
        Args:
            topic (str): MQTT topic
            data (dict): Notification data
        """
        try:
            logger.info(f"[MQTT DASHBOARD HANDLER] handle_system_notification - Topic: {topic}, Data: {data}")
            # Check if this is a faculty status notification
            if data.get('type') == 'faculty_status':
                faculty_id = data.get('faculty_id')
                new_status = data.get('status')
                
                if faculty_id is not None and new_status is not None:
                    # Update the faculty card
                    card_updated = self.update_faculty_card_status(faculty_id, new_status)
                    logger.debug(f"System notification for faculty {faculty_id} status processed, card_updated: {card_updated}. Triggering full UI refresh.")
                    # Schedule a full refresh to ensure data consistency
                    self.request_ui_refresh.emit()
        except Exception as e:
            logger.error(f"Error handling system notification: {e}")

    def update_faculty_card_status(self, faculty_id, new_status_bool):
        """
        Update the status of a faculty card in real-time.
        
        Args:
            faculty_id (int): Faculty ID
            new_status_bool (bool): New status (True = Available, False = Unavailable)
        """
        try:
            # Find the faculty card in the grid
            for i in range(self.faculty_grid.count()):
                container_widget = self.faculty_grid.itemAt(i).widget()
                if not container_widget:
                    continue
                    
                container_layout = container_widget.layout()
                if not container_layout or container_layout.count() == 0:
                    continue
                    
                faculty_card = container_layout.itemAt(0).widget()
                # Ensure it's a PooledFacultyCard and has the method
                if not faculty_card or not hasattr(faculty_card, 'update_status') or not hasattr(faculty_card, 'faculty_data'):
                    continue
                
                if faculty_card.faculty_data.get('id') == faculty_id:
                    status_string = "available" if new_status_bool else "offline" # Or "unavailable"
                    
                    # Update card's internal state and display using its own method
                    faculty_card.update_status(status_string)
                    
                    # Update faculty_data dictionary stored in the card (if update_status doesn't do it)
                    # PooledFacultyCard.update_status already updates self.faculty_data['status']
                    # It also updates self.faculty_data['available'] effectively via the status string.
                    faculty_card.faculty_data['available'] = new_status_bool


                    # Update card's objectName for theming
                    new_object_name = "faculty_card_available" if new_status_bool else "faculty_card_unavailable"
                    if faculty_card.objectName() != new_object_name:
                        faculty_card.setObjectName(new_object_name)
                        # Force style refresh
                        faculty_card.style().unpolish(faculty_card)
                        faculty_card.style().polish(faculty_card)
                        faculty_card.update()

                    logger.debug(f"Updated faculty card for ID {faculty_id} to status: {status_string} via card method")
                    return True # Found and updated
            
            logger.debug(f"Faculty card for ID {faculty_id} not found in current view for status update.")
            return False # Card not found
            
        except Exception as e:
            logger.error(f"Error updating faculty card status for ID {faculty_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def setup_real_time_updates(self):
        """
        Set up real-time updates for consultation status changes.
        """
        try:
            # Import and register with faculty response controller
            from ..controllers.faculty_response_controller import get_faculty_response_controller
            
            self.faculty_response_controller = get_faculty_response_controller()
            self.faculty_response_controller.register_callback(self.handle_faculty_response_update)
            
            logger.info("Registered for real-time consultation status updates")
            
        except Exception as e:
            logger.error(f"Failed to set up real-time updates: {str(e)}")

    def handle_faculty_response_update(self, response_data):
        """
        Handle real-time faculty response updates.
        
        Args:
            response_data (dict): Faculty response data containing consultation updates
        """
        try:
            # Check if this response is for the current student
            student_id = response_data.get('student_id')
            if not student_id:
                return
                
            # Get current student ID
            current_student_id = None
            if isinstance(self.student, dict):
                current_student_id = self.student.get('id')
            else:
                current_student_id = getattr(self.student, 'id', None)
                
            if current_student_id != student_id:
                return  # Not for this student
                
            # Extract response information
            response_type = response_data.get('response_type', 'Unknown')
            faculty_name = response_data.get('faculty_name', 'Faculty')
            consultation_id = response_data.get('consultation_id')
            
            # Show notification to student
            self.show_consultation_status_notification(response_type, faculty_name, consultation_id)
            
            # Refresh consultation history if panel is available
            if self.consultation_panel:
                self.consultation_panel.refresh_history()
                
            logger.info(f"Processed real-time consultation update: {response_type} from {faculty_name}")
            
        except Exception as e:
            logger.error(f"Error handling faculty response update: {str(e)}")

    def show_consultation_status_notification(self, response_type, faculty_name, consultation_id):
        """
        Show a notification to the student about consultation status change.
        
        Args:
            response_type (str): Type of faculty response (ACKNOWLEDGE, BUSY, etc.)
            faculty_name (str): Name of the faculty member
            consultation_id (int): ID of the consultation
        """
        try:
            # Import notification utilities
            from ..utils.notification import NotificationManager
            
            # Create appropriate notification message
            if response_type == "ACKNOWLEDGE" or response_type == "ACCEPTED":
                title = "Consultation Accepted!"
                message = f"{faculty_name} has accepted your consultation request."
                notification_type = NotificationManager.SUCCESS
            elif response_type == "BUSY" or response_type == "UNAVAILABLE":
                title = "Faculty Busy"
                message = f"{faculty_name} is currently busy and cannot take your consultation request."
                notification_type = NotificationManager.WARNING
            elif response_type == "REJECTED" or response_type == "DECLINED":
                title = "Consultation Declined"
                message = f"{faculty_name} has declined your consultation request."
                notification_type = NotificationManager.ERROR
            elif response_type == "COMPLETED":
                title = "Consultation Completed"
                message = f"Your consultation with {faculty_name} has been completed."
                notification_type = NotificationManager.INFO
            else:
                title = "Consultation Update"
                message = f"{faculty_name} has responded to your consultation request."
                notification_type = NotificationManager.INFO
            
            # Show the notification
            NotificationManager.show_message(
                self,
                title,
                message,
                notification_type
            )
            
        except ImportError:
            # Fallback to basic message box if notification manager not available
            from PyQt5.QtWidgets import QMessageBox
            
            if response_type == "ACKNOWLEDGE" or response_type == "ACCEPTED":
                QMessageBox.information(self, "Consultation Accepted", 
                                      f"{faculty_name} has accepted your consultation request.")
            elif response_type == "BUSY" or response_type == "UNAVAILABLE":
                QMessageBox.warning(self, "Faculty Busy", 
                                  f"{faculty_name} is currently busy and cannot take your consultation request.")
            else:
                QMessageBox.information(self, "Consultation Update", 
                                      f"{faculty_name} has responded to your consultation request.")
        except Exception as e:
            logger.error(f"Error showing consultation status notification: {str(e)}")
