from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame, QDialog, QFormLayout, QLineEdit,
                               QDialogButtonBox, QMessageBox, QComboBox, QCheckBox,
                               QGroupBox, QFileDialog, QTextEdit, QApplication, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QTextCursor

import os
import logging
from .base_window import BaseWindow
from ..controllers import FacultyController
from ..models import Student, get_db, Faculty
from ..services import get_rfid_service
from ..utils.input_sanitizer import (
    sanitize_string, sanitize_email, sanitize_filename, sanitize_path, sanitize_boolean
)

# Set up logging
logger = logging.getLogger(__name__)

class AdminDashboardWindow(BaseWindow):
    """
    Admin dashboard window with tabs for managing faculty, students, and system settings.
    """
    # Signals
    faculty_updated = pyqtSignal()
    student_updated = pyqtSignal()
    change_window = pyqtSignal(str, object)  # Add explicit signal if it's missing

    def __init__(self, admin=None, parent=None):
        self.admin = admin
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """
        Initialize the UI components.
        """
        # Set window title
        self.setWindowTitle("ConsultEase - Admin Dashboard")

        # Create a main container widget for the scroll area
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header with admin info and logout button
        header_layout = QHBoxLayout()

        # Admin welcome label
        admin_username = "Admin"
        if self.admin:
            # Handle admin as either an object or a dictionary
            if isinstance(self.admin, dict):
                admin_username = self.admin.get('username', 'Admin')
            else:
                admin_username = getattr(self.admin, 'username', 'Admin')

        admin_label = QLabel(f"Admin Dashboard - Logged in as: {admin_username}")
        admin_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(admin_label)

        # Logout button - smaller size
        logout_button = QPushButton("Logout")
        logout_button.setFixedSize(80, 30)
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)

        main_layout.addLayout(header_layout)

        # Tab widget for different admin functions
        self.tab_widget = QTabWidget()

        # Create tabs
        self.faculty_tab = FacultyManagementTab()
        self.faculty_tab.faculty_updated.connect(self.handle_faculty_updated)

        self.student_tab = StudentManagementTab()
        self.student_tab.student_updated.connect(self.handle_student_updated)

        self.system_tab = SystemMaintenanceTab()

        # Import and create system monitoring tab
        from .system_monitoring_widget import SystemMonitoringWidget
        self.monitoring_tab = SystemMonitoringWidget()

        # Add tabs to tab widget
        self.tab_widget.addTab(self.faculty_tab, "Faculty Management")
        self.tab_widget.addTab(self.student_tab, "Student Management")
        self.tab_widget.addTab(self.system_tab, "System Maintenance")
        self.tab_widget.addTab(self.monitoring_tab, "System Monitoring")

        main_layout.addWidget(self.tab_widget)

        # Create a scroll area and set its properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Allow the widget to resize
        scroll_area.setWidget(main_container)  # Set the main container as the scroll area's widget

        # Only show scrollbars when needed
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Style the scroll area with improved visibility and touch-friendliness
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 15px;  /* Increased width for better touch targets */
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #adb5bd;  /* Darker color for better visibility */
                min-height: 30px;  /* Increased minimum height for better touch targets */
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #868e96;  /* Even darker on hover */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Set the scroll area as the central widget
        self.setCentralWidget(scroll_area)

    def logout(self):
        """
        Handle logout button click with proper cleanup and form clearing.
        """
        logger.info("Admin logging out")

        # Clean up any resources
        try:
            # Clean up student tab resources
            if hasattr(self, 'student_tab') and self.student_tab:
                if hasattr(self.student_tab, 'cleanup'):
                    self.student_tab.cleanup()
                elif hasattr(self.student_tab, 'scan_dialog') and self.student_tab.scan_dialog:
                    self.student_tab.scan_dialog.close()
        except Exception as e:
            logger.error(f"Error during admin logout cleanup: {str(e)}")

        # Clear admin authentication state in the controller
        try:
            # Get the admin controller from the main application if available
            if hasattr(self.parent(), 'admin_controller'):
                self.parent().admin_controller.logout()
            
            # Clear login attempt tracking
            if hasattr(self.parent(), '_admin_login_attempts'):
                self.parent()._admin_login_attempts.clear()
                logger.debug("Cleared admin login attempt tracking on logout")
                
        except Exception as e:
            logger.error(f"Error clearing admin authentication state: {str(e)}")

        # Clear the admin login form if it exists
        try:
            if hasattr(self.parent(), 'admin_login_window') and self.parent().admin_login_window:
                self.parent().admin_login_window.clear_login_form()
                logger.debug("Cleared admin login form on logout")
        except Exception as e:
            logger.error(f"Error clearing admin login form: {str(e)}")

        # Hide this window
        self.hide()

        # Emit signal to change to the main login window (RFID scan) instead of admin login
        logger.info("Redirecting to main login window (RFID scan) after admin logout")
        self.change_window.emit("login", None)

    def handle_faculty_updated(self):
        """
        Handle faculty updated signal.
        """
        # Refresh faculty tab data
        self.faculty_tab.refresh_data()
        # Forward signal
        self.faculty_updated.emit()

    def handle_student_updated(self):
        """
        Handle student updated signal.
        """
        # Refresh student tab data
        self.student_tab.refresh_data()
        # Forward signal
        self.student_updated.emit()

class FacultyManagementTab(QWidget):
    """
    Tab for managing faculty members.
    """
    # Signals
    faculty_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.faculty_controller = FacultyController()

        # Set up auto-refresh timer for real-time updates
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

        # Track last data hash to avoid unnecessary UI updates
        self._last_data_hash = None

        # Loading state management
        self._is_loading = False
        self._loading_widget = None

        # Error state tracking
        self._last_error_time = None
        self._consecutive_errors = 0

        self.init_ui()

    def init_ui(self):
        """
        Initialize the UI components.
        """
        # Create a container widget for the scroll area
        container = QWidget()

        # Main layout
        main_layout = QVBoxLayout(container)

        # Buttons for actions with improved touch-friendly styling
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Better spacing between buttons

        # Common button style for touch-friendly interface
        button_style = """
            QPushButton {
                font-size: 14pt;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 8px;
                border: none;
                min-height: 44px;
                min-width: 120px;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:pressed {
                transform: scale(0.95);
            }
        """

        self.add_button = QPushButton("Add Faculty")
        self.add_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_button.clicked.connect(self.add_faculty)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Faculty")
        self.edit_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.edit_button.clicked.connect(self.edit_faculty)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Faculty")
        self.delete_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #F44336;
                color: white;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.delete_button.clicked.connect(self.delete_faculty)
        button_layout.addWidget(self.delete_button)

        # Add beacon management button
        self.beacon_button = QPushButton("Beacon Management")
        self.beacon_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #FF9800;
                color: white;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.beacon_button.clicked.connect(self.open_beacon_management)
        button_layout.addWidget(self.beacon_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #9E9E9E;
                color: white;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Faculty table with improved touch-friendly styling
        self.faculty_table = QTableWidget()
        self.faculty_table.setColumnCount(7)
        self.faculty_table.setHorizontalHeaderLabels(["ID", "Name", "Department", "Email", "BLE ID", "Status", "Always Available"])
        self.faculty_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.faculty_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.faculty_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.faculty_table.setSelectionMode(QTableWidget.SingleSelection)

        # Improve table styling for touch interface
        self.faculty_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #3498db;
                font-size: 12pt;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #eee;
                min-height: 40px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
                font-size: 12pt;
                min-height: 44px;
            }
            QHeaderView::section:hover {
                background-color: #2c3e50;
            }
        """)

        # Enable alternating row colors for better readability
        self.faculty_table.setAlternatingRowColors(True)

        main_layout.addWidget(self.faculty_table)

        # Add some spacing at the bottom for better appearance
        main_layout.addSpacing(10)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)

        # Only show scrollbars when needed
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Style the scroll area with improved visibility and touch-friendliness
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 15px;  /* Increased width for better touch targets */
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #adb5bd;  /* Darker color for better visibility */
                min-height: 30px;  /* Increased minimum height for better touch targets */
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background: #868e96;  /* Even darker on hover */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Create a layout for the tab and add the scroll area
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        # Initial data load
        self.refresh_data()

    def refresh_data(self):
        """
        Refresh the faculty data in the table with optimized updates.
        Only updates the UI if data has actually changed.
        """
        try:
            # Show loading indicator for initial load
            if self._last_data_hash is None:
                self._show_loading_indicator()

            # Get all faculty from the controller
            faculties = self.faculty_controller.get_all_faculty()

            # Reset error tracking on successful data fetch
            self._consecutive_errors = 0
            self._last_error_time = None

            # Create a hash of the current data to check for changes
            import hashlib
            faculty_data_str = str([(f.id, f.name, f.department, f.email, f.ble_id, f.status, f.always_available) for f in faculties])
            current_hash = hashlib.md5(faculty_data_str.encode()).hexdigest()

            # Only update UI if data has changed
            if current_hash == self._last_data_hash:
                self._hide_loading_indicator()
                return

            self._last_data_hash = current_hash

            # Hide loading indicator before updating table
            self._hide_loading_indicator()

            # Temporarily disable updates for better performance
            self.faculty_table.setUpdatesEnabled(False)

            # Clear the table
            self.faculty_table.setRowCount(0)

            for faculty in faculties:
                row_position = self.faculty_table.rowCount()
                self.faculty_table.insertRow(row_position)

                # Add data to each column
                self.faculty_table.setItem(row_position, 0, QTableWidgetItem(str(faculty.id)))
                self.faculty_table.setItem(row_position, 1, QTableWidgetItem(faculty.name))
                self.faculty_table.setItem(row_position, 2, QTableWidgetItem(faculty.department))
                self.faculty_table.setItem(row_position, 3, QTableWidgetItem(faculty.email))
                self.faculty_table.setItem(row_position, 4, QTableWidgetItem(faculty.ble_id or ""))

                status_item = QTableWidgetItem("Available" if faculty.status else "Unavailable")
                if faculty.status:
                    status_item.setBackground(Qt.green)
                else:
                    status_item.setBackground(Qt.red)
                self.faculty_table.setItem(row_position, 5, status_item)

                # Add always available status
                always_available_item = QTableWidgetItem("Yes" if faculty.always_available else "No")
                if faculty.always_available:
                    always_available_item.setBackground(Qt.green)
                self.faculty_table.setItem(row_position, 6, always_available_item)

            # Re-enable updates
            self.faculty_table.setUpdatesEnabled(True)

            # Show empty state message if no faculty
            if len(faculties) == 0:
                self._show_empty_faculty_table_message()

            logger.debug(f"Faculty table refreshed with {len(faculties)} entries")

        except Exception as e:
            logger.error(f"Error refreshing faculty data: {str(e)}")

            # Hide loading indicator on error
            self._hide_loading_indicator()

            # Track consecutive errors
            import time
            self._consecutive_errors += 1
            self._last_error_time = time.time()

            # Show error in table if this is a persistent issue
            if self._consecutive_errors >= 3:
                self._show_error_in_table(f"Error loading faculty data: {str(e)}")

            # Only show warning for serious errors, not during normal auto-refresh
            if self._consecutive_errors == 1:  # Only show on first error
                if "Connection refused" in str(e) or "Database error" in str(e):
                    QMessageBox.warning(self, "Data Error", f"Failed to refresh faculty data: {str(e)}")

            # Slow down refresh rate if we're having persistent errors
            if self._consecutive_errors >= 5:
                self.refresh_timer.setInterval(60000)  # Slow down to 1 minute
                logger.warning("Slowing down refresh rate due to persistent errors")

    def _show_empty_faculty_table_message(self):
        """
        Show a message in the table when no faculty members exist.
        """
        # Add a single row with a message spanning all columns
        self.faculty_table.insertRow(0)

        # Create a message item
        message_item = QTableWidgetItem("No faculty members found. Click 'Add Faculty' to add the first faculty member.")
        message_item.setTextAlignment(Qt.AlignCenter)
        message_item.setFlags(Qt.ItemIsEnabled)  # Make it non-selectable

        # Style the message
        from PyQt5.QtGui import QFont, QColor
        font = QFont()
        font.setItalic(True)
        font.setPointSize(14)
        message_item.setFont(font)
        message_item.setForeground(QColor("#666"))

        # Set the item in the first column and span all columns
        self.faculty_table.setItem(0, 0, message_item)
        self.faculty_table.setSpan(0, 0, 1, 7)  # Span all 7 columns

    def _show_loading_indicator(self):
        """
        Show a loading indicator in the faculty table.
        """
        if self._is_loading:
            return  # Already showing loading indicator

        self._is_loading = True
        logger.debug("Showing loading indicator in faculty table")

        # Clear table first
        self.faculty_table.setRowCount(0)

        # Add loading row
        self.faculty_table.insertRow(0)

        # Create loading message
        loading_item = QTableWidgetItem("Loading faculty data...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        loading_item.setFlags(Qt.ItemIsEnabled)  # Make it non-selectable

        # Style the loading message
        from PyQt5.QtGui import QFont, QColor
        font = QFont()
        font.setItalic(True)
        font.setPointSize(12)
        loading_item.setFont(font)
        loading_item.setForeground(QColor("#3498db"))

        # Set the item and span all columns
        self.faculty_table.setItem(0, 0, loading_item)
        self.faculty_table.setSpan(0, 0, 1, 7)

    def _hide_loading_indicator(self):
        """
        Hide the loading indicator.
        """
        if not self._is_loading:
            return

        logger.debug("Hiding loading indicator")
        self._is_loading = False
        # The table will be populated with actual data after this

    def _show_error_in_table(self, error_message):
        """
        Show an error message in the faculty table.

        Args:
            error_message (str): Error message to display
        """
        logger.info(f"Showing error in faculty table: {error_message}")

        # Clear table first
        self.faculty_table.setRowCount(0)

        # Add error row
        self.faculty_table.insertRow(0)

        # Create error message
        error_item = QTableWidgetItem(f"⚠️ {error_message}")
        error_item.setTextAlignment(Qt.AlignCenter)
        error_item.setFlags(Qt.ItemIsEnabled)  # Make it non-selectable

        # Style the error message
        from PyQt5.QtGui import QFont, QColor
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        error_item.setFont(font)
        error_item.setForeground(QColor("#e74c3c"))

        # Set the item and span all columns
        self.faculty_table.setItem(0, 0, error_item)
        self.faculty_table.setSpan(0, 0, 1, 7)

    def handle_faculty_updated(self):
        """
        Handle faculty data updated event from main application.
        This ensures real-time synchronization between admin and student dashboards.
        """
        logger.info("Admin dashboard received faculty update notification")
        try:
            # Force immediate refresh of faculty data
            self.refresh_data()
            logger.debug("Admin dashboard faculty data refreshed successfully")
        except Exception as e:
            logger.error(f"Error handling faculty update in admin dashboard: {e}")

    def add_faculty(self):
        """
        Show dialog to add a new faculty member.
        """
        dialog = FacultyDialog(parent=self)

        # Ensure dialog appears on top
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        if dialog.exec_() == QDialog.Accepted:
            try:
                # Sanitize inputs
                name = sanitize_string(dialog.name_input.text(), max_length=100)
                department = sanitize_string(dialog.department_input.text(), max_length=100)
                email = sanitize_email(dialog.email_input.text())
                ble_id = sanitize_string(dialog.ble_id_input.text(), max_length=50)
                image_path = dialog.image_path

                # Validate inputs
                if not name:
                    raise ValueError("Faculty name cannot be empty")

                if not department:
                    raise ValueError("Department cannot be empty")

                if not email:
                    raise ValueError("Email is required and must be valid")

                # Validate name and email using Faculty model validation
                if not Faculty.validate_name(name):
                    raise ValueError("Invalid faculty name format")

                if not Faculty.validate_email(email):
                    raise ValueError("Invalid email format")

                if ble_id and not Faculty.validate_ble_id(ble_id):
                    raise ValueError("Invalid BLE ID format")

                # Process image if provided
                if image_path:
                    # Get the filename only
                    import os
                    import shutil

                    # Create images directory if it doesn't exist
                    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    images_dir = os.path.join(base_dir, 'images', 'faculty')
                    if not os.path.exists(images_dir):
                        os.makedirs(images_dir)

                    # Sanitize and generate a unique filename
                    safe_email_prefix = sanitize_filename(email.split('@')[0])
                    safe_basename = sanitize_filename(os.path.basename(image_path))
                    filename = f"{safe_email_prefix}_{safe_basename}"

                    # Ensure the destination path is safe
                    dest_path = sanitize_path(os.path.join(images_dir, filename), base_dir)

                    # Copy the image file
                    shutil.copy2(image_path, dest_path)

                    # Store the relative path
                    image_path = filename
                else:
                    image_path = None

                # Get always available flag
                always_available = sanitize_boolean(dialog.always_available_checkbox.isChecked())

                # Add faculty using controller
                faculty, errors = self.faculty_controller.add_faculty(name, department, email, ble_id, image_path, always_available)

                if faculty and not errors:
                    QMessageBox.information(self, "Add Faculty", f"Faculty '{name}' added successfully.")
                    # Force immediate refresh to show changes
                    self._last_data_hash = None  # Force refresh
                    self.refresh_data()
                    self.faculty_updated.emit()
                else:
                    error_msg = "Failed to add faculty."
                    if errors:
                        error_msg += f" Errors: {'; '.join(errors)}"
                    else:
                        error_msg += " This email or BLE ID may already be in use."
                    QMessageBox.warning(self, "Add Faculty", error_msg)

            except ValueError as e:
                logger.error(f"Validation error adding faculty: {str(e)}")
                QMessageBox.warning(self, "Input Error", str(e))
            except Exception as e:
                logger.error(f"Error adding faculty: {str(e)}")
                QMessageBox.warning(self, "Add Faculty", f"Error adding faculty: {str(e)}")

    def edit_faculty(self):
        """
        Show dialog to edit the selected faculty member.
        """
        # Get selected row
        selected_rows = self.faculty_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Edit Faculty", "Please select a faculty member to edit.")
            return

        # Get faculty ID from the first column
        row_index = selected_rows[0].row()
        faculty_id = int(self.faculty_table.item(row_index, 0).text())

        # Get faculty from controller
        faculty = self.faculty_controller.get_faculty_by_id(faculty_id)
        if not faculty:
            QMessageBox.warning(self, "Edit Faculty", f"Faculty with ID {faculty_id} not found.")
            return

        # Create and populate dialog with this tab as parent
        dialog = FacultyDialog(faculty_id=faculty_id, parent=self)
        dialog.name_input.setText(faculty.name)
        dialog.department_input.setText(faculty.department)
        dialog.email_input.setText(faculty.email)
        dialog.ble_id_input.setText(faculty.ble_id)
        dialog.always_available_checkbox.setChecked(faculty.always_available)

        # Set image path if available
        if faculty.image_path:
            dialog.image_path = faculty.get_image_path()
            dialog.image_path_input.setText(faculty.image_path)

        # Ensure dialog appears on top
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        if dialog.exec_() == QDialog.Accepted:
            try:
                name = dialog.name_input.text().strip()
                department = dialog.department_input.text().strip()
                email = dialog.email_input.text().strip()
                ble_id = dialog.ble_id_input.text().strip()
                image_path = dialog.image_path

                # Process image if provided and different from current
                if image_path and (not faculty.image_path or image_path != faculty.get_image_path()):
                    # Get the filename only
                    import os
                    import shutil

                    # Create images directory if it doesn't exist
                    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    images_dir = os.path.join(base_dir, 'images', 'faculty')
                    if not os.path.exists(images_dir):
                        os.makedirs(images_dir)

                    # Generate a unique filename
                    filename = f"{email.split('@')[0]}_{os.path.basename(image_path)}"
                    dest_path = os.path.join(images_dir, filename)

                    # Copy the image file
                    shutil.copy2(image_path, dest_path)

                    # Store the relative path
                    image_path = filename
                elif faculty.image_path:
                    # Keep the existing image path
                    image_path = faculty.image_path

                # Get always available flag
                always_available = dialog.always_available_checkbox.isChecked()

                # Update faculty using controller
                updated_faculty = self.faculty_controller.update_faculty(
                    faculty_id, name, department, email, ble_id, image_path, always_available
                )

                if updated_faculty:
                    QMessageBox.information(self, "Edit Faculty", f"Faculty '{name}' updated successfully.")
                    # Force immediate refresh to show changes
                    self._last_data_hash = None  # Force refresh
                    self.refresh_data()
                    self.faculty_updated.emit()
                else:
                    QMessageBox.warning(self, "Edit Faculty", "Failed to update faculty. This email or BLE ID may already be in use.")

            except Exception as e:
                logger.error(f"Error updating faculty: {str(e)}")
                QMessageBox.warning(self, "Edit Faculty", f"Error updating faculty: {str(e)}")

    def delete_faculty(self):
        """
        Delete the selected faculty member.
        """
        # Get selected row
        selected_rows = self.faculty_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Delete Faculty", "Please select a faculty member to delete.")
            return

        # Get faculty ID and name from the table
        row_index = selected_rows[0].row()
        faculty_id = int(self.faculty_table.item(row_index, 0).text())
        faculty_name = self.faculty_table.item(row_index, 1).text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Faculty",
            f"Are you sure you want to delete faculty member '{faculty_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Delete faculty using controller
                success = self.faculty_controller.delete_faculty(faculty_id)

                if success:
                    QMessageBox.information(self, "Delete Faculty", f"Faculty '{faculty_name}' deleted successfully.")
                    # Force immediate refresh to show changes
                    self._last_data_hash = None  # Force refresh
                    self.refresh_data()
                    self.faculty_updated.emit()
                else:
                    QMessageBox.warning(self, "Delete Faculty", f"Failed to delete faculty '{faculty_name}'.")

            except Exception as e:
                logger.error(f"Error deleting faculty: {str(e)}")
                QMessageBox.warning(self, "Delete Faculty", f"Error deleting faculty: {str(e)}")

    def open_beacon_management(self):
        """
        Open the beacon management dialog.
        """
        try:
            dialog = BeaconManagementDialog(parent=self)
            dialog.exec_()
            # Refresh data after beacon management in case BLE IDs were updated
            self.refresh_data()
            self.faculty_updated.emit()
        except Exception as e:
            logger.error(f"Error opening beacon management: {str(e)}")
            QMessageBox.critical(self, "Beacon Management Error", f"Error opening beacon management: {str(e)}")

class BeaconManagementDialog(QDialog):
    """
    Dialog for managing nRF51822 beacon configuration and faculty assignments.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.faculty_controller = FacultyController()
        self.beacon_config = {}
        self.setWindowTitle("nRF51822 Beacon Management")
        self.setModal(True)
        self.resize(800, 600)
        self.init_ui()
        self.load_faculty_data()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Title and description
        title_label = QLabel("nRF51822 Beacon Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        description_label = QLabel(
            "Configure nRF51822 BLE beacons for faculty presence detection. "
            "Each beacon should be assigned to a specific faculty member."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("margin-bottom: 15px; color: #666;")
        layout.addWidget(description_label)

        # Create tab widget for different beacon management functions
        self.tab_widget = QTabWidget()

        # Beacon Discovery Tab
        self.discovery_tab = BeaconDiscoveryTab(self)
        self.tab_widget.addTab(self.discovery_tab, "Beacon Discovery")

        # Faculty Assignment Tab
        self.assignment_tab = BeaconAssignmentTab(self)
        self.tab_widget.addTab(self.assignment_tab, "Faculty Assignment")

        # ESP32 Configuration Tab
        self.config_tab = ESP32ConfigurationTab(self)
        self.tab_widget.addTab(self.config_tab, "ESP32 Configuration")

        # Testing Tab
        self.testing_tab = BeaconTestingTab(self)
        self.tab_widget.addTab(self.testing_tab, "Testing & Monitoring")

        layout.addWidget(self.tab_widget)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def load_faculty_data(self):
        """Load faculty data for beacon assignment."""
        try:
            faculty_list = self.faculty_controller.get_all_faculty()
            # Pass faculty data to tabs that need it
            self.assignment_tab.set_faculty_data(faculty_list)
            self.config_tab.set_faculty_data(faculty_list)
        except Exception as e:
            logger.error(f"Error loading faculty data: {str(e)}")
            QMessageBox.warning(self, "Data Error", f"Failed to load faculty data: {str(e)}")

class BeaconDiscoveryTab(QWidget):
    """Tab for discovering nRF51822 beacon MAC addresses."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.discovered_beacons = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Follow these steps to discover your nRF51822 beacon MAC addresses:\n\n"
            "1. Power on ONE beacon at a time\n"
            "2. Use a BLE scanner app (nRF Connect, BLE Scanner, LightBlue)\n"
            "3. Find your beacon in the scanner (may appear as 'nRF51822' or custom name)\n"
            "4. Record the MAC address below\n"
            "5. Repeat for all 5 beacons"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        layout.addWidget(instructions)

        # Beacon entry section
        beacon_group = QGroupBox("Discovered Beacons")
        beacon_layout = QVBoxLayout()

        # Create 5 beacon entry rows
        self.beacon_entries = []
        for i in range(5):
            beacon_row = QHBoxLayout()

            label = QLabel(f"Beacon #{i+1}:")
            label.setMinimumWidth(80)
            beacon_row.addWidget(label)

            mac_input = QLineEdit()
            mac_input.setPlaceholderText("XX:XX:XX:XX:XX:XX")
            mac_input.textChanged.connect(lambda text, idx=i: self.validate_mac_input(text, idx))
            beacon_row.addWidget(mac_input)

            status_label = QLabel("Not configured")
            status_label.setStyleSheet("color: #666;")
            status_label.setMinimumWidth(100)
            beacon_row.addWidget(status_label)

            self.beacon_entries.append({
                'mac_input': mac_input,
                'status_label': status_label
            })

            beacon_layout.addLayout(beacon_row)

        beacon_group.setLayout(beacon_layout)
        layout.addWidget(beacon_group)

        # Action buttons
        button_layout = QHBoxLayout()

        validate_button = QPushButton("Validate All MAC Addresses")
        validate_button.clicked.connect(self.validate_all_macs)
        button_layout.addWidget(validate_button)

        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_beacon_config)
        button_layout.addWidget(save_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("Status messages will appear here...")
        layout.addWidget(self.status_text)

    def validate_mac_input(self, text, index):
        """Validate MAC address input in real-time."""
        import re
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'

        entry = self.beacon_entries[index]
        if text and re.match(mac_pattern, text):
            entry['status_label'].setText("Valid")
            entry['status_label'].setStyleSheet("color: green;")
            entry['mac_input'].setStyleSheet("border: 2px solid green;")
        elif text:
            entry['status_label'].setText("Invalid format")
            entry['status_label'].setStyleSheet("color: red;")
            entry['mac_input'].setStyleSheet("border: 2px solid red;")
        else:
            entry['status_label'].setText("Not configured")
            entry['status_label'].setStyleSheet("color: #666;")
            entry['mac_input'].setStyleSheet("")

    def validate_all_macs(self):
        """Validate all MAC addresses and check for duplicates."""
        mac_addresses = []
        valid_count = 0

        for i, entry in enumerate(self.beacon_entries):
            mac = entry['mac_input'].text().strip().upper()
            if mac:
                if self.is_valid_mac(mac):
                    if mac in mac_addresses:
                        entry['status_label'].setText("Duplicate!")
                        entry['status_label'].setStyleSheet("color: red;")
                        entry['mac_input'].setStyleSheet("border: 2px solid red;")
                    else:
                        mac_addresses.append(mac)
                        valid_count += 1
                        entry['status_label'].setText("Valid")
                        entry['status_label'].setStyleSheet("color: green;")
                        entry['mac_input'].setStyleSheet("border: 2px solid green;")
                else:
                    entry['status_label'].setText("Invalid format")
                    entry['status_label'].setStyleSheet("color: red;")
                    entry['mac_input'].setStyleSheet("border: 2px solid red;")

        self.log_status(f"Validation complete: {valid_count} valid MAC addresses found")
        if valid_count == 5:
            self.log_status("✓ All 5 beacons configured with valid MAC addresses!")
        elif valid_count > 0:
            self.log_status(f"⚠ {5 - valid_count} beacons still need configuration")

    def is_valid_mac(self, mac):
        """Check if MAC address format is valid."""
        import re
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac))

    def save_beacon_config(self):
        """Save the beacon configuration."""
        try:
            config = {}
            valid_beacons = 0

            for i, entry in enumerate(self.beacon_entries):
                mac = entry['mac_input'].text().strip().upper()
                if mac and self.is_valid_mac(mac):
                    config[f'beacon_{i+1}'] = {
                        'mac_address': mac,
                        'beacon_number': i + 1
                    }
                    valid_beacons += 1

            if valid_beacons == 0:
                QMessageBox.warning(self, "Save Error", "No valid beacon MAC addresses to save.")
                return

            # Save to parent dialog
            if hasattr(self.parent(), 'beacon_config'):
                self.parent().beacon_config = config
                self.log_status(f"✓ Saved configuration for {valid_beacons} beacons")
                QMessageBox.information(self, "Configuration Saved",
                                      f"Successfully saved configuration for {valid_beacons} beacons.")

        except Exception as e:
            logger.error(f"Error saving beacon configuration: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Error saving configuration: {str(e)}")

    def log_status(self, message):
        """Add a status message to the status text area."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")

class BeaconAssignmentTab(QWidget):
    """Tab for assigning beacons to faculty members."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.faculty_data = []
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Assign discovered beacons to faculty members. Each beacon should be assigned to exactly one faculty member."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        layout.addWidget(instructions)

        # Assignment table
        self.assignment_table = QTableWidget()
        self.assignment_table.setColumnCount(4)
        self.assignment_table.setHorizontalHeaderLabels(["Beacon #", "MAC Address", "Faculty Member", "Action"])
        self.assignment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.assignment_table)

        # Action buttons
        button_layout = QHBoxLayout()

        refresh_button = QPushButton("Refresh Beacon Data")
        refresh_button.clicked.connect(self.refresh_beacon_data)
        button_layout.addWidget(refresh_button)

        assign_button = QPushButton("Auto-Assign to Faculty")
        assign_button.clicked.connect(self.auto_assign_faculty)
        button_layout.addWidget(assign_button)

        save_button = QPushButton("Save Assignments")
        save_button.clicked.connect(self.save_assignments)
        button_layout.addWidget(save_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def set_faculty_data(self, faculty_list):
        """Set the faculty data for assignment."""
        self.faculty_data = faculty_list
        self.refresh_assignment_table()

    def refresh_beacon_data(self):
        """Refresh beacon data from discovery tab."""
        if hasattr(self.parent(), 'beacon_config'):
            self.refresh_assignment_table()
        else:
            QMessageBox.information(self, "No Beacon Data",
                                  "Please discover beacon MAC addresses first in the Beacon Discovery tab.")

    def refresh_assignment_table(self):
        """Refresh the assignment table with current data."""
        self.assignment_table.setRowCount(0)

        if not hasattr(self.parent(), 'beacon_config'):
            return

        beacon_config = self.parent().beacon_config

        for beacon_key, beacon_info in beacon_config.items():
            row = self.assignment_table.rowCount()
            self.assignment_table.insertRow(row)

            # Beacon number
            self.assignment_table.setItem(row, 0, QTableWidgetItem(str(beacon_info['beacon_number'])))

            # MAC address
            self.assignment_table.setItem(row, 1, QTableWidgetItem(beacon_info['mac_address']))

            # Faculty dropdown
            faculty_combo = QComboBox()
            faculty_combo.addItem("-- Select Faculty --", None)
            for faculty in self.faculty_data:
                faculty_combo.addItem(f"{faculty.name} (ID: {faculty.id})", faculty.id)

            self.assignment_table.setCellWidget(row, 2, faculty_combo)

            # Action button
            assign_button = QPushButton("Assign")
            assign_button.clicked.connect(lambda checked, r=row: self.assign_beacon_to_faculty(r))
            self.assignment_table.setCellWidget(row, 3, assign_button)

    def auto_assign_faculty(self):
        """Automatically assign beacons to faculty in order."""
        if not self.faculty_data:
            QMessageBox.warning(self, "No Faculty Data", "No faculty members available for assignment.")
            return

        for row in range(self.assignment_table.rowCount()):
            if row < len(self.faculty_data):
                faculty_combo = self.assignment_table.cellWidget(row, 2)
                if faculty_combo:
                    # Set to faculty member (index 1 because index 0 is "-- Select Faculty --")
                    faculty_combo.setCurrentIndex(row + 1)

        QMessageBox.information(self, "Auto-Assignment",
                              f"Automatically assigned {min(self.assignment_table.rowCount(), len(self.faculty_data))} beacons to faculty members.")

    def assign_beacon_to_faculty(self, row):
        """Assign a specific beacon to the selected faculty member."""
        faculty_combo = self.assignment_table.cellWidget(row, 2)
        if not faculty_combo or faculty_combo.currentData() is None:
            QMessageBox.warning(self, "Assignment Error", "Please select a faculty member first.")
            return

        faculty_id = faculty_combo.currentData()
        mac_address = self.assignment_table.item(row, 1).text()

        # Update faculty BLE ID in database
        try:
            from ..controllers.faculty_controller import FacultyController
            faculty_controller = FacultyController()

            # Get faculty object
            faculty = faculty_controller.get_faculty_by_id(faculty_id)
            if faculty:
                # Update BLE ID
                success = faculty_controller.update_faculty_ble_id(faculty_id, mac_address)
                if success:
                    QMessageBox.information(self, "Assignment Success",
                                          f"Successfully assigned beacon {mac_address} to {faculty.name}")
                else:
                    QMessageBox.warning(self, "Assignment Error", "Failed to update faculty BLE ID in database.")
            else:
                QMessageBox.warning(self, "Assignment Error", f"Faculty with ID {faculty_id} not found.")

        except Exception as e:
            logger.error(f"Error assigning beacon to faculty: {str(e)}")
            QMessageBox.critical(self, "Assignment Error", f"Error assigning beacon: {str(e)}")

    def save_assignments(self):
        """Save all beacon assignments to the database."""
        try:
            assignments_made = 0
            errors = []

            from ..controllers.faculty_controller import FacultyController
            faculty_controller = FacultyController()

            for row in range(self.assignment_table.rowCount()):
                faculty_combo = self.assignment_table.cellWidget(row, 2)
                if faculty_combo and faculty_combo.currentData() is not None:
                    faculty_id = faculty_combo.currentData()
                    mac_address = self.assignment_table.item(row, 1).text()

                    try:
                        success = faculty_controller.update_faculty_ble_id(faculty_id, mac_address)
                        if success:
                            assignments_made += 1
                        else:
                            errors.append(f"Failed to assign beacon {mac_address}")
                    except Exception as e:
                        errors.append(f"Error assigning beacon {mac_address}: {str(e)}")

            if assignments_made > 0:
                QMessageBox.information(self, "Assignments Saved",
                                      f"Successfully saved {assignments_made} beacon assignments.")

            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.warning(self, "Assignment Errors", f"Some assignments failed:\n{error_msg}")

        except Exception as e:
            logger.error(f"Error saving beacon assignments: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Error saving assignments: {str(e)}")

class ESP32ConfigurationTab(QWidget):
    """Tab for generating ESP32 configuration files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.faculty_data = []
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Generate ESP32 configuration files for each faculty desk unit. "
            "Each unit will be configured with the appropriate faculty ID and all beacon MAC addresses."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        layout.addWidget(instructions)

        # Configuration preview
        config_group = QGroupBox("Configuration Preview")
        config_layout = QVBoxLayout()

        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setMaximumHeight(300)
        self.config_text.setPlaceholderText("Configuration preview will appear here...")
        config_layout.addWidget(self.config_text)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Action buttons
        button_layout = QHBoxLayout()

        generate_button = QPushButton("Generate All Configurations")
        generate_button.clicked.connect(self.generate_all_configs)
        button_layout.addWidget(generate_button)

        preview_button = QPushButton("Preview Configuration")
        preview_button.clicked.connect(self.preview_configuration)
        button_layout.addWidget(preview_button)

        export_button = QPushButton("Export to Files")
        export_button.clicked.connect(self.export_configurations)
        button_layout.addWidget(export_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Status area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("Status messages will appear here...")
        layout.addWidget(self.status_text)

    def set_faculty_data(self, faculty_list):
        """Set the faculty data for configuration generation."""
        self.faculty_data = faculty_list

    def generate_all_configs(self):
        """Generate configurations for all faculty desk units."""
        if not self.faculty_data:
            QMessageBox.warning(self, "No Faculty Data", "No faculty members available for configuration generation.")
            return

        if not hasattr(self.parent(), 'beacon_config') or not self.parent().beacon_config:
            QMessageBox.warning(self, "No Beacon Data", "Please configure beacon MAC addresses first.")
            return

        try:
            beacon_config = self.parent().beacon_config
            configurations = {}

            for i, faculty in enumerate(self.faculty_data[:5]):  # Limit to 5 units
                config = self.generate_faculty_config(faculty, beacon_config, i + 1)
                configurations[f"unit_{i+1}_{faculty.name.replace(' ', '_')}"] = config

            self.log_status(f"Generated configurations for {len(configurations)} faculty desk units")

            # Store configurations in parent for export
            if hasattr(self.parent(), 'esp32_configurations'):
                self.parent().esp32_configurations = configurations
            else:
                setattr(self.parent(), 'esp32_configurations', configurations)

            QMessageBox.information(self, "Configuration Generated",
                                  f"Successfully generated configurations for {len(configurations)} ESP32 units.")

        except Exception as e:
            logger.error(f"Error generating configurations: {str(e)}")
            QMessageBox.critical(self, "Generation Error", f"Error generating configurations: {str(e)}")

    def generate_faculty_config(self, faculty, beacon_config, unit_number):
        """Generate configuration for a specific faculty member."""
        from datetime import datetime

        # Create MAC addresses array
        mac_addresses = []
        for beacon_info in beacon_config.values():
            mac_addresses.append(beacon_info['mac_address'])

        # Pad with empty strings if less than 5 beacons
        while len(mac_addresses) < 5:
            mac_addresses.append("")

        config_content = f'''/**
 * ConsultEase - Faculty Desk Unit Configuration
 * Generated for: {faculty.name} (Unit #{unit_number})
 * Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
 *
 * This file contains configuration settings for Faculty Desk Unit #{unit_number}.
 * This unit is assigned to {faculty.name} in {faculty.department}.
 */

#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
#define WIFI_SSID "ConsultEase"
#define WIFI_PASSWORD "Admin123"

// MQTT Configuration
#define MQTT_SERVER "172.20.10.8"  // Update with your MQTT broker IP
#define MQTT_PORT 1883
#define MQTT_USERNAME ""  // Leave empty if not using authentication
#define MQTT_PASSWORD ""  // Leave empty if not using authentication

// Faculty Configuration - Unit #{unit_number}
#define FACULTY_ID {faculty.id}  // This should match the faculty ID in the database
#define FACULTY_NAME "{faculty.name}"  // This should match the faculty name in the database
#define FACULTY_DEPARTMENT "{faculty.department}"  // This should match the faculty department in the database

// BLE Configuration - MAC Address Detection for nRF51822 Beacons
#define BLE_SCAN_INTERVAL 3000  // Scan interval in milliseconds (optimized for nRF51822)
#define BLE_SCAN_DURATION 5     // Scan duration in seconds (longer for better beacon detection)
#define BLE_RSSI_THRESHOLD -85  // RSSI threshold for presence detection (adjusted for beacon range)

// Faculty MAC Addresses - nRF51822 BLE Beacon MAC addresses
// Format: "XX:XX:XX:XX:XX:XX" (case insensitive)
// All units scan for all beacons, but only report status for their assigned faculty
#define MAX_FACULTY_MAC_ADDRESSES 5
extern const char* FACULTY_MAC_ADDRESSES[MAX_FACULTY_MAC_ADDRESSES];

// MAC Address Detection Settings - Optimized for nRF51822 Beacons
#define MAC_DETECTION_TIMEOUT 45000    // Time in ms to consider faculty absent (increased for beacon reliability)
#define MAC_SCAN_ACTIVE true           // Use active scanning (better for beacon detection)
#define MAC_DETECTION_DEBOUNCE 2       // Number of consecutive scans needed (reduced for faster response)

// Display Configuration
#define TFT_ROTATION 1  // 0=Portrait, 1=Landscape, 2=Inverted Portrait, 3=Inverted Landscape

// Color Scheme - National University Philippines
#define NU_BLUE      0x0015      // Dark blue (navy) - Primary color
#define NU_GOLD      0xFE60      // Gold/Yellow - Secondary color
#define NU_DARKBLUE  0x000B      // Darker blue for contrasts
#define NU_LIGHTGOLD 0xF710      // Lighter gold for highlights
#define TFT_WHITE    0xFFFF      // White for text
#define TFT_BLACK    0x0000      // Black for backgrounds

// UI Colors
#define TFT_BG       NU_BLUE         // Background color
#define TFT_TEXT     TFT_WHITE       // Text color
#define TFT_HEADER   NU_DARKBLUE     // Header color
#define TFT_ACCENT   NU_GOLD         // Accent color
#define TFT_HIGHLIGHT NU_LIGHTGOLD   // Highlight color

// MQTT Topics - Standardized format
#define MQTT_TOPIC_STATUS "consultease/faculty/%d/status"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_MAC_STATUS "consultease/faculty/%d/mac_status"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_REQUESTS "consultease/faculty/%d/requests"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_MESSAGES "consultease/faculty/%d/messages"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_NOTIFICATIONS "consultease/system/notifications"

// Legacy MQTT Topics - For backward compatibility
#define MQTT_LEGACY_STATUS "professor/status"
#define MQTT_LEGACY_MESSAGES "professor/messages"

// Debug Configuration
#define DEBUG_ENABLED true  // Set to false to disable debug output

#endif // CONFIG_H

// MAC Addresses Array (add this to faculty_desk_unit.ino):
// Faculty MAC Addresses Definition - nRF51822 BLE Beacons
const char* FACULTY_MAC_ADDRESSES[MAX_FACULTY_MAC_ADDRESSES] = {{
'''

        for i, mac in enumerate(mac_addresses):
            if mac:
                config_content += f'  "{mac}"'
            else:
                config_content += f'  ""'

            if i < len(mac_addresses) - 1:
                config_content += ','

            if mac:
                # Find which beacon this is
                beacon_num = i + 1
                config_content += f'  // Beacon #{beacon_num}'
            else:
                config_content += f'  // Empty slot'

            config_content += '\n'

        config_content += '};\n'

        return config_content

    def preview_configuration(self):
        """Preview the configuration for the first faculty member."""
        if not self.faculty_data:
            QMessageBox.warning(self, "No Faculty Data", "No faculty members available for preview.")
            return

        if not hasattr(self.parent(), 'beacon_config') or not self.parent().beacon_config:
            QMessageBox.warning(self, "No Beacon Data", "Please configure beacon MAC addresses first.")
            return

        try:
            faculty = self.faculty_data[0]
            beacon_config = self.parent().beacon_config
            config = self.generate_faculty_config(faculty, beacon_config, 1)

            self.config_text.setPlainText(config)
            self.log_status(f"Previewing configuration for {faculty.name}")

        except Exception as e:
            logger.error(f"Error previewing configuration: {str(e)}")
            QMessageBox.critical(self, "Preview Error", f"Error previewing configuration: {str(e)}")

    def export_configurations(self):
        """Export all configurations to files."""
        if not hasattr(self.parent(), 'esp32_configurations'):
            QMessageBox.warning(self, "No Configurations", "Please generate configurations first.")
            return

        try:
            # Ask user for export directory
            from PyQt5.QtWidgets import QFileDialog
            export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")

            if not export_dir:
                return

            configurations = self.parent().esp32_configurations
            exported_count = 0

            for unit_name, config_content in configurations.items():
                file_path = os.path.join(export_dir, f"{unit_name}_config.h")

                with open(file_path, 'w') as f:
                    f.write(config_content)

                exported_count += 1
                self.log_status(f"Exported configuration for {unit_name}")

            QMessageBox.information(self, "Export Complete",
                                  f"Successfully exported {exported_count} configuration files to:\n{export_dir}")

        except Exception as e:
            logger.error(f"Error exporting configurations: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Error exporting configurations: {str(e)}")

    def log_status(self, message):
        """Add a status message to the status text area."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")

class BeaconTestingTab(QWidget):
    """Tab for testing beacon integration and monitoring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitoring = False
        self.mqtt_client = None
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Test the beacon integration and monitor real-time beacon detection. "
            "Use these tools to verify that your ESP32 units are properly detecting beacons."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f8ff; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        layout.addWidget(instructions)

        # Testing controls
        test_group = QGroupBox("Testing Controls")
        test_layout = QVBoxLayout()

        # MQTT connection test
        mqtt_layout = QHBoxLayout()
        mqtt_layout.addWidget(QLabel("MQTT Broker:"))

        self.mqtt_host_input = QLineEdit("172.20.10.8")
        mqtt_layout.addWidget(self.mqtt_host_input)

        self.mqtt_port_input = QLineEdit("1883")
        self.mqtt_port_input.setMaximumWidth(80)
        mqtt_layout.addWidget(self.mqtt_port_input)

        test_mqtt_button = QPushButton("Test MQTT Connection")
        test_mqtt_button.clicked.connect(self.test_mqtt_connection)
        mqtt_layout.addWidget(test_mqtt_button)

        test_layout.addLayout(mqtt_layout)

        # Monitoring controls
        monitor_layout = QHBoxLayout()

        self.monitor_button = QPushButton("Start Monitoring")
        self.monitor_button.clicked.connect(self.toggle_monitoring)
        monitor_layout.addWidget(self.monitor_button)

        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        monitor_layout.addWidget(clear_button)

        monitor_layout.addStretch()
        test_layout.addLayout(monitor_layout)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Monitoring log
        log_group = QGroupBox("Real-time Monitoring Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Monitoring messages will appear here...")
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def test_mqtt_connection(self):
        """Test MQTT broker connection."""
        try:
            import paho.mqtt.client as mqtt

            host = self.mqtt_host_input.text().strip()
            port = int(self.mqtt_port_input.text().strip())

            if not host:
                QMessageBox.warning(self, "Input Error", "Please enter MQTT broker host.")
                return

            # Create test client
            test_client = mqtt.Client()

            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    self.log_message("✓ MQTT connection successful")
                    QMessageBox.information(self, "Connection Test", "Successfully connected to MQTT broker!")
                    client.disconnect()
                else:
                    self.log_message(f"✗ MQTT connection failed (code {rc})")
                    QMessageBox.warning(self, "Connection Test", f"Failed to connect to MQTT broker (code {rc})")

            def on_disconnect(client, userdata, rc):
                self.log_message("MQTT disconnected")

            test_client.on_connect = on_connect
            test_client.on_disconnect = on_disconnect

            self.log_message(f"Testing MQTT connection to {host}:{port}...")
            test_client.connect(host, port, 60)
            test_client.loop_start()

            # Stop the loop after a short time
            QTimer.singleShot(3000, lambda: test_client.loop_stop())

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid port number.")
        except Exception as e:
            logger.error(f"Error testing MQTT connection: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Error testing MQTT connection: {str(e)}")

    def toggle_monitoring(self):
        """Start or stop monitoring beacon detection."""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """Start monitoring beacon detection messages."""
        try:
            import paho.mqtt.client as mqtt

            host = self.mqtt_host_input.text().strip()
            port = int(self.mqtt_port_input.text().strip())

            if not host:
                QMessageBox.warning(self, "Input Error", "Please enter MQTT broker host.")
                return

            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect

            self.log_message(f"Connecting to MQTT broker at {host}:{port}...")
            self.mqtt_client.connect(host, port, 60)
            self.mqtt_client.loop_start()

            self.monitoring = True
            self.monitor_button.setText("Stop Monitoring")
            self.monitor_button.setStyleSheet("background-color: #f44336; color: white;")

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid port number.")
        except Exception as e:
            logger.error(f"Error starting monitoring: {str(e)}")
            QMessageBox.critical(self, "Monitoring Error", f"Error starting monitoring: {str(e)}")

    def stop_monitoring(self):
        """Stop monitoring beacon detection messages."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.mqtt_client = None

        self.monitoring = False
        self.monitor_button.setText("Start Monitoring")
        self.monitor_button.setStyleSheet("")
        self.log_message("Monitoring stopped")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback."""
        if rc == 0:
            self.log_message("✓ Connected to MQTT broker")

            # Subscribe to relevant topics
            topics = [
                "consultease/faculty/+/status",
                "consultease/faculty/+/mac_status",
                "consultease/faculty/+/requests",
                "professor/status",
                "professor/messages"
            ]

            for topic in topics:
                client.subscribe(topic)
                self.log_message(f"Subscribed to {topic}")

        else:
            self.log_message(f"✗ Failed to connect to MQTT broker (code {rc})")

    def on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback."""
        try:
            topic = msg.topic
            payload = msg.payload.decode()

            # Format message for display
            if topic.endswith("/mac_status"):
                # Parse JSON payload for MAC status
                try:
                    import json
                    data = json.loads(payload)
                    status = data.get("status", "unknown")
                    mac = data.get("mac", "unknown")
                    faculty_id = topic.split("/")[2]

                    if status == "faculty_present":
                        self.log_message(f"🟢 Faculty {faculty_id} PRESENT (Beacon: {mac})", "green")
                    elif status == "faculty_absent":
                        self.log_message(f"🔴 Faculty {faculty_id} ABSENT (Beacon: {mac})", "red")
                    else:
                        self.log_message(f"📡 Faculty {faculty_id}: {status} (Beacon: {mac})")

                except json.JSONDecodeError:
                    self.log_message(f"📡 {topic}: {payload}")
            else:
                # Regular message
                if payload in ["keychain_connected", "faculty_present"]:
                    self.log_message(f"🟢 {topic}: {payload}", "green")
                elif payload in ["keychain_disconnected", "faculty_absent"]:
                    self.log_message(f"🔴 {topic}: {payload}", "red")
                else:
                    self.log_message(f"📡 {topic}: {payload}")

        except Exception as e:
            self.log_message(f"Error processing message: {str(e)}", "red")

    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback."""
        self.log_message("Disconnected from MQTT broker")

    def clear_log(self):
        """Clear the monitoring log."""
        self.log_text.clear()
        self.log_message("Log cleared")

    def log_message(self, message, color=None):
        """Add a message to the monitoring log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        if color:
            formatted_message = f'<span style="color: {color};">[{timestamp}] {message}</span>'
            self.log_text.append(formatted_message)
        else:
            self.log_text.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class FacultyDialog(QDialog):
    """
    Dialog for adding or editing faculty members.
    """
    def __init__(self, faculty_id=None, parent=None):
        super().__init__(parent)
        self.faculty_id = faculty_id
        self.image_path = None

        # Set window flags to ensure dialog stays on top and has proper modal behavior
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

        self.init_ui()

    def init_ui(self):
        """
        Initialize the UI components.
        """
        # Set title based on mode (add or edit)
        self.setWindowTitle("Edit Faculty" if self.faculty_id else "Add Faculty")

        # Main layout
        layout = QVBoxLayout()

        # Form layout for inputs
        form_layout = QFormLayout()

        # Name input
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)

        # Department input
        self.department_input = QLineEdit()
        form_layout.addRow("Department:", self.department_input)

        # Email input
        self.email_input = QLineEdit()
        form_layout.addRow("Email:", self.email_input)

        # BLE ID input
        self.ble_id_input = QLineEdit()
        form_layout.addRow("BLE ID:", self.ble_id_input)

        # Always available checkbox
        self.always_available_checkbox = QCheckBox("Always Available (BLE Always On)")
        self.always_available_checkbox.setToolTip("If checked, this faculty member will always be shown as available, regardless of BLE status")
        form_layout.addRow("", self.always_available_checkbox)

        # Image selection
        image_layout = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setReadOnly(True)
        self.image_path_input.setPlaceholderText("No image selected")

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_image)

        image_layout.addWidget(self.image_path_input)
        image_layout.addWidget(browse_button)

        form_layout.addRow("Profile Image:", image_layout)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # If editing, the faculty data will be populated by the caller
        # No need to fetch data here as it's passed in when the dialog is created

    def browse_image(self):
        """
        Open file dialog to select a faculty image.
        """
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.image_path = selected_files[0]
                self.image_path_input.setText(self.image_path)

    def accept(self):
        """
        Validate and accept the dialog.
        """
        # Validate inputs
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a name.")
            return

        if not self.department_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a department.")
            return

        if not self.email_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter an email.")
            return

        if not self.ble_id_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a BLE ID.")
            return

        # If all validations pass, accept the dialog
        super().accept()

class StudentManagementTab(QWidget):
    """
    Tab for managing students.
    """
    # Signals
    student_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.student_controller = None
        self.rfid_service = None  # Store RFID service instance
        self.init_ui()
        self.refresh_data()

        # Initialize RFID service
        try:
            from ..services import get_rfid_service
            self.rfid_service = get_rfid_service()
        except Exception as e:
            logger.warning(f"Failed to initialize RFID service: {e}")

        # For scanning RFID cards
        self.scanning_for_rfid = False
        self.scan_dialog = None
        self.rfid_callback = None

    def __del__(self):
        """
        Destructor to ensure cleanup happens when the object is destroyed.
        """
        try:
            self.cleanup()
        except Exception as e:
            # Can't use logger here as it might be None during shutdown
            print(f"Error in StudentManagementTab destructor: {str(e)}")

    def _safely_refresh_rfid_service(self, operation_name="operation"):
        """
        Safely refresh the RFID service with comprehensive error handling.
        
        Args:
            operation_name (str): Name of the operation for logging
            
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        try:
            # Method 1: Try to get fresh instance and reload module
            import importlib
            from ..services import rfid_service as rfid_module
            
            # Force reload the module to get latest code
            importlib.reload(rfid_module)
            
            # Get fresh service instance
            rfid_service_instance = rfid_module.get_rfid_service()
            
            # Check if the method exists
            if hasattr(rfid_service_instance, 'refresh_student_data'):
                rfid_service_instance.refresh_student_data()
                logger.info(f"✅ Successfully refreshed RFID service after {operation_name}")
                return True
            else:
                logger.warning(f"⚠️ refresh_student_data method not found on RFIDService")
                raise AttributeError("refresh_student_data method not found")
                
        except Exception as e:
            logger.warning(f"Method 1 failed: {str(e)}")
            
            try:
                # Method 2: Try using RFIDController as fallback
                from ..controllers.rfid_controller import RFIDController
                rfid_controller = RFIDController()
                
                if hasattr(rfid_controller, 'refresh_student_data'):
                    student_data = rfid_controller.refresh_student_data()
                    logger.info(f"✅ Used RFIDController.refresh_student_data() as fallback for {operation_name}")
                    logger.info(f"   Loaded {len(student_data)} students for RFID scanning")
                    return True
                else:
                    logger.warning("RFIDController.refresh_student_data() also not found")
                    
            except Exception as e2:
                logger.error(f"Method 2 failed: {str(e2)}")
                
                try:
                    # Method 3: Try direct import and instantiation
                    from central_system.services.rfid_service import RFIDService, get_rfid_service
                    
                    # Check if class has the method
                    if hasattr(RFIDService, 'refresh_student_data'):
                        rfid_instance = get_rfid_service()
                        rfid_instance.refresh_student_data()
                        logger.info(f"✅ Used direct RFIDService instance for {operation_name}")
                        return True
                    else:
                        logger.error("refresh_student_data method not found even in direct RFIDService class")
                        
                except Exception as e3:
                    logger.error(f"Method 3 failed: {str(e3)}")
                    
        # All methods failed
        logger.error(f"❌ All RFID refresh methods failed for {operation_name}")
        logger.error("💡 RFID service may need to be restarted manually")
        return False

    def debug_rfid_service(self):
        """
        Debug method to diagnose RFID service issues.
        Can be called manually to check service status.
        """
        logger.info("🔍 Starting RFID service debug...")
        
        try:
            # Test 1: Check file existence
            import os
            rfid_file = os.path.join(os.getcwd(), 'central_system', 'services', 'rfid_service.py')
            if os.path.exists(rfid_file):
                logger.info(f"✅ RFID service file exists: {rfid_file}")
                
                # Check file modification time
                import time
                mtime = os.path.getmtime(rfid_file)
                logger.info(f"   Last modified: {time.ctime(mtime)}")
            else:
                logger.error(f"❌ RFID service file not found: {rfid_file}")
                
            # Test 2: Check imports
            try:
                from central_system.services.rfid_service import RFIDService, get_rfid_service
                logger.info("✅ Direct import successful")
                
                # Test 3: Check class methods
                methods = [method for method in dir(RFIDService) if not method.startswith('_')]
                logger.info(f"   Available RFIDService methods: {methods}")
                
                if 'refresh_student_data' in methods:
                    logger.info("✅ refresh_student_data found in class definition")
                else:
                    logger.error("❌ refresh_student_data NOT found in class definition")
                    
            except Exception as e:
                logger.error(f"❌ Import failed: {e}")
                
            # Test 4: Check instance
            try:
                service = get_rfid_service()
                logger.info(f"✅ Service instance created: {type(service)}")
                
                instance_methods = [method for method in dir(service) if not method.startswith('_')]
                logger.info(f"   Instance methods: {instance_methods}")
                
                if hasattr(service, 'refresh_student_data'):
                    logger.info("✅ refresh_student_data found on instance")
                    
                    # Try to call it
                    result = service.refresh_student_data()
                    logger.info(f"✅ Method call successful, returned {len(result)} students")
                else:
                    logger.error("❌ refresh_student_data NOT found on instance")
                    
            except Exception as e:
                logger.error(f"❌ Instance test failed: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
        except Exception as e:
            logger.error(f"❌ Debug failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def init_ui(self):
        """
        Initialize the UI components.
        """
        # Create a container widget for the scroll area
        container = QWidget()

        # Main layout
        main_layout = QVBoxLayout(container)

        # Buttons for actions
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Student")
        self.add_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.add_button.clicked.connect(self.add_student)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Student")
        self.edit_button.clicked.connect(self.edit_student)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete Student")
        self.delete_button.setStyleSheet("background-color: #F44336; color: white;")
        self.delete_button.clicked.connect(self.delete_student)
        button_layout.addWidget(self.delete_button)

        self.scan_button = QPushButton("Scan RFID")
        self.scan_button.clicked.connect(self.scan_rfid)
        button_layout.addWidget(self.scan_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

        # Student table
        self.student_table = QTableWidget()
        self.student_table.setColumnCount(4)
        self.student_table.setHorizontalHeaderLabels(["ID", "Name", "Department", "RFID UID"])
        self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.student_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.student_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.student_table.setSelectionMode(QTableWidget.SingleSelection)

        main_layout.addWidget(self.student_table)

        # Add some spacing at the bottom for better appearance
        main_layout.addSpacing(10)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)

        # Only show scrollbars when needed
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Style the scroll area to match the application theme
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Create a layout for the tab and add the scroll area
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

        # Initial data load
        self.refresh_data()

    def cleanup(self):
        """
        Clean up resources when the tab is closed or the window is closed.
        """
        logger.info("Cleaning up StudentManagementTab resources")

        # Close any open scan dialog
        if self.scan_dialog and self.scan_dialog.isVisible():
            self.scan_dialog.close()
            self.scan_dialog = None

        # Unregister any RFID callbacks
        if self.rfid_callback:
            try:
                self.rfid_service.unregister_callback(self.rfid_callback)
                self.rfid_callback = None
                logger.info("Unregistered RFID callback")
            except Exception as e:
                logger.error(f"Error unregistering RFID callback: {str(e)}")

    def refresh_data(self):
        """
        Refresh the student data in the table.
        """
        # Clear the table
        self.student_table.setRowCount(0)

        try:
            # Get students from database
            db = get_db()
            students = db.query(Student).all()

            for student in students:
                row_position = self.student_table.rowCount()
                self.student_table.insertRow(row_position)

                # Add data to each column
                self.student_table.setItem(row_position, 0, QTableWidgetItem(str(student.id)))
                self.student_table.setItem(row_position, 1, QTableWidgetItem(student.name))
                self.student_table.setItem(row_position, 2, QTableWidgetItem(student.department))
                self.student_table.setItem(row_position, 3, QTableWidgetItem(student.rfid_uid))

        except Exception as e:
            logger.error(f"Error refreshing student data: {str(e)}")
            QMessageBox.warning(self, "Data Error", f"Failed to refresh student data: {str(e)}")

    def add_student(self):
        """
        Show dialog to add a new student.
        """
        # Import all necessary modules at the top level
        import traceback

        # Create dialog with this tab as the parent
        dialog = StudentDialog(parent=self)

        # Ensure dialog appears on top
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        if dialog.exec_() == QDialog.Accepted:
            try:
                name = dialog.name_input.text().strip()
                department = dialog.department_input.text().strip()
                rfid_uid = dialog.rfid_uid

                logger.info(f"Adding new student: Name={name}, Department={department}, RFID={rfid_uid}")

                # Use a separate function to handle the database operations
                self._add_student_to_database(name, department, rfid_uid)

            except Exception as e:
                logger.error(f"Error adding student: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                QMessageBox.warning(self, "Add Student", f"Error adding student: {str(e)}")

    def _add_student_to_database(self, name, department, rfid_uid):
        """
        Add a student to the database and refresh the RFID service.

        Args:
            name (str): Student name
            department (str): Student department
            rfid_uid (str): Student RFID UID
        """
        # Import all necessary modules
        import traceback
        from ..models import Student, get_db
        from ..services import get_rfid_service

        try:
            # Get a database connection
            db = get_db()

            # Check if RFID already exists
            existing = db.query(Student).filter(Student.rfid_uid == rfid_uid).first()
            if existing:
                QMessageBox.warning(self, "Add Student", f"A student with RFID {rfid_uid} already exists.")
                return

            # Create new student
            new_student = Student(
                name=name,
                department=department,
                rfid_uid=rfid_uid
            )

            # Add and commit
            db.add(new_student)
            db.commit()
            logger.info(f"Added student to database: {name} with RFID: {rfid_uid}")

            # Get the RFID service and refresh it
            self._safely_refresh_rfid_service(f"adding student {name}")

            # Show success message
            QMessageBox.information(self, "Add Student", f"Student '{name}' added successfully.")

            # Refresh the UI and emit signal
            self.refresh_data()
            self.student_updated.emit()

            # Log all students for debugging
            try:
                # Use a new database connection to ensure we get fresh data
                fresh_db = get_db(force_new=True)
                all_students = fresh_db.query(Student).all()
                logger.info(f"Available students in database after adding: {len(all_students)}")
                for s in all_students:
                    logger.info(f"  - ID: {s.id}, Name: {s.name}, RFID: {s.rfid_uid}")
                fresh_db.close()
            except Exception as e:
                logger.error(f"Error logging students: {str(e)}")

        except Exception as e:
            logger.error(f"Error in _add_student_to_database: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.warning(self, "Add Student", f"Error adding student to database: {str(e)}")

    def edit_student(self):
        """
        Show dialog to edit the selected student.
        """
        # Import all necessary modules at the top level
        import traceback
        from ..models import Student, get_db

        # Get selected row
        selected_rows = self.student_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Edit Student", "Please select a student to edit.")
            return

        # Get student ID from the first column
        row_index = selected_rows[0].row()
        student_id = int(self.student_table.item(row_index, 0).text())

        try:
            # Get student from database
            db = get_db()
            student = db.query(Student).filter(Student.id == student_id).first()

            if not student:
                QMessageBox.warning(self, "Edit Student", f"Student with ID {student_id} not found.")
                return

            # Create and populate dialog with this tab as the parent
            dialog = StudentDialog(student_id=student_id, parent=self)
            dialog.name_input.setText(student.name)
            dialog.department_input.setText(student.department)
            dialog.rfid_input.setText(student.rfid_uid)
            dialog.rfid_uid = student.rfid_uid

            # Ensure dialog appears on top
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

            if dialog.exec_() == QDialog.Accepted:
                name = dialog.name_input.text().strip()
                department = dialog.department_input.text().strip()
                rfid_uid = dialog.rfid_uid

                logger.info(f"Editing student: ID={student_id}, Name={name}, Department={department}, RFID={rfid_uid}")

                # Use a separate function to handle the database operations
                self._update_student_in_database(student_id, name, department, rfid_uid)

        except Exception as e:
            logger.error(f"Error editing student: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.warning(self, "Edit Student", f"Error editing student: {str(e)}")

    def _update_student_in_database(self, student_id, name, department, rfid_uid):
        """
        Update a student in the database and refresh the RFID service.

        Args:
            student_id (int): Student ID
            name (str): Student name
            department (str): Student department
            rfid_uid (str): Student RFID UID
        """
        # Import all necessary modules
        import traceback
        from ..models import Student, get_db
        from ..services import get_rfid_service

        try:
            # Get a database connection
            db = get_db()

            # Get the student
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                QMessageBox.warning(self, "Edit Student", f"Student with ID {student_id} not found.")
                return

            # Check if new RFID already exists (if changed)
            if rfid_uid != student.rfid_uid:
                existing = db.query(Student).filter(Student.rfid_uid == rfid_uid).first()
                if existing and existing.id != student_id:
                    QMessageBox.warning(self, "Edit Student", f"A student with RFID {rfid_uid} already exists.")
                    return

            # Update student
            student.name = name
            student.department = department
            student.rfid_uid = rfid_uid

            # Commit changes
            db.commit()
            logger.info(f"Updated student in database: ID={student_id}, Name={name}, RFID={rfid_uid}")

            # Get the RFID service and refresh it
            self._safely_refresh_rfid_service(f"updating student {name}")

            # Show success message
            QMessageBox.information(self, "Edit Student", f"Student '{name}' updated successfully.")

            # Refresh the UI and emit signal
            self.refresh_data()
            self.student_updated.emit()

            # Log all students for debugging
            try:
                # Use a new database connection to ensure we get fresh data
                fresh_db = get_db(force_new=True)
                all_students = fresh_db.query(Student).all()
                logger.info(f"Available students in database after updating: {len(all_students)}")
                for s in all_students:
                    logger.info(f"  - ID: {s.id}, Name: {s.name}, RFID: {s.rfid_uid}")
                fresh_db.close()
            except Exception as e:
                logger.error(f"Error logging students: {str(e)}")

        except Exception as e:
            logger.error(f"Error in _update_student_in_database: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.warning(self, "Edit Student", f"Error updating student in database: {str(e)}")

    def delete_student(self):
        """
        Delete the selected student.
        """
        # Import all necessary modules at the top level
        import traceback

        # Get selected row
        selected_rows = self.student_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Delete Student", "Please select a student to delete.")
            return

        # Get student ID and name from the table
        row_index = selected_rows[0].row()
        student_id = int(self.student_table.item(row_index, 0).text())
        student_name = self.student_table.item(row_index, 1).text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Student",
            f"Are you sure you want to delete student '{student_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                logger.info(f"Deleting student: ID={student_id}, Name={student_name}")

                # Use a separate function to handle the database operations
                self._delete_student_from_database(student_id, student_name)

            except Exception as e:
                logger.error(f"Error deleting student: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                QMessageBox.warning(self, "Delete Student", f"Error deleting student: {str(e)}")

    def _delete_student_from_database(self, student_id, student_name):
        """
        Delete a student from the database and refresh the RFID service.

        Args:
            student_id (int): Student ID
            student_name (str): Student name
        """
        # Import all necessary modules
        import traceback
        from ..models import Student, get_db
        from ..services import get_rfid_service

        try:
            # Get a database connection
            db = get_db()

            # Get the student
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                QMessageBox.warning(self, "Delete Student", f"Student with ID {student_id} not found.")
                return

            # Delete the student
            db.delete(student)
            db.commit()
            logger.info(f"Deleted student from database: ID={student_id}, Name={student_name}")

            # Get the RFID service and refresh it
            self._safely_refresh_rfid_service(f"deleting student {student_name}")

            # Show success message
            QMessageBox.information(self, "Delete Student", f"Student '{student_name}' deleted successfully.")

            # Refresh the UI and emit signal
            self.refresh_data()
            self.student_updated.emit()

            # Log all students for debugging
            try:
                # Use a new database connection to ensure we get fresh data
                fresh_db = get_db(force_new=True)
                all_students = fresh_db.query(Student).all()
                logger.info(f"Available students in database after deletion: {len(all_students)}")
                for s in all_students:
                    logger.info(f"  - ID: {s.id}, Name: {s.name}, RFID: {s.rfid_uid}")
                fresh_db.close()
            except Exception as e:
                logger.error(f"Error logging students: {str(e)}")

        except Exception as e:
            logger.error(f"Error in _delete_student_from_database: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.warning(self, "Delete Student", f"Error deleting student from database: {str(e)}")

    def scan_rfid(self):
        """
        Scan RFID card for student registration.
        """
        dialog = RFIDScanDialog(self.rfid_service, parent=self)
        self.scan_dialog = dialog

        # Ensure dialog appears on top
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        if dialog.exec_() == QDialog.Accepted:
            rfid_uid = dialog.get_rfid_uid()
            if rfid_uid:
                QMessageBox.information(self, "RFID Scan", f"RFID card scanned: {rfid_uid}")

                # Look up student by RFID
                try:
                    db = get_db()
                    student = db.query(Student).filter(Student.rfid_uid == rfid_uid).first()

                    if student:
                        # Select the student in the table
                        for row in range(self.student_table.rowCount()):
                            if self.student_table.item(row, 3).text() == rfid_uid:
                                self.student_table.selectRow(row)
                                QMessageBox.information(
                                    self,
                                    "Student Found",
                                    f"Student found: {student.name}\nDepartment: {student.department}"
                                )
                                break
                    else:
                        # No student with this RFID
                        reply = QMessageBox.question(
                            self,
                            "Add New Student",
                            f"No student found with RFID: {rfid_uid}\nWould you like to add a new student with this RFID?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes
                        )

                        if reply == QMessageBox.Yes:
                            # Pre-fill the RFID field in the student dialog with this as parent
                            dialog = StudentDialog(parent=self)
                            dialog.rfid_uid = rfid_uid
                            dialog.rfid_input.setText(rfid_uid)

                            # Ensure dialog appears on top
                            dialog.show()
                            dialog.raise_()
                            dialog.activateWindow()

                            if dialog.exec_() == QDialog.Accepted:
                                try:
                                    name = dialog.name_input.text().strip()
                                    department = dialog.department_input.text().strip()

                                    logger.info(f"Adding new student via RFID scan: Name={name}, Department={department}, RFID={rfid_uid}")

                                    # Use the existing method to add the student to the database
                                    self._add_student_to_database(name, department, rfid_uid)

                                except Exception as e:
                                    logger.error(f"Error adding student: {str(e)}")
                                    QMessageBox.warning(self, "Add Student", f"Error adding student: {str(e)}")

                except Exception as e:
                    logger.error(f"Error looking up student by RFID: {str(e)}")
                    QMessageBox.warning(self, "RFID Lookup Error", f"Error looking up student: {str(e)}")

class StudentDialog(QDialog):
    """
    Dialog for adding or editing students.
    """
    def __init__(self, student_id=None, parent=None):
        # Ensure parent is properly set
        super().__init__(parent)
        self.student_id = student_id
        self.rfid_uid = ""
        self.is_scanning = False
        self.rfid_scan_dialog = None

        # Get RFID service
        from central_system.services import get_rfid_service
        self.rfid_service = get_rfid_service()

        # Store a reference to our scan callback
        self.scan_callback = None

        self.init_ui()

        # If editing, the student data will be populated by the caller
        # No need to fetch data here as it's passed in when the dialog is created

    def init_ui(self):
        """
        Initialize the UI components.
        """
        # Set title based on mode (add or edit)
        self.setWindowTitle("Edit Student" if self.student_id else "Add Student")

        # Main layout
        layout = QVBoxLayout()

        # Form layout for inputs
        form_layout = QFormLayout()

        # Name input
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)

        # Department input
        self.department_input = QLineEdit()
        form_layout.addRow("Department:", self.department_input)

        # RFID UID input and scan button
        rfid_layout = QHBoxLayout()
        self.rfid_input = QLineEdit()
        self.rfid_input.setReadOnly(True)
        rfid_layout.addWidget(self.rfid_input, 1)

        scan_button = QPushButton("Scan RFID")
        scan_button.clicked.connect(self.scan_rfid)
        rfid_layout.addWidget(scan_button)

        form_layout.addRow("RFID UID:", rfid_layout)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def scan_rfid(self):
        """
        Scan RFID card.
        """
        try:
            logger.info("StudentDialog: Starting RFID scan")

            # Create our own RFID scan handler to receive directly from the service
            def handle_scan(student=None, rfid_uid=None):
                if not rfid_uid:
                    return

                logger.info(f"StudentDialog: RFID scan received: {rfid_uid}")
                self.rfid_uid = rfid_uid
                self.rfid_input.setText(self.rfid_uid)

                # If this was a simulation, trigger the animation to stop
                if self.rfid_scan_dialog and self.rfid_scan_dialog.isVisible():
                    self.rfid_scan_dialog.handle_rfid_scan(student, rfid_uid)

            # Store the callback reference to prevent garbage collection
            self.scan_callback = handle_scan

            # Register our callback with the RFID service
            self.rfid_service.register_callback(self.scan_callback)
            self.is_scanning = True

            # Create and show the dialog with this dialog as parent
            self.rfid_scan_dialog = RFIDScanDialog(self.rfid_service, parent=self)

            # Ensure dialog appears on top
            self.rfid_scan_dialog.show()
            self.rfid_scan_dialog.raise_()
            self.rfid_scan_dialog.activateWindow()

            # Wait for the dialog to complete
            result = self.rfid_scan_dialog.exec_()

            # When the dialog completes, get the value
            if result == QDialog.Accepted:
                rfid_uid = self.rfid_scan_dialog.get_rfid_uid()
                if rfid_uid:
                    logger.info(f"StudentDialog: Dialog returned RFID: {rfid_uid}")
                    self.rfid_uid = rfid_uid
                    self.rfid_input.setText(self.rfid_uid)

            # Clean up our callback
            try:
                if self.scan_callback:
                    self.rfid_service.unregister_callback(self.scan_callback)
                    self.scan_callback = None
                self.is_scanning = False
            except Exception as e:
                logger.error(f"Error unregistering RFID callback: {str(e)}")

        except Exception as e:
            logger.error(f"Error in student RFID scan: {str(e)}")
            QMessageBox.warning(self, "RFID Scan Error", f"An error occurred while scanning: {str(e)}")

    def closeEvent(self, event):
        """Handle dialog close to clean up callback"""
        # Clean up our callback if we're still scanning
        if hasattr(self, 'scan_callback') and self.scan_callback and self.is_scanning:
            try:
                self.rfid_service.unregister_callback(self.scan_callback)
                self.scan_callback = None
                self.is_scanning = False
                logger.info("Unregistered RFID callback in StudentDialog closeEvent")
            except Exception as e:
                logger.error(f"Error unregistering RFID callback in closeEvent: {str(e)}")
        super().closeEvent(event)

    def accept(self):
        """
        Validate and accept the dialog.
        """
        # Validate inputs
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a name.")
            return

        if not self.department_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a department.")
            return

        if not self.rfid_uid:
            QMessageBox.warning(self, "Validation Error", "Please scan an RFID card.")
            return

        # If all validations pass, accept the dialog
        super().accept()

    def get_rfid_uid(self):
        """
        Get the scanned RFID UID.
        """
        return self.rfid_uid

class RFIDScanDialog(QDialog):
    """
    Dialog for RFID card scanning.
    """
    def __init__(self, rfid_service=None, parent=None):
        # Ensure parent is properly set
        super().__init__(parent)
        self.rfid_uid = ""
        self.rfid_service = rfid_service or get_rfid_service()

        # Set window flags to ensure dialog stays on top and has proper modal behavior
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

        # Track whether we've received a scan
        self.scan_received = False

        self.init_ui()

        # Add a direct callback reference to prevent garbage collection
        self.callback_fn = self.handle_rfid_scan

        # Register RFID callback - ensure we're using the instance method
        self.rfid_service.register_callback(self.callback_fn)

        # Start the scanning animation
        self.scanning_timer = QTimer(self)
        self.scanning_timer.timeout.connect(self.update_animation)
        self.scanning_timer.start(500)  # Update every 500ms

        # For development, add a simulate button
        if os.environ.get('RFID_SIMULATION_MODE', 'true').lower() == 'true':
            self.simulate_button = QPushButton("Simulate Scan")
            self.simulate_button.clicked.connect(self.simulate_scan)
            self.layout().addWidget(self.simulate_button, alignment=Qt.AlignCenter)

    def init_ui(self):
        """
        Initialize the UI components.
        """
        self.setWindowTitle("RFID Scan")
        self.setFixedSize(350, 350)  # Make dialog taller for manual input

        # Main layout
        layout = QVBoxLayout()

        # Instructions
        instruction_label = QLabel("Please scan the 13.56 MHz RFID card...")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet("font-size: 14pt;")
        layout.addWidget(instruction_label)

        # Animation label
        self.animation_label = QLabel("🔄")
        self.animation_label.setAlignment(Qt.AlignCenter)
        self.animation_label.setStyleSheet("font-size: 48pt; color: #4a86e8;")
        layout.addWidget(self.animation_label)

        # Status label
        self.status_label = QLabel("Scanning...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12pt; color: #4a86e8;")
        layout.addWidget(self.status_label)

        # Add manual input section
        manual_section = QGroupBox("Manual RFID Input")
        manual_layout = QVBoxLayout()

        manual_instructions = QLabel("If scanning doesn't work, enter the RFID manually:")
        manual_layout.addWidget(manual_instructions)

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Enter RFID UID manually")
        self.manual_input.returnPressed.connect(self.handle_manual_input)
        manual_layout.addWidget(self.manual_input)

        manual_submit = QPushButton("Submit Manual RFID")
        manual_submit.clicked.connect(self.handle_manual_input)
        manual_layout.addWidget(manual_submit)

        manual_section.setLayout(manual_layout)
        layout.addWidget(manual_section)

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def handle_manual_input(self):
        """
        Handle manual RFID input.
        """
        uid = self.manual_input.text().strip().upper()
        if uid:
            logger.info(f"Manual RFID input: {uid}")
            self.manual_input.clear()
            self.handle_rfid_scan(None, uid)
        else:
            self.status_label.setText("Please enter a valid RFID UID")
            self.status_label.setStyleSheet("font-size: 12pt; color: #f44336;")
            QTimer.singleShot(2000, lambda: self.reset_status_label())

    def reset_status_label(self):
        """Reset the status label to its default state"""
        if not self.scan_received:  # Only reset if we haven't received a scan
            self.status_label.setText("Scanning...")
            self.status_label.setStyleSheet("font-size: 12pt; color: #4a86e8;")

    def update_animation(self):
        """
        Update the scanning animation.
        """
        if self.scan_received:  # Don't update if we've received a scan
            return

        animations = ["🔄", "🔁", "🔃", "🔂"]
        current_index = animations.index(self.animation_label.text()) if self.animation_label.text() in animations else 0
        next_index = (current_index + 1) % len(animations)
        self.animation_label.setText(animations[next_index])

    def handle_rfid_scan(self, student=None, rfid_uid=None):
        """
        Handle RFID scan event.
        """
        logger.info(f"RFIDScanDialog received scan: {rfid_uid}")

        # Ignore if no UID was provided or if we already received a scan
        if not rfid_uid or self.scan_received:
            logger.info(f"Ignoring scan - no UID or already received: {rfid_uid}")
            return

        self.scan_received = True
        self.rfid_uid = rfid_uid

        # Update UI
        self.scanning_timer.stop()
        self.animation_label.setText("✅")
        self.animation_label.setStyleSheet("font-size: 48pt; color: #4caf50;")
        self.status_label.setText(f"Card detected: {self.rfid_uid}")
        self.status_label.setStyleSheet("font-size: 12pt; color: #4caf50;")

        # If a student was found with this RFID, show a warning
        if student:
            QMessageBox.warning(
                self,
                "RFID Already Registered",
                f"This RFID card is already registered to student:\n{student.name}"
            )

        # Auto-accept after a delay
        QTimer.singleShot(1500, self.accept)

    def closeEvent(self, event):
        """Handle dialog close to clean up callback"""
        # Unregister callback to prevent memory leaks
        if hasattr(self, 'callback_fn') and self.callback_fn:
            try:
                self.rfid_service.unregister_callback(self.callback_fn)
                logger.info("Unregistered RFID callback in RFIDScanDialog closeEvent")
            except Exception as e:
                logger.error(f"Error unregistering RFID callback in closeEvent: {str(e)}")
        super().closeEvent(event)

    def reject(self):
        """Override reject to clean up callback"""
        # Unregister callback to prevent memory leaks
        if hasattr(self, 'callback_fn') and self.callback_fn:
            try:
                self.rfid_service.unregister_callback(self.callback_fn)
                logger.info("Unregistered RFID callback in RFIDScanDialog reject")
            except Exception as e:
                logger.error(f"Error unregistering RFID callback in reject: {str(e)}")
        super().reject()

    def accept(self):
        """
        Accept the dialog.
        """
        # Unregister our callback
        try:
            if hasattr(self, 'callback_fn') and self.callback_fn:
                self.rfid_service.unregister_callback(self.callback_fn)
                self.callback_fn = None
                logger.info("Unregistered RFID callback in accept")
        except Exception as e:
            logger.error(f"Error unregistering RFID callback in accept: {str(e)}")
        super().accept()

    def simulate_scan(self):
        """
        Simulate a successful RFID scan.
        """
        try:
            # Disable the simulate button to prevent multiple clicks
            if hasattr(self, 'simulate_button'):
                self.simulate_button.setEnabled(False)

            # Only simulate if no real scan has occurred yet
            if not self.scan_received:
                logger.info("Simulating RFID scan from RFIDScanDialog")

                # Generate a random RFID number
                import random
                random_uid = ''.join(random.choices('0123456789ABCDEF', k=8))
                logger.info(f"Generated random RFID: {random_uid}")

                # Call the service's simulate method
                self.rfid_service.simulate_card_read(random_uid)

                logger.info(f"Simulation complete, RFID: {random_uid}")
        except Exception as e:
            logger.error(f"Error in RFID simulation: {str(e)}")
            self.status_label.setText(f"Simulation error: {str(e)}")
            # Re-enable the button if there was an error
            if hasattr(self, 'simulate_button'):
                self.simulate_button.setEnabled(True)

    def get_rfid_uid(self):
        """
        Get the scanned RFID UID.
        """
        return self.rfid_uid

class SystemMaintenanceTab(QWidget):
    """
    Tab for system maintenance tasks.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.consultation_controller = None
        self.admin_controller = None
        self.init_ui()
        self.load_faculty_list()

    def init_ui(self):
        """
        Initialize the UI components.
        """
        # Create a container widget for the scroll area
        container = QWidget()

        # Main layout
        main_layout = QVBoxLayout(container)

        # Database section
        database_group = QGroupBox("Database Maintenance")
        database_layout = QVBoxLayout()

        # Backup/restore buttons
        backup_button = QPushButton("Backup Database")
        backup_button.clicked.connect(self.backup_database)
        database_layout.addWidget(backup_button)

        restore_button = QPushButton("Restore Database")
        restore_button.clicked.connect(self.restore_database)
        database_layout.addWidget(restore_button)

        database_group.setLayout(database_layout)
        main_layout.addWidget(database_group)

        # Admin Account Management section
        admin_group = QGroupBox("Admin Account Management")
        admin_layout = QVBoxLayout()

        # Change Username section
        username_form = QFormLayout()
        self.current_password_username = QLineEdit()
        self.current_password_username.setEchoMode(QLineEdit.Password)
        username_form.addRow("Current Password:", self.current_password_username)

        self.new_username_input = QLineEdit()
        username_form.addRow("New Username:", self.new_username_input)

        change_username_button = QPushButton("Change Username")
        change_username_button.clicked.connect(self.change_admin_username)
        username_form.addRow("", change_username_button)

        admin_layout.addLayout(username_form)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        admin_layout.addWidget(separator)

        # Change Password section
        password_form = QFormLayout()
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.Password)
        password_form.addRow("Current Password:", self.current_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        password_form.addRow("New Password:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        password_form.addRow("Confirm Password:", self.confirm_password_input)

        change_password_button = QPushButton("Change Password")
        change_password_button.clicked.connect(self.open_password_change_dialog)
        password_form.addRow("", change_password_button)

        admin_layout.addLayout(password_form)
        admin_group.setLayout(admin_layout)
        main_layout.addWidget(admin_group)

        # System logs section
        logs_group = QGroupBox("System Logs")
        logs_layout = QVBoxLayout()

        view_logs_button = QPushButton("View Logs")
        view_logs_button.clicked.connect(self.view_logs)
        logs_layout.addWidget(view_logs_button)

        logs_group.setLayout(logs_layout)
        main_layout.addWidget(logs_group)

        # Faculty Desk Unit section
        faculty_desk_group = QGroupBox("Faculty Desk Unit")
        faculty_desk_layout = QVBoxLayout()

        # Add a dropdown to select faculty
        faculty_layout = QHBoxLayout()
        faculty_label = QLabel("Select Faculty:")
        self.faculty_combo = QComboBox()
        self.faculty_combo.setMinimumWidth(200)
        faculty_layout.addWidget(faculty_label)
        faculty_layout.addWidget(self.faculty_combo)
        faculty_desk_layout.addLayout(faculty_layout)

        # Add a button to test the connection
        test_connection_button = QPushButton("Test Faculty Desk Connection")
        test_connection_button.clicked.connect(self.test_faculty_desk_connection)
        faculty_desk_layout.addWidget(test_connection_button)

        faculty_desk_group.setLayout(faculty_desk_layout)
        main_layout.addWidget(faculty_desk_group)

        # Beacon Management section
        beacon_group = QGroupBox("nRF51822 Beacon Management")
        beacon_layout = QVBoxLayout()

        # Quick access to beacon management
        beacon_info_label = QLabel(
            "Manage nRF51822 BLE beacons for faculty presence detection. "
            "Configure beacon MAC addresses and assign them to faculty members."
        )
        beacon_info_label.setWordWrap(True)
        beacon_info_label.setStyleSheet("margin-bottom: 10px; color: #666;")
        beacon_layout.addWidget(beacon_info_label)

        beacon_button_layout = QHBoxLayout()

        open_beacon_mgmt_button = QPushButton("Open Beacon Management")
        open_beacon_mgmt_button.setStyleSheet("background-color: #2196F3; color: white;")
        open_beacon_mgmt_button.clicked.connect(self.open_beacon_management_from_system)
        beacon_button_layout.addWidget(open_beacon_mgmt_button)

        test_beacon_button = QPushButton("Test Beacon Detection")
        test_beacon_button.clicked.connect(self.test_beacon_detection)
        beacon_button_layout.addWidget(test_beacon_button)

        beacon_button_layout.addStretch()
        beacon_layout.addLayout(beacon_button_layout)

        beacon_group.setLayout(beacon_layout)
        main_layout.addWidget(beacon_group)

        # System settings section
        settings_group = QGroupBox("System Settings")
        settings_layout = QFormLayout()

        # MQTT settings
        self.mqtt_host_input = QLineEdit(os.environ.get('MQTT_BROKER_HOST', 'localhost'))
        settings_layout.addRow("MQTT Broker Host:", self.mqtt_host_input)

        self.mqtt_port_input = QLineEdit(os.environ.get('MQTT_BROKER_PORT', '1883'))
        settings_layout.addRow("MQTT Broker Port:", self.mqtt_port_input)

        # Auto-start settings
        self.auto_start_checkbox = QCheckBox()
        self.auto_start_checkbox.setChecked(True)
        settings_layout.addRow("Auto-start on boot:", self.auto_start_checkbox)

        # Save button
        save_settings_button = QPushButton("Save Settings")
        save_settings_button.clicked.connect(self.save_settings)
        settings_layout.addRow("", save_settings_button)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Add some spacing at the bottom for better appearance
        main_layout.addSpacing(20)

        # Create a scroll area for the system maintenance tab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container)

        # Only show scrollbars when needed
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Style the scroll area to match the application theme
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Create a layout for the tab and add the scroll area
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)

    def backup_database(self):
        """
        Backup the database to a file.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Backup Database",
            os.path.expanduser("~/consultease_backup.db"),
            "Database Files (*.db *.sql)"
        )

        if file_path:
            try:
                # Get database type
                from ..models.base import DB_TYPE

                # Show progress dialog
                progress_dialog = QMessageBox(self)
                progress_dialog.setWindowTitle("Database Backup")
                progress_dialog.setText("Backing up database, please wait...")
                progress_dialog.setStandardButtons(QMessageBox.NoButton)
                progress_dialog.show()
                QApplication.processEvents()

                if DB_TYPE.lower() == 'sqlite':
                    # For SQLite, just copy the file
                    from ..models.base import DB_PATH
                    import shutil

                    # Create backup command for display
                    backup_cmd = f"Copy {DB_PATH} to {file_path}"

                    # Ask for confirmation
                    progress_dialog.close()
                    reply = QMessageBox.question(
                        self,
                        "Backup Database",
                        f"The system will backup the SQLite database:\n\n{backup_cmd}\n\nContinue?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )

                    if reply == QMessageBox.Yes:
                        progress_dialog.show()
                        QApplication.processEvents()

                        # Copy the SQLite database file
                        shutil.copy2(DB_PATH, file_path)
                        success = True
                    else:
                        success = False
                else:
                    # For PostgreSQL, use pg_dump
                    from ..models.base import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

                    # Create backup command
                    backup_cmd = f"pg_dump -U {DB_USER} -h {DB_HOST} -d {DB_NAME} -f {file_path}"

                    # Ask for confirmation
                    progress_dialog.close()
                    reply = QMessageBox.question(
                        self,
                        "Backup Database",
                        f"The system will execute the following command:\n\n{backup_cmd}\n\nContinue?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )

                    if reply == QMessageBox.Yes:
                        progress_dialog.show()
                        QApplication.processEvents()

                        # Execute the command
                        import subprocess
                        env = os.environ.copy()
                        env["PGPASSWORD"] = DB_PASSWORD
                        result = subprocess.run(
                            backup_cmd,
                            shell=True,
                            env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )

                        success = (result.returncode == 0)
                    else:
                        success = False

                # Close progress dialog
                progress_dialog.close()

                if success:
                    QMessageBox.information(self, "Backup Database", f"Database backup saved to:\n{file_path}")
                else:
                    if 'result' in locals() and hasattr(result, 'stderr'):
                        error_msg = result.stderr.decode('utf-8')
                        QMessageBox.critical(self, "Backup Error", f"Failed to backup database:\n{error_msg}")
                    else:
                        QMessageBox.critical(self, "Backup Error", "Backup operation was cancelled or failed.")

            except Exception as e:
                logger.error(f"Error backing up database: {str(e)}")
                QMessageBox.critical(self, "Backup Error", f"Error backing up database: {str(e)}")

    def restore_database(self):
        """
        Restore the database from a file.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database",
            os.path.expanduser("~"),
            "Database Files (*.db *.sql)"
        )

        if file_path:
            # Confirm restore
            reply = QMessageBox.warning(
                self,
                "Restore Database",
                "Restoring the database will overwrite all current data. Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                try:
                    # Get database type
                    from ..models.base import DB_TYPE

                    # Show progress dialog
                    progress_dialog = QMessageBox(self)
                    progress_dialog.setWindowTitle("Database Restore")
                    progress_dialog.setText("Restoring database, please wait...")
                    progress_dialog.setStandardButtons(QMessageBox.NoButton)
                    progress_dialog.show()
                    QApplication.processEvents()

                    success = False

                    if DB_TYPE.lower() == 'sqlite':
                        # For SQLite, just copy the file
                        from ..models.base import DB_PATH
                        import shutil

                        # Create restore command for display
                        restore_cmd = f"Copy {file_path} to {DB_PATH}"

                        # Make a backup of the current database first
                        backup_path = f"{DB_PATH}.bak"
                        if os.path.exists(DB_PATH):
                            shutil.copy2(DB_PATH, backup_path)
                            logger.info(f"Created backup of current database at {backup_path}")

                        # Copy the backup file to the database location
                        shutil.copy2(file_path, DB_PATH)

                        # Verify the restore
                        if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
                            success = True
                        else:
                            # Restore from backup if the restore failed
                            if os.path.exists(backup_path):
                                shutil.copy2(backup_path, DB_PATH)
                                logger.warning("Restore failed, reverted to backup")
                    else:
                        # For PostgreSQL, use psql
                        from ..models.base import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME

                        # Create restore command
                        restore_cmd = f"psql -U {DB_USER} -h {DB_HOST} -d {DB_NAME} -f {file_path}"

                        # Execute the command
                        import subprocess
                        env = os.environ.copy()
                        env["PGPASSWORD"] = DB_PASSWORD
                        result = subprocess.run(
                            restore_cmd,
                            shell=True,
                            env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )

                        success = (result.returncode == 0)

                    # Close progress dialog
                    progress_dialog.close()

                    if success:
                        QMessageBox.information(self, "Restore Database", f"Database restored from:\n{file_path}")

                        # Inform the user that a restart is needed
                        QMessageBox.information(
                            self,
                            "Restart Required",
                            "The database has been restored. Please restart the application for changes to take effect."
                        )
                    else:
                        if 'result' in locals() and hasattr(result, 'stderr'):
                            error_msg = result.stderr.decode('utf-8')
                            QMessageBox.critical(self, "Restore Error", f"Failed to restore database:\n{error_msg}")
                        else:
                            QMessageBox.critical(self, "Restore Error", "Failed to restore database.")

                except Exception as e:
                    logger.error(f"Error restoring database: {str(e)}")
                    QMessageBox.critical(self, "Restore Error", f"Error restoring database: {str(e)}")

    def view_logs(self):
        """
        View system logs.
        """
        # Create a log viewer dialog
        log_dialog = LogViewerDialog(self)
        log_dialog.exec_()

    def load_faculty_list(self):
        """
        Load the list of faculty members into the dropdown.
        """
        try:
            # Import the faculty controller
            from ..controllers import FacultyController
            faculty_controller = FacultyController()

            # Get all faculty members
            faculties = faculty_controller.get_all_faculty()

            # Clear the dropdown
            self.faculty_combo.clear()

            # Add faculty members to the dropdown
            for faculty in faculties:
                self.faculty_combo.addItem(f"{faculty.name} (ID: {faculty.id})", faculty.id)

            logger.info(f"Loaded {len(faculties)} faculty members into dropdown")
        except Exception as e:
            logger.error(f"Error loading faculty list: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load faculty list: {str(e)}")

    def test_faculty_desk_connection(self):
        """
        Test the connection to the selected faculty desk unit.
        """
        try:
            # Get the selected faculty ID
            if self.faculty_combo.count() == 0:
                QMessageBox.warning(self, "Test Connection", "No faculty members available. Please add faculty members first.")
                return

            faculty_id = self.faculty_combo.currentData()
            faculty_name = self.faculty_combo.currentText().split(" (ID:")[0]

            if not faculty_id:
                QMessageBox.warning(self, "Test Connection", "Please select a faculty member.")
                return

            # Import the consultation controller if not already imported
            if not self.consultation_controller:
                from ..controllers import ConsultationController
                self.consultation_controller = ConsultationController()

            # Show a progress dialog
            progress_dialog = QMessageBox(self)
            progress_dialog.setWindowTitle("Testing Connection")
            progress_dialog.setText(f"Sending test message to faculty desk unit for {faculty_name}...\nPlease check the faculty desk unit display.")
            progress_dialog.setStandardButtons(QMessageBox.NoButton)
            progress_dialog.show()
            QApplication.processEvents()

            # Send a test message
            success = self.consultation_controller.test_faculty_desk_connection(faculty_id)

            # Close the progress dialog
            progress_dialog.close()

            if success:
                QMessageBox.information(self, "Test Connection",
                    f"Test message sent successfully to faculty desk unit for {faculty_name}.\n\n"
                    f"If the faculty desk unit did not receive the message, please check:\n"
                    f"1. The faculty desk unit is powered on and connected to WiFi\n"
                    f"2. The MQTT broker is running and accessible\n"
                    f"3. The faculty ID in the faculty desk unit matches the faculty ID in the database\n"
                    f"4. The MQTT topics are correctly configured")
            else:
                QMessageBox.warning(self, "Test Connection",
                    f"Failed to send test message to faculty desk unit for {faculty_name}.\n\n"
                    f"Please check:\n"
                    f"1. The MQTT broker is running and accessible\n"
                    f"2. The MQTT broker host and port are correctly configured\n"
                    f"3. The network connection is working")

        except Exception as e:
            logger.error(f"Error testing faculty desk connection: {str(e)}")
            QMessageBox.critical(self, "Test Connection", f"Error testing faculty desk connection: {str(e)}")

    def change_admin_username(self):
        """
        Change the admin username.
        """
        try:
            # Get the current admin info from the parent window
            parent_window = self.window()
            if not hasattr(parent_window, 'admin') or not parent_window.admin:
                QMessageBox.warning(self, "Admin Error", "No admin user is currently logged in.")
                return

            # Get admin ID
            admin_id = parent_window.admin.get('id') if isinstance(parent_window.admin, dict) else parent_window.admin.id

            # Get input values
            current_password = self.current_password_username.text()
            new_username = self.new_username_input.text().strip()

            # Validate inputs
            if not current_password:
                QMessageBox.warning(self, "Validation Error", "Please enter your current password.")
                return

            if not new_username:
                QMessageBox.warning(self, "Validation Error", "Please enter a new username.")
                return

            # Initialize admin controller if needed
            if not self.admin_controller:
                from ..controllers import AdminController
                self.admin_controller = AdminController()

            # Change username
            success = self.admin_controller.change_username(admin_id, current_password, new_username)

            if success:
                # Update the admin info in the parent window
                if isinstance(parent_window.admin, dict):
                    parent_window.admin['username'] = new_username
                else:
                    parent_window.admin.username = new_username

                # Update the header label in the parent window
                for child in parent_window.findChildren(QLabel):
                    if "Logged in as:" in child.text():
                        child.setText(f"Admin Dashboard - Logged in as: {new_username}")
                        break

                QMessageBox.information(self, "Username Changed", "Your username has been changed successfully.")

                # Clear the input fields
                self.current_password_username.clear()
                self.new_username_input.clear()
            else:
                QMessageBox.warning(self, "Username Change Failed", "Failed to change username. Please check your password and try again.")

        except Exception as e:
            logger.error(f"Error changing admin username: {str(e)}")
            QMessageBox.critical(self, "Username Change Error", f"Error changing username: {str(e)}")

    def change_admin_password(self):
        """
        Change the admin password.
        """
        try:
            # Get the current admin info from the parent window
            parent_window = self.window()
            if not hasattr(parent_window, 'admin') or not parent_window.admin:
                QMessageBox.warning(self, "Admin Error", "No admin user is currently logged in.")
                return

            # Get admin ID
            admin_id = parent_window.admin.get('id') if isinstance(parent_window.admin, dict) else parent_window.admin.id

            # Get input values
            current_password = self.current_password_input.text()
            new_password = self.new_password_input.text()
            confirm_password = self.confirm_password_input.text()

            # Validate inputs
            if not current_password:
                QMessageBox.warning(self, "Validation Error", "Please enter your current password.")
                return

            if not new_password:
                QMessageBox.warning(self, "Validation Error", "Please enter a new password.")
                return

            if new_password != confirm_password:
                QMessageBox.warning(self, "Validation Error", "New password and confirmation do not match.")
                return

            # Initialize admin controller if needed
            if not self.admin_controller:
                from ..controllers import AdminController
                self.admin_controller = AdminController()

            # Change password
            success = self.admin_controller.change_password(admin_id, current_password, new_password)

            if success:
                QMessageBox.information(self, "Password Changed", "Your password has been changed successfully.")

                # Clear the input fields
                self.current_password_input.clear()
                self.new_password_input.clear()
                self.confirm_password_input.clear()
            else:
                QMessageBox.warning(self, "Password Change Failed", "Failed to change password. Please check your current password and try again.")

        except ValueError as e:
            # This will catch password validation errors from the Admin model
            logger.error(f"Password validation error: {str(e)}")
            QMessageBox.warning(self, "Password Validation Error", str(e))
        except Exception as e:
            logger.error(f"Error changing admin password: {str(e)}")
            QMessageBox.critical(self, "Password Change Error", f"Error changing password: {str(e)}")

    def open_password_change_dialog(self):
        """
        Open the enhanced password change dialog.
        """
        try:
            # Get the current admin info from the parent window
            parent_window = self.window()
            if not hasattr(parent_window, 'admin') or not parent_window.admin:
                QMessageBox.warning(self, "Admin Error", "No admin user is currently logged in.")
                return

            # Import the password change dialog
            from .password_change_dialog import PasswordChangeDialog

            # Create admin info dictionary
            if isinstance(parent_window.admin, dict):
                admin_info = parent_window.admin
            else:
                admin_info = {
                    'id': parent_window.admin.id,
                    'username': parent_window.admin.username
                }

            # Create and show the dialog
            dialog = PasswordChangeDialog(admin_info, forced_change=False, parent=self)

            def on_password_changed(success):
                if success:
                    # Clear the old password input fields
                    self.current_password_input.clear()
                    self.new_password_input.clear()
                    self.confirm_password_input.clear()
                    logger.info(f"Password changed successfully for admin: {admin_info['username']}")

            dialog.password_changed.connect(on_password_changed)
            dialog.exec_()

        except Exception as e:
            logger.error(f"Error opening password change dialog: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while opening the password change dialog: {str(e)}")

    def open_beacon_management_from_system(self):
        """
        Open beacon management dialog from system maintenance tab.
        """
        try:
            dialog = BeaconManagementDialog(parent=self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error opening beacon management: {str(e)}")
            QMessageBox.critical(self, "Beacon Management Error", f"Error opening beacon management: {str(e)}")

    def test_beacon_detection(self):
        """
        Test beacon detection by opening the testing tab directly.
        """
        try:
            dialog = BeaconManagementDialog(parent=self)
            # Switch to testing tab
            dialog.tab_widget.setCurrentIndex(3)  # Testing tab is index 3
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error opening beacon testing: {str(e)}")
            QMessageBox.critical(self, "Beacon Testing Error", f"Error opening beacon testing: {str(e)}")

    def save_settings(self):
        """
        Save system settings.
        """
        try:
            # Get settings values
            mqtt_host = self.mqtt_host_input.text().strip()
            mqtt_port = self.mqtt_port_input.text().strip()
            auto_start = self.auto_start_checkbox.isChecked()

            # Validate settings
            if not mqtt_host:
                QMessageBox.warning(self, "Validation Error", "Please enter an MQTT broker host.")
                return

            if not mqtt_port.isdigit():
                QMessageBox.warning(self, "Validation Error", "MQTT broker port must be a number.")
                return

            # Create a settings file
            settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.ini")

            with open(settings_path, 'w') as f:
                f.write("[MQTT]\n")
                f.write(f"broker_host = {mqtt_host}\n")
                f.write(f"broker_port = {mqtt_port}\n")
                f.write("\n[System]\n")
                f.write(f"auto_start = {str(auto_start).lower()}\n")

            # Update environment variables
            os.environ['MQTT_BROKER_HOST'] = mqtt_host
            os.environ['MQTT_BROKER_PORT'] = mqtt_port

            QMessageBox.information(self, "Save Settings", "Settings saved successfully.\nSome settings may require an application restart to take effect.")

            # Reload the faculty list after settings change
            self.load_faculty_list()

        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Error saving settings: {str(e)}")

class LogViewerDialog(QDialog):
    """
    Dialog for viewing system logs.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_logs()

    def init_ui(self):
        """
        Initialize the UI components.
        """
        self.setWindowTitle("System Logs")
        self.resize(800, 600)

        # Main layout
        layout = QVBoxLayout()

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.log_text)

        # Controls
        controls_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_logs)
        controls_layout.addWidget(self.refresh_button)

        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        controls_layout.addWidget(self.clear_button)

        controls_layout.addStretch()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        controls_layout.addWidget(self.close_button)

        layout.addLayout(controls_layout)

        self.setLayout(layout)

    def load_logs(self):
        """
        Load and display the system logs.
        """
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "consultease.log")

            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    log_content = f.read()

                # Set the log content
                self.log_text.setText(log_content)

                # Scroll to end
                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.log_text.setTextCursor(cursor)
            else:
                self.log_text.setText("Log file not found.")

        except Exception as e:
            self.log_text.setText(f"Error loading logs: {str(e)}")

    def clear_logs(self):
        """
        Clear the system logs.
        """
        try:
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "consultease.log")

            # Confirm clear
            reply = QMessageBox.warning(
                self,
                "Clear Logs",
                "Are you sure you want to clear all logs?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if os.path.exists(log_path):
                    with open(log_path, 'w') as f:
                        f.write("")

                    self.log_text.setText("")
                    QMessageBox.information(self, "Clear Logs", "Logs cleared successfully.")
                else:
                    QMessageBox.warning(self, "Clear Logs", "Log file not found.")

        except Exception as e:
            QMessageBox.critical(self, "Clear Logs", f"Error clearing logs: {str(e)}")