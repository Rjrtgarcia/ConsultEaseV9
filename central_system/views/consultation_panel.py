"""
Consultation panel module.
Contains the consultation request form and consultation history panel.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QFrame, QLineEdit, QTextEdit,
                            QComboBox, QMessageBox, QTabWidget, QTableWidget,
                            QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
                            QSizePolicy, QProgressBar, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QColor

import logging

# Set up logging
logger = logging.getLogger(__name__)
import json # For parsing MQTT payload
from ..models.consultation import ConsultationStatus # Added for MQTT handler

class ConsultationRequestForm(QFrame):
    """
    Form to request a consultation with a faculty member.
    """
    request_submitted = pyqtSignal(object, str, str)

    def __init__(self, faculty=None, parent=None):
        super().__init__(parent)
        self.faculty = faculty
        self.faculty_options = []
        self.init_ui()

    def init_ui(self):
        """
        Initialize the consultation request form UI.
        """
        # Import theme system
        from ..utils.theme import ConsultEaseTheme

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("consultation_request_form")

        # Apply theme-based stylesheet with gold and blue theme
        self.setStyleSheet('''
            QFrame#consultation_request_form {
                background-color: #ffffff;
                border: 2px solid #DAA520;
                border-radius: 10px;
                padding: 20px;
            }
            QLabel {
                font-size: 16pt;
                color: #1E90FF;
                font-weight: 500;
                margin-bottom: 5px;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 2px solid #4169E1;
                border-radius: 5px;
                padding: 15px;
                background-color: #ffffff;
                font-size: 16pt;
                color: #333333;
                margin: 5px 0;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #FFD700;
                background-color: #FFFEF7;
            }
            QPushButton {
                border-radius: 5px;
                padding: 15px 25px;
                font-size: 16pt;
                font-weight: bold;
                color: white;
                margin: 10px 0;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        ''')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Form title
        title_label = QLabel("Request Consultation")
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #DAA520;")
        main_layout.addWidget(title_label)

        # Faculty selection
        faculty_layout = QHBoxLayout()
        faculty_label = QLabel("Faculty:")
        faculty_label.setFixedWidth(120)
        faculty_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #1E90FF;")
        self.faculty_combo = QComboBox()
        self.faculty_combo.setMinimumWidth(300)
        self.faculty_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #4169E1;
                border-radius: 5px;
                padding: 10px;
                background-color: #ffffff;
                font-size: 12pt;
                color: #333333;
            }
            QComboBox:focus {
                border: 2px solid #FFD700;
                background-color: #FFFEF7;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #4169E1;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #4169E1;
                selection-background-color: #FFD700;
                selection-color: #333333;
                background-color: #ffffff;
                font-size: 12pt;
            }
        """)
        faculty_layout.addWidget(faculty_label)
        faculty_layout.addWidget(self.faculty_combo)
        main_layout.addLayout(faculty_layout)

        # Course code input
        course_layout = QHBoxLayout()
        course_label = QLabel("Course Code:")
        course_label.setFixedWidth(120)
        course_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #1E90FF;")
        self.course_input = QLineEdit()
        self.course_input.setPlaceholderText("e.g., CS101 (optional)")
        self.course_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #4169E1;
                border-radius: 5px;
                padding: 10px;
                background-color: #ffffff;
                font-size: 12pt;
                color: #333333;
            }
            QLineEdit:focus {
                border: 2px solid #FFD700;
                background-color: #FFFEF7;
            }
        """)
        course_layout.addWidget(course_label)
        course_layout.addWidget(self.course_input)
        main_layout.addLayout(course_layout)

        # Message input
        message_layout = QVBoxLayout()
        message_label = QLabel("Consultation Details:")
        message_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #1E90FF;")
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Describe what you'd like to discuss...")
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #4169E1;
                border-radius: 5px;
                padding: 10px;
                background-color: #ffffff;
                font-size: 12pt;
                color: #333333;
            }
            QTextEdit:focus {
                border: 2px solid #FFD700;
                background-color: #FFFEF7;
            }
        """)
        self.message_input.setMinimumHeight(150)
        message_layout.addWidget(message_label)
        message_layout.addWidget(self.message_input)
        main_layout.addLayout(message_layout)

        # Character count with visual indicator
        char_count_frame = QFrame()
        char_count_layout = QVBoxLayout(char_count_frame)
        char_count_layout.setContentsMargins(0, 0, 0, 0)
        char_count_layout.setSpacing(2)

        # Label and progress bar in a horizontal layout
        count_indicator_layout = QHBoxLayout()
        count_indicator_layout.setContentsMargins(0, 0, 0, 0)

        self.char_count_label = QLabel("0/500 characters")
        self.char_count_label.setAlignment(Qt.AlignLeft)
        self.char_count_label.setStyleSheet("color: #1E90FF; font-size: 11pt; font-weight: bold;")

        # Add a small info label about the limit
        char_limit_info = QLabel("(500 character limit)")
        char_limit_info.setStyleSheet("color: #DAA520; font-size: 10pt; font-weight: bold;")
        char_limit_info.setAlignment(Qt.AlignRight)

        count_indicator_layout.addWidget(self.char_count_label)
        count_indicator_layout.addStretch()
        count_indicator_layout.addWidget(char_limit_info)

        char_count_layout.addLayout(count_indicator_layout)

        # Add progress bar for visual feedback
        self.char_count_progress = QProgressBar()
        self.char_count_progress.setRange(0, 500)
        self.char_count_progress.setValue(0)
        self.char_count_progress.setTextVisible(False)
        self.char_count_progress.setFixedHeight(10)
        self.char_count_progress.setStyleSheet("""
            QProgressBar {
                background-color: #f0f0f0;
                border: 1px solid #DAA520;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #4169E1;
                border-radius: 5px;
            }
        """)

        char_count_layout.addWidget(self.char_count_progress)
        main_layout.addWidget(char_count_frame)

        # Connect text changed signal to update character count
        self.message_input.textChanged.connect(self.update_char_count)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet('''
            QPushButton {
                background-color: #DAA520;
                min-width: 120px;
            }
        ''')
        cancel_button.clicked.connect(self.cancel_request)

        submit_button = QPushButton("Submit Request")
        submit_button.setStyleSheet('''
            QPushButton {
                background-color: #4169E1;
                min-width: 120px;
            }
        ''')
        submit_button.clicked.connect(self.submit_request)

        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(submit_button)

        main_layout.addLayout(button_layout)

    def update_char_count(self):
        """
        Update the character count label and progress bar.
        """
        count = len(self.message_input.toPlainText())
        color = "#1E90FF"  # Default blue
        progress_color = "#4169E1"  # Default blue

        if count > 400:
            color = "#DAA520"  # Warning gold
            progress_color = "#DAA520"
        if count > 500:
            color = "#FF6347"  # Error red-orange
            progress_color = "#FF6347"

        self.char_count_label.setText(f"{count}/500 characters")
        self.char_count_label.setStyleSheet(f"color: {color}; font-size: 11pt; font-weight: bold;")

        # Update progress bar
        self.char_count_progress.setValue(count)
        self.char_count_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #f0f0f0;
                border: 1px solid #DAA520;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {progress_color};
                border-radius: 5px;
            }}
        """)

    def set_faculty(self, faculty):
        """
        Set the faculty for the consultation request.
        Fixed to prevent jarring tab shifting.
        """
        self.faculty = faculty

        # Update the combo box
        if self.faculty and self.faculty_combo.count() > 0:
            for i in range(self.faculty_combo.count()):
                faculty_id = self.faculty_combo.itemData(i)
                if faculty_id == self.faculty.id:
                    self.faculty_combo.setCurrentIndex(i)
                    break

    def set_faculty_options(self, faculty_list):
        """
        Set the available faculty options in the dropdown.
        """
        self.faculty_options = faculty_list
        self.faculty_combo.clear()

        for faculty in faculty_list:
            self.faculty_combo.addItem(f"{faculty.name} ({faculty.department})", faculty.id)

        # If we have a selected faculty, select it in the dropdown
        if self.faculty:
            for i in range(self.faculty_combo.count()):
                faculty_id = self.faculty_combo.itemData(i)
                if faculty_id == self.faculty.id:
                    self.faculty_combo.setCurrentIndex(i)
                    break

    def get_selected_faculty(self):
        """
        Get the selected faculty from the dropdown.
        """
        if self.faculty_combo.count() == 0:
            return self.faculty

        faculty_id = self.faculty_combo.currentData()

        for faculty in self.faculty_options:
            if faculty.id == faculty_id:
                return faculty

        return None

    def submit_request(self):
        """
        Handle the submission of the consultation request with enhanced validation.
        """
        # Validate faculty selection
        faculty = self.get_selected_faculty()
        if not faculty:
            self.show_validation_error("Faculty Selection", "Please select a faculty member.")
            self.faculty_combo.setFocus()
            return

        # Check if faculty is available
        if hasattr(faculty, 'status') and not faculty.status:
            self.show_validation_error("Faculty Availability",
                f"Faculty {faculty.name} is currently unavailable. Please select an available faculty member.")
            self.faculty_combo.setFocus()
            return

        # Validate message content
        message = self.message_input.toPlainText().strip()
        if not message:
            self.show_validation_error("Consultation Details", "Please enter consultation details.")
            self.message_input.setFocus()
            return

        # Check message length
        if len(message) > 500:
            self.show_validation_error("Message Length",
                "Consultation details are too long. Please limit to 500 characters.")
            self.message_input.setFocus()
            return

        # Check message minimum length for meaningful content
        if len(message) < 10:
            self.show_validation_error("Message Content",
                "Please provide more details about your consultation request (minimum 10 characters).")
            self.message_input.setFocus()
            return

        # Validate course code format if provided
        course_code = self.course_input.text().strip()
        if course_code and not self.is_valid_course_code(course_code):
            self.show_validation_error("Course Code Format",
                "Please enter a valid course code (e.g., CS101, MATH202).")
            self.course_input.setFocus()
            return

        # All validation passed, emit signal with the request details
        self.request_submitted.emit(faculty, message, course_code)

    def show_validation_error(self, title, message):
        """
        Show a validation error message using the standardized notification system.

        Args:
            title (str): Error title
            message (str): Error message
        """
        try:
            # Try to use the notification manager
            from ..utils.notification import NotificationManager
            NotificationManager.show_message(
                self,
                title,
                message,
                NotificationManager.WARNING
            )
        except ImportError:
            # Fallback to basic implementation
            error_dialog = QMessageBox(self)
            error_dialog.setWindowTitle("Validation Error")
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setText(f"<b>{title}</b>")
            error_dialog.setInformativeText(message)
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.setDefaultButton(QMessageBox.Ok)
            error_dialog.setStyleSheet("""
                QMessageBox {
                    background-color: #f8f9fa;
                }
                QLabel {
                    color: #212529;
                    font-size: 12pt;
                }
                QPushButton {
                    background-color: #0d3b66;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #0a2f52;
                }
            """)
            error_dialog.exec_()

    def is_valid_course_code(self, course_code):
        """
        Validate course code format.

        Args:
            course_code (str): Course code to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Basic validation: 2-4 letters followed by 3-4 numbers, optionally followed by a letter
        import re
        pattern = r'^[A-Za-z]{2,4}\d{3,4}[A-Za-z]?$'

        # Allow common formats like CS101, MATH202, ENG101A
        return bool(re.match(pattern, course_code))

    def cancel_request(self):
        """
        Cancel the consultation request.
        """
        self.message_input.clear()
        self.course_input.clear()
        self.setVisible(False)

class ConsultationHistoryPanel(QFrame):
    """
    Panel to display consultation history.
    """
    consultation_selected = pyqtSignal(object)
    consultation_cancelled = pyqtSignal(int)

    def __init__(self, student=None, mqtt_service=None, parent=None):
        super().__init__(parent)
        self.student = student
        self.mqtt_service = mqtt_service
        self.consultations = []
        self.init_ui()

        if self.student and self.mqtt_service:
            self._subscribe_to_consultation_updates()
        else:
            if not self.student:
                logger.warning("ConsultationHistoryPanel initialized without a student.")
            if not self.mqtt_service:
                logger.warning("ConsultationHistoryPanel initialized without an MQTT service.")

    def init_ui(self):
        """
        Initialize the consultation history panel UI.
        """
        # Import theme system
        from ..utils.theme import ConsultEaseTheme

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("consultation_history_panel")

        # Apply theme-based stylesheet with gold and blue theme
        self.setStyleSheet('''
            QFrame#consultation_history_panel {
                background-color: #ffffff;
                border: 2px solid #DAA520;
                border-radius: 10px;
                padding: 20px;
            }
            QTableWidget {
                border: 2px solid #4169E1;
                border-radius: 5px;
                background-color: #ffffff;
                alternate-background-color: #FAFAFA;
                gridline-color: #DAA520;
                font-size: 16pt;
                color: #333333;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #DAA520;
            }
            QHeaderView::section {
                background-color: #4169E1;
                color: white;
                padding: 15px;
                border: none;
                font-size: 16pt;
                font-weight: bold;
            }
            QHeaderView::section:first {
                border-top-left-radius: 5px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 5px;
            }
            /* Improve scrollbar visibility */
            QScrollBar:vertical {
                background: #FAFAFA;
                width: 15px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #DAA520;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #B8860B;
            }
            QPushButton {
                border-radius: 5px;
                padding: 12px 20px;
                font-size: 15pt;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        ''')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("My Consultation History")
        title_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #DAA520;")
        main_layout.addWidget(title_label)

        # Consultation table
        self.consultation_table = QTableWidget()
        self.consultation_table.setColumnCount(5)
        self.consultation_table.setHorizontalHeaderLabels(["Faculty", "Course", "Status", "Date", "Actions"])

        # Improved column sizing to ensure action buttons are fully visible
        header = self.consultation_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Faculty - stretch to fill
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Course - fit content
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Status - fit content
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Date - fit content
        header.setSectionResizeMode(4, QHeaderView.Fixed) # Actions - fixed width
        
        # Set minimum widths for better button visibility
        header.setMinimumSectionSize(100)  # Minimum width for any column
        self.consultation_table.setColumnWidth(4, 180)  # Fixed width for Actions column to ensure buttons fit
        
        # Set minimum row height to accommodate buttons properly
        self.consultation_table.verticalHeader().setDefaultSectionSize(50)  # Increase row height
        self.consultation_table.verticalHeader().setMinimumSectionSize(45)  # Minimum row height

        self.consultation_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.consultation_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.consultation_table.setSelectionMode(QTableWidget.SingleSelection)
        self.consultation_table.setAlternatingRowColors(True)

        main_layout.addWidget(self.consultation_table)

        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.setStyleSheet('''
            QPushButton {
                background-color: #4169E1;
                min-width: 120px;
            }
        ''')
        refresh_button.clicked.connect(self.refresh_consultations)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(refresh_button)

        main_layout.addLayout(button_layout)

    def set_student(self, student):
        """
        Set the student for the consultation history.
        """
        self.student = student
        self.refresh_consultations()

    def refresh_consultations(self):
        """
        Refresh the consultation history from the database with loading indicator.
        """
        if not self.student:
            return

        # Get student ID from either object or dictionary
        if isinstance(self.student, dict):
            student_id = self.student.get('id')
        else:
            # Legacy support for student objects
            student_id = getattr(self.student, 'id', None)

        if not student_id:
            return

        try:
            # Import notification utilities
            from ..utils.notification import LoadingDialog, NotificationManager

            # Define the operation to run with progress updates
            def load_consultations(progress_callback):
                # Import consultation controller
                from ..controllers import ConsultationController

                # Update progress
                progress_callback(10, "Connecting to database...")

                # Get consultation controller
                consultation_controller = ConsultationController()

                # Update progress
                progress_callback(30, "Fetching consultation data...")

                # Get consultations for this student
                consultations = consultation_controller.get_consultations(student_id=student_id)

                # Update progress
                progress_callback(80, "Processing results...")

                # Simulate a short delay for better UX
                import time
                time.sleep(0.5)

                # Update progress
                progress_callback(100, "Complete!")

                return consultations

            # Show loading dialog while fetching consultations
            self.consultations = LoadingDialog.show_loading(
                self,
                load_consultations,
                title="Refreshing Consultations",
                message="Loading your consultation history...",
                cancelable=True
            )

            # Update the table with the results
            self.update_consultation_table()

        except Exception as e:
            logger.error(f"Error refreshing consultations: {str(e)}")

            try:
                # Use notification manager if available
                from ..utils.notification import NotificationManager
                NotificationManager.show_message(
                    self,
                    "Error",
                    f"Failed to refresh consultation history: {str(e)}",
                    NotificationManager.ERROR
                )
            except ImportError:
                # Fallback to basic message box
                QMessageBox.warning(self, "Error", f"Failed to refresh consultation history: {str(e)}")

    def update_consultation_table(self):
        """
        Update the consultation table with the current consultations.
        """
        # Clear the table
        self.consultation_table.setRowCount(0)

        # Add consultations to the table
        for consultation in self.consultations:
            row_position = self.consultation_table.rowCount()
            self.consultation_table.insertRow(row_position)

            # Faculty name
            faculty_item = QTableWidgetItem(consultation.faculty.name)
            faculty_item.setData(Qt.UserRole, consultation.id) # Store consultation_id for MQTT updates
            self.consultation_table.setItem(row_position, 0, faculty_item)

            # Course code
            course_item = QTableWidgetItem(consultation.course_code if consultation.course_code else "N/A")
            self.consultation_table.setItem(row_position, 1, course_item)

            # Status with enhanced color coding and improved contrast
            status_item = QTableWidgetItem(consultation.status.value.capitalize())

            # Define status colors with gold and blue theme
            status_colors = {
                "pending": {
                    "bg": QColor(255, 248, 220),  # Light goldenrod background
                    "fg": QColor(184, 134, 11),   # Dark goldenrod text
                    "border": "#DAA520"           # Goldenrod border
                },
                "accepted": {
                    "bg": QColor(240, 248, 255),  # Very light blue background
                    "fg": QColor(34, 139, 34),    # Forest green text
                    "border": "#228B22"           # Green border for accepted
                },
                "busy": {
                    "bg": QColor(255, 245, 245),  # Very light red background  
                    "fg": QColor(220, 53, 69),    # Red text
                    "border": "#dc3545"           # Red border
                },
                "completed": {
                    "bg": QColor(230, 240, 255),  # Light blue background
                    "fg": QColor(65, 105, 225),   # Royal blue text
                    "border": "#4169E1"           # Royal blue border
                },
                "cancelled": {
                    "bg": QColor(255, 245, 245),  # Light red background
                    "fg": QColor(178, 134, 11),   # Dark goldenrod text
                    "border": "#B8860B"           # Dark goldenrod border
                }
            }

            # Apply the appropriate color scheme
            status_value = consultation.status.value
            if status_value in status_colors:
                colors = status_colors[status_value]
                status_item.setBackground(colors["bg"])
                status_item.setForeground(colors["fg"])

                # Apply custom styling with border for better definition
                status_item.setData(
                    Qt.UserRole,
                    f"border: 2px solid {colors['border']}; border-radius: 4px; padding: 4px;"
                )

            # Make text bold and slightly larger for better readability
            font = status_item.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            status_item.setFont(font)
            self.consultation_table.setItem(row_position, 2, status_item)

            # Date
            date_str = consultation.requested_at.strftime("%Y-%m-%d %H:%M")
            date_item = QTableWidgetItem(date_str)
            self.consultation_table.setItem(row_position, 3, date_item)

            # Actions
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(10, 8, 10, 8)  # Better margins for button centering
            actions_layout.setSpacing(12)  # Increased spacing between buttons

            # Add stretch before buttons for better centering
            actions_layout.addStretch()

            # View details button with improved sizing and centering
            view_button = QPushButton("View")
            view_button.setFixedSize(70, 40)  # Slightly larger for better touch interaction
            view_button.setStyleSheet("""
                QPushButton {
                    background-color: #4169E1; 
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 13pt;
                    font-weight: bold;
                    padding: 8px 12px;
                }
                QPushButton:hover {
                    background-color: #1E90FF;
                    transform: scale(1.02);
                }
                QPushButton:pressed {
                    background-color: #0066CC;
                    transform: scale(0.98);
                }
            """)
            # Use a better lambda that ignores the checked parameter
            view_button.clicked.connect(lambda _, c=consultation: self.view_consultation_details(c))
            actions_layout.addWidget(view_button)

            # Cancel button (only for pending consultations) with improved sizing and centering
            if consultation.status.value == "pending":
                cancel_button = QPushButton("Cancel")
                cancel_button.setObjectName(f"cancel_button_{consultation.id}") # Unique name for later access
                cancel_button.setFixedSize(80, 40)  # Slightly larger for better touch interaction
                cancel_button.setStyleSheet("""
                    QPushButton {
                        background-color: #DAA520; 
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 13pt;
                        font-weight: bold;
                        padding: 8px 12px;
                    }
                    QPushButton:hover {
                        background-color: #B8860B;
                        transform: scale(1.02);
                    }
                    QPushButton:pressed {
                        background-color: #996515;
                        transform: scale(0.98);
                    }
                """)
                # Use a better lambda that ignores the checked parameter
                cancel_button.clicked.connect(lambda _, c=consultation: self.cancel_consultation(c))
                actions_layout.addWidget(cancel_button)

            # Add stretch after buttons for perfect centering
            actions_layout.addStretch()

            # Set size policy for proper widget sizing with better height
            actions_cell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            actions_cell.setMinimumHeight(50)  # Increased minimum height for better button visibility

            self.consultation_table.setCellWidget(row_position, 4, actions_cell)

    def view_consultation_details(self, consultation):
        """
        Show consultation details in a dialog.
        """
        dialog = ConsultationDetailsDialog(consultation, self)
        dialog.exec_()

    def cancel_consultation(self, consultation):
        """
        Cancel a pending consultation with improved confirmation dialog.
        """
        try:
            # Try to use the notification manager for confirmation
            from ..utils.notification import NotificationManager

            # Show confirmation dialog
            if NotificationManager.show_confirmation(
                self,
                "Cancel Consultation",
                f"Are you sure you want to cancel your consultation request with {consultation.faculty.name}?",
                "Yes, Cancel",
                "No, Keep It"
            ):
                # Emit signal to cancel the consultation
                self.consultation_cancelled.emit(consultation.id)

        except ImportError:
            # Fallback to basic confirmation dialog
            reply = QMessageBox.question(
                self,
                "Cancel Consultation",
                f"Are you sure you want to cancel your consultation request with {consultation.faculty.name}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Emit signal to cancel the consultation
                self.consultation_cancelled.emit(consultation.id)


    # MQTT Update Handling Methods
    def _subscribe_to_consultation_updates(self):
        if not self.mqtt_service or not self.student:
            logger.error("MQTT service or student not available for subscription in ConsultationHistoryPanel.")
            return
        try:
            # Subscribe to updates for any consultation, will filter by student_id in handler
            topic = "consultease/consultations/+/status"
            self.mqtt_service.subscribe(topic, self._handle_mqtt_consultation_status_update)
            logger.info(f"ConsultationHistoryPanel for student {self.student.id} subscribed to {topic}")
        except Exception as e:
            logger.error(f"Error subscribing to consultation updates: {str(e)}")

    def _handle_mqtt_consultation_status_update(self, topic, payload_str):
        try:
            payload = json.loads(payload_str)
            logger.debug(f"MQTT Update Received in Panel: Topic='{topic}', Payload='{payload}'")

            mqtt_consultation_id = payload.get('consultation_id')
            new_status_str = payload.get('status')
            mqtt_student_id = payload.get('student_id')

            if not all([mqtt_consultation_id, new_status_str, mqtt_student_id]):
                logger.warning("Incomplete consultation update payload received via MQTT.")
                return

            if self.student and mqtt_student_id != self.student.id:
                logger.debug(f"MQTT update for consultation {mqtt_consultation_id} (student {mqtt_student_id}) ignored by panel for student {self.student.id}")
                return
            
            logger.info(f"Processing MQTT update for consultation {mqtt_consultation_id} for student {self.student.id}")

            for cons in self.consultations:
                if cons.id == mqtt_consultation_id:
                    cons.status = ConsultationStatus(new_status_str)
                    logger.debug(f"Updated local consultation list for {mqtt_consultation_id} to status {new_status_str}")
                    break

            for row in range(self.consultation_table.rowCount()):
                item = self.consultation_table.item(row, 0) 
                if item and item.data(Qt.UserRole) == mqtt_consultation_id:
                    status_item = self.consultation_table.item(row, 2)
                    if not status_item:
                        status_item = QTableWidgetItem()
                        self.consultation_table.setItem(row, 2, status_item)
                    status_item.setText(new_status_str.capitalize())
                    
                    status_colors = {
                        "pending": {"bg": QColor(255, 248, 220), "fg": QColor(184, 134, 11), "border": "#DAA520"},
                        "accepted": {"bg": QColor(240, 248, 255), "fg": QColor(34, 139, 34), "border": "#228B22"},
                        "busy": {"bg": QColor(255, 245, 245), "fg": QColor(220, 53, 69), "border": "#dc3545"},
                        "completed": {"bg": QColor(230, 240, 255), "fg": QColor(65, 105, 225), "border": "#4169E1"},
                        "cancelled": {"bg": QColor(255, 245, 245), "fg": QColor(178, 134, 11), "border": "#B8860B"}
                    }
                    if new_status_str in status_colors:
                        colors = status_colors[new_status_str]
                        status_item.setBackground(colors["bg"])
                        status_item.setForeground(colors["fg"])
                        status_item.setData(Qt.UserRole + 1, f"border: 2px solid {colors['border']}; border-radius: 4px; padding: 4px;") 
                        font = status_item.font()
                        font.setBold(True)
                        font.setPointSize(font.pointSize() + 1)
                        status_item.setFont(font)
                    else:
                        status_item.setBackground(QColor("white")) 
                        status_item.setForeground(QColor("black"))

                    actions_cell_widget = self.consultation_table.cellWidget(row, 4)
                    if actions_cell_widget:
                        cancel_btn = actions_cell_widget.findChild(QPushButton, f"cancel_button_{mqtt_consultation_id}")
                        if cancel_btn:
                            cancel_btn.setVisible(new_status_str == ConsultationStatus.PENDING.value)
                        else:
                            logger.warning(f"Could not find cancel button by name f'cancel_button_{mqtt_consultation_id}' for consultation {mqtt_consultation_id}")
                                        
                    logger.info(f"UI updated for consultation {mqtt_consultation_id} (row {row}) to status '{new_status_str}'.")
                    break 
            else:
                logger.debug(f"Consultation {mqtt_consultation_id} not found in table for UI update, or panel is for a different student.")

        except json.JSONDecodeError:
            logger.error("MQTT Update Error: Failed to decode JSON payload.")
        except Exception as e:
            logger.error(f"MQTT Update Error: {str(e)}", exc_info=True)

class ConsultationDetailsDialog(QDialog):
    """
    Dialog to display consultation details.
    """
    def __init__(self, consultation, parent=None):
        super().__init__(parent)
        self.consultation = consultation
        self.init_ui()

    def init_ui(self):
        """
        Initialize the dialog UI.
        """
        # Import theme system
        from ..utils.theme import ConsultEaseTheme

        self.setWindowTitle("Consultation Details")
        self.setMinimumWidth(700)  # Slightly wider for better content display
        self.setMinimumHeight(600)  # Slightly taller for better spacing
        self.setObjectName("consultation_details_dialog")

        # Apply theme-based stylesheet with gold and blue theme
        self.setStyleSheet('''
            QDialog#consultation_details_dialog {
                background-color: #ffffff;
                padding: 15px;
            }
            QLabel {
                font-size: 16pt;
                color: #333333;
                padding: 5px 0;
            }
            QLabel[heading="true"] {
                font-size: 22pt;
                font-weight: bold;
                color: #4169E1;
                margin-bottom: 15px;
                padding: 10px 0;
            }
            QFrame {
                border: 2px solid #DAA520;
                border-radius: 10px;
                background-color: #ffffff;
                padding: 25px;
                margin: 10px 0;
            }
            QPushButton {
                border-radius: 8px;
                padding: 15px 25px;
                font-size: 16pt;
                font-weight: bold;
                color: white;
                background-color: #4169E1;
                min-width: 120px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background-color: #0066CC;
                transform: scale(0.98);
            }
        ''')

        layout = QVBoxLayout(self)
        layout.setSpacing(20)  # Increased spacing between elements
        layout.setContentsMargins(20, 20, 20, 20)  # Better margins

        # Title
        title_label = QLabel("Consultation Details")
        title_label.setProperty("heading", "true")
        title_label.setAlignment(Qt.AlignCenter)  # Center the title
        layout.addWidget(title_label)

        # Details frame
        details_frame = QFrame()
        details_layout = QFormLayout(details_frame)
        details_layout.setSpacing(15)  # Increased spacing between form rows
        details_layout.setLabelAlignment(Qt.AlignRight)
        details_layout.setFormAlignment(Qt.AlignLeft)

        # Faculty
        faculty_label = QLabel("Faculty:")
        faculty_label.setStyleSheet("font-weight: bold; color: #DAA520;")
        faculty_value = QLabel(self.consultation.faculty.name)
        faculty_value.setStyleSheet("font-weight: bold; font-size: 17pt; color: #4169E1;")
        details_layout.addRow(faculty_label, faculty_value)

        # Department
        dept_label = QLabel("Department:")
        dept_label.setStyleSheet("font-weight: bold; color: #DAA520;")
        dept_value = QLabel(self.consultation.faculty.department)
        dept_value.setStyleSheet("font-size: 16pt; color: #333333;")
        details_layout.addRow(dept_label, dept_value)

        # Course
        course_label = QLabel("Course:")
        course_label.setStyleSheet("font-weight: bold; color: #DAA520;")
        course_value = QLabel(self.consultation.course_code if self.consultation.course_code else "N/A")
        course_value.setStyleSheet("font-size: 16pt; color: #333333;")
        details_layout.addRow(course_label, course_value)

        # Status with enhanced visual styling
        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold; color: #DAA520;")
        status_value = QLabel(self.consultation.status.value.capitalize())

        # Define status colors with gold and blue theme
        status_styles = {
            "pending": {
                "color": "#B8860B",                # Dark goldenrod text
                "background": "#FFF8DC",           # Cornsilk background
                "border": "2px solid #DAA520",     # Goldenrod border
                "padding": "10px 15px",
                "border-radius": "8px"
            },
            "accepted": {
                "color": "#228B22",                # Forest green text
                "background": "#f0f8ff",           # Very light blue background
                "border": "2px solid #228B22",     # Green border
                "padding": "10px 15px",
                "border-radius": "8px"
            },
            "busy": {
                "color": "#dc3545",                # Red text
                "background": "#fff5f5",           # Very light red background
                "border": "2px solid #dc3545",     # Red border
                "padding": "10px 15px",
                "border-radius": "8px"
            },
            "completed": {
                "color": "#4169E1",                # Royal blue text
                "background": "#E6F0FF",           # Light blue background
                "border": "2px solid #4169E1",     # Royal blue border
                "padding": "10px 15px",
                "border-radius": "8px"
            },
            "cancelled": {
                "color": "#B8860B",                # Dark goldenrod text
                "background": "#FFF8DC",           # Cornsilk background
                "border": "2px solid #B8860B",     # Dark goldenrod border
                "padding": "10px 15px",
                "border-radius": "8px"
            }
        }

        # Apply the appropriate style
        status_value.setStyleSheet(f"""
            font-weight: bold;
            font-size: 17pt;
            color: {status_styles.get(self.consultation.status.value, {}).get("color", "#212529")};
            background-color: {status_styles.get(self.consultation.status.value, {}).get("background", "#e9ecef")};
            border: {status_styles.get(self.consultation.status.value, {}).get("border", "2px solid #adb5bd")};
            padding: {status_styles.get(self.consultation.status.value, {}).get("padding", "10px 15px")};
            border-radius: {status_styles.get(self.consultation.status.value, {}).get("border-radius", "8px")};
        """)
        details_layout.addRow(status_label, status_value)

        # Requested date
        requested_label = QLabel("Requested:")
        requested_label.setStyleSheet("font-weight: bold; color: #495057;")
        requested_value = QLabel(self.consultation.requested_at.strftime("%Y-%m-%d %H:%M"))
        requested_value.setStyleSheet("font-size: 16pt; color: #343a40;")
        details_layout.addRow(requested_label, requested_value)

        # Accepted date (if applicable)
        if self.consultation.accepted_at:
            accepted_label = QLabel("Accepted:")
            accepted_label.setStyleSheet("font-weight: bold; color: #495057;")
            accepted_value = QLabel(self.consultation.accepted_at.strftime("%Y-%m-%d %H:%M"))
            accepted_value.setStyleSheet("font-size: 16pt; color: #28a745;")
            details_layout.addRow(accepted_label, accepted_value)

        # Busy date (if applicable)
        if self.consultation.busy_at:
            busy_label = QLabel("Marked Busy:")
            busy_label.setStyleSheet("font-weight: bold; color: #495057;")
            busy_value = QLabel(self.consultation.busy_at.strftime("%Y-%m-%d %H:%M"))
            busy_value.setStyleSheet("font-size: 16pt; color: #ffc107;")
            details_layout.addRow(busy_label, busy_value)

        # Completed date (if applicable)
        if self.consultation.completed_at:
            completed_label = QLabel("Completed:")
            completed_label.setStyleSheet("font-weight: bold; color: #495057;")
            completed_value = QLabel(self.consultation.completed_at.strftime("%Y-%m-%d %H:%M"))
            completed_value.setStyleSheet("font-size: 16pt; color: #007bff;")
            details_layout.addRow(completed_label, completed_value)

        layout.addWidget(details_frame)

        # Message section with better spacing
        message_label = QLabel("Consultation Details:")
        message_label.setProperty("heading", "true")
        layout.addWidget(message_label)

        message_frame = QFrame()
        message_layout = QVBoxLayout(message_frame)
        message_layout.setContentsMargins(20, 20, 20, 20)  # Better padding inside frame

        message_text = QLabel(self.consultation.request_message)
        message_text.setWordWrap(True)
        message_text.setStyleSheet("""
            font-size: 15pt;
            color: #495057;
            padding: 15px;
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            line-height: 1.5;
        """)
        message_layout.addWidget(message_text)

        layout.addWidget(message_frame)

        # Add some stretch to push the button to the bottom
        layout.addStretch()

        # Close button with better styling and spacing
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)  # Top margin for button separation
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

class ConsultationPanel(QTabWidget):
    """
    Main consultation panel with request form and history tabs.
    Improved with better transitions and user feedback.
    """
    consultation_requested = pyqtSignal(object, str, str)
    consultation_cancelled = pyqtSignal(int)

    def __init__(self, student=None, mqtt_service=None, parent=None):
        super().__init__(parent)
        self.student = student
        self.mqtt_service = mqtt_service # Store mqtt_service
        self.init_ui()

        # Set up auto-refresh timer for history panel
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_history)
        self.refresh_timer.start(60000)  # Refresh every minute

        # Connect tab change signal
        self.currentChanged.connect(self.on_tab_changed)

    def init_ui(self):
        """
        Initialize the consultation panel UI with improved styling and responsiveness.
        """
        # Import theme system
        from ..utils.theme import ConsultEaseTheme

        # Set object name for theme-based styling
        self.setObjectName("consultation_panel")

        # Create an enhanced stylesheet for the consultation panel
        enhanced_stylesheet = """
            QTabWidget#consultation_panel {
                background-color: #f8f9fa;
                border: none;
                padding: 0px;
                margin: 0px;
            }

            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 5px;
                position: relative;
                top: 0px;  /* Ensure stable positioning */
            }

            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px 20px;
                margin-right: 4px;
                font-size: 15pt;
                font-weight: bold;
                min-width: 200px;
                min-height: 20px;  /* Ensure consistent tab height */
                position: relative;  /* Prevent floating */
            }

            QTabBar::tab:selected {
                background-color: #228be6;
                color: white;
                border: 1px solid #1971c2;
                border-bottom: none;
                position: relative;  /* Maintain position when selected */
            }

            QTabBar::tab:hover:!selected {
                background-color: #dee2e6;
                transition: background-color 0.2s ease;  /* Smooth hover transition */
            }

            QTabWidget::tab-bar {
                alignment: center;
                position: fixed;  /* Prevent tab bar from moving */
            }
            
            /* Ensure stable layout during interactions */
            QTabBar {
                qproperty-drawBase: false;
                outline: 0;  /* Remove focus outline that can cause shifting */
            }
        """

        # Apply the enhanced stylesheet
        self.setStyleSheet(enhanced_stylesheet)

        # Request form tab with improved icon and text
        self.request_form = ConsultationRequestForm()
        self.request_form.request_submitted.connect(self.handle_consultation_request)
        self.addTab(self.request_form, "Request Consultation")

        # Set tab icon if available
        try:
            from PyQt5.QtGui import QIcon
            self.setTabIcon(0, QIcon("central_system/resources/icons/request.png"))
        except:
            # If icon not available, just use text
            pass

        # History tab with improved icon and text
        self.history_panel = ConsultationHistoryPanel(student=self.student, mqtt_service=self.mqtt_service)
        self.history_panel.consultation_cancelled.connect(self.handle_consultation_cancel)
        self.addTab(self.history_panel, "Consultation History")

        # Set tab icon if available
        try:
            from PyQt5.QtGui import QIcon
            self.setTabIcon(1, QIcon("central_system/resources/icons/history.png"))
        except:
            # If icon not available, just use text
            pass

        # Calculate responsive minimum size based on screen dimensions
        screen_width = QApplication.desktop().screenGeometry().width()
        screen_height = QApplication.desktop().screenGeometry().height()

        # Calculate responsive minimum size (smaller on small screens, larger on big screens)
        min_width = min(900, max(500, int(screen_width * 0.5)))
        min_height = min(700, max(400, int(screen_height * 0.6)))

        self.setMinimumSize(min_width, min_height)

        # Set size policy for better responsiveness
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add smooth transition animation for tab changes
        self.setTabPosition(QTabWidget.North)
        self.tabBar().setDrawBase(False)

    def set_student(self, student):
        """
        Set the student for the consultation panel.
        """
        self.student = student
        self.history_panel.set_student(student)

        # Update window title with student name
        if student and hasattr(self.parent(), 'setWindowTitle'):
            # Handle both student object and student data dictionary
            if isinstance(student, dict):
                student_name = student.get('name', 'Student')
            else:
                # Legacy support for student objects
                student_name = getattr(student, 'name', 'Student')
            self.parent().setWindowTitle(f"ConsultEase - {student_name}")

    def set_faculty(self, faculty):
        """
        Set the faculty for the consultation request.
        Fixed to prevent jarring tab shifting.
        """
        self.request_form.set_faculty(faculty)

        # Switch to request form tab smoothly without animation
        # Only animate if we're not already on the request tab
        if self.currentIndex() != 0:
            # Set tab directly for immediate, stable transition
            self.setCurrentIndex(0)
            
            # Optional: Add a very subtle visual feedback without movement
            try:
                from PyQt5.QtCore import QTimer
                from PyQt5.QtGui import QColor
                
                # Brief highlight effect on the tab without position changes
                def highlight_tab():
                    tab_bar = self.tabBar()
                    original_color = tab_bar.palette().color(tab_bar.foregroundRole())
                    
                    # Set a subtle highlight
                    tab_bar.setTabTextColor(0, QColor("#228be6"))
                    
                    # Reset after very brief moment
                    def reset_color():
                        tab_bar.setTabTextColor(0, original_color)
                    
                    QTimer.singleShot(150, reset_color)
                
                # Apply highlight after a tiny delay to ensure tab switch is complete
                QTimer.singleShot(50, highlight_tab)
                
            except Exception as e:
                # If any issues with highlight, just ignore
                logger.debug(f"Tab highlight effect skipped: {e}")
                pass

    def set_faculty_options(self, faculty_list):
        """
        Set the available faculty options in the dropdown.
        """
        self.request_form.set_faculty_options(faculty_list)

        # Update status message if no faculty available
        if not faculty_list:
            QMessageBox.information(
                self,
                "No Faculty Available",
                "There are no faculty members available at this time. Please try again later."
            )

    def handle_consultation_request(self, faculty, message, course_code):
        """
        Handle consultation request submission with improved feedback.
        """
        try:
            # Try to import notification manager
            try:
                from ..utils.notification import NotificationManager, LoadingDialog
                use_notification_manager = True
            except ImportError:
                use_notification_manager = False

            # Define the operation to run with progress updates
            def submit_request(progress_callback=None):
                if progress_callback:
                    progress_callback(20, "Submitting request...")

                # Emit signal to controller
                self.consultation_requested.emit(faculty, message, course_code)

                if progress_callback:
                    progress_callback(60, "Processing submission...")

                # Clear form fields
                self.request_form.message_input.clear()
                self.request_form.course_input.clear()

                if progress_callback:
                    progress_callback(80, "Refreshing history...")

                # Refresh history
                self.history_panel.refresh_consultations()

                if progress_callback:
                    progress_callback(100, "Complete!")

                return True

            # Use loading dialog if available
            if use_notification_manager:
                # Show loading dialog while submitting
                LoadingDialog.show_loading(
                    self,
                    submit_request,
                    title="Submitting Request",
                    message="Submitting your consultation request...",
                    cancelable=False
                )

                # Show success message
                NotificationManager.show_message(
                    self,
                    "Request Submitted",
                    f"Your consultation request with {faculty.name} has been submitted successfully.",
                    NotificationManager.SUCCESS
                )
            else:
                # Fallback to basic implementation
                submit_request()

                # Show success message
                QMessageBox.information(
                    self,
                    "Consultation Request Submitted",
                    f"Your consultation request with {faculty.name} has been submitted successfully."
                )

            # Animate transition to history tab
            self.animate_tab_change(1)

        except Exception as e:
            logger.error(f"Error submitting consultation request: {str(e)}")

            # Show error message
            try:
                from ..utils.notification import NotificationManager
                NotificationManager.show_message(
                    self,
                    "Submission Error",
                    f"Failed to submit consultation request: {str(e)}",
                    NotificationManager.ERROR
                )
            except ImportError:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to submit consultation request: {str(e)}"
                )

    def handle_consultation_cancel(self, consultation_id):
        """
        Handle consultation cancellation with improved feedback.
        """
        try:
            # Try to import notification manager
            try:
                from ..utils.notification import NotificationManager, LoadingDialog
                use_notification_manager = True
            except ImportError:
                use_notification_manager = False

            # Define the operation to run with progress updates
            def cancel_consultation(progress_callback=None):
                if progress_callback:
                    progress_callback(30, "Cancelling request...")

                # Emit signal to controller
                self.consultation_cancelled.emit(consultation_id)

                if progress_callback:
                    progress_callback(70, "Updating records...")

                # Refresh history
                self.history_panel.refresh_consultations()

                if progress_callback:
                    progress_callback(100, "Complete!")

                return True

            # Use loading dialog if available
            if use_notification_manager:
                # Show confirmation dialog first
                if NotificationManager.show_confirmation(
                    self,
                    "Cancel Consultation",
                    "Are you sure you want to cancel this consultation request?",
                    "Yes, Cancel",
                    "No, Keep It"
                ):
                    # Show loading dialog while cancelling
                    LoadingDialog.show_loading(
                        self,
                        cancel_consultation,
                        title="Cancelling Request",
                        message="Cancelling your consultation request...",
                        cancelable=False
                    )

                    # Show success message
                    NotificationManager.show_message(
                        self,
                        "Request Cancelled",
                        "Your consultation request has been cancelled successfully.",
                        NotificationManager.SUCCESS
                    )
            else:
                # Fallback to basic implementation
                reply = QMessageBox.question(
                    self,
                    "Cancel Consultation",
                    "Are you sure you want to cancel this consultation request?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # Cancel the consultation
                    cancel_consultation()

                    # Show success message
                    QMessageBox.information(
                        self,
                        "Consultation Cancelled",
                        "Your consultation request has been cancelled successfully."
                    )

        except Exception as e:
            logger.error(f"Error cancelling consultation: {str(e)}")

            # Show error message
            try:
                from ..utils.notification import NotificationManager
                NotificationManager.show_message(
                    self,
                    "Cancellation Error",
                    f"Failed to cancel consultation: {str(e)}",
                    NotificationManager.ERROR
                )
            except ImportError:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to cancel consultation: {str(e)}"
                )

    def animate_tab_change(self, tab_index):
        """
        Animate the transition to a different tab with enhanced visual effects.
        Fixed to prevent jarring tab shifting and ensure stable navigation.

        Args:
            tab_index (int): The index of the tab to switch to
        """
        # Immediately change to the target tab to prevent any shifting issues
        self.setCurrentIndex(tab_index)
        
        # Apply a simple, subtle visual feedback without complex animations
        try:
            current_tab_bar = self.tabBar()
            if current_tab_bar and tab_index < current_tab_bar.count():
                # Store original style
                original_style = current_tab_bar.styleSheet()
                
                # Create a very subtle highlight effect
                highlight_style = f"""
                    QTabBar::tab:selected {{
                        background-color: #e3f2fd;
                        border-bottom: 3px solid #228be6;
                    }}
                """
                
                # Apply highlight temporarily
                current_tab_bar.setStyleSheet(highlight_style)
                
                # Reset after a very short delay
                def reset_style():
                    try:
                        current_tab_bar.setStyleSheet(original_style)
                    except:
                        pass
                
                QTimer.singleShot(150, reset_style)  # Very brief highlight
                
        except Exception as e:
            # If any error occurs, just ensure the tab is changed without animation
            logger.debug(f"Tab animation fallback: {e}")
            self.setCurrentIndex(tab_index)

    def on_tab_changed(self, index):
        """
        Handle tab change events.

        Args:
            index (int): The index of the newly selected tab
        """
        # Refresh history when switching to history tab
        if index == 1:  # History tab
            self.history_panel.refresh_consultations()

    def auto_refresh_history(self):
        """
        Automatically refresh the history panel periodically.
        """
        # Only refresh if the history tab is visible
        if self.currentIndex() == 1:
            self.history_panel.refresh_consultations()

    def refresh_history(self):
        """
        Refresh the consultation history.
        """
        self.history_panel.refresh_consultations()
