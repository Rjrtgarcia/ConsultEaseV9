from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QLineEdit, QFrame, QFormLayout, QTextEdit, QCheckBox,
                               QProgressBar, QMessageBox, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
import re
import logging

logger = logging.getLogger(__name__)

class AdminAccountCreationDialog(QDialog):
    """
    User-friendly dialog for creating the first admin account.
    Designed for touchscreen interface with clear instructions and validation.
    """

    # Signal emitted when account is successfully created
    account_created = pyqtSignal(dict)  # Emits admin info dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("ConsultEase - First Time Setup")
        self.setMinimumSize(800, 700)
        self.admin_controller = None  # Initialize admin_controller
        self.init_ui()

    def set_admin_controller(self, admin_controller):
        """Set the admin controller instance."""
        self.admin_controller = admin_controller

    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Create scrollable content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # Header section
        self.create_header_section(content_layout)

        # Instructions section
        self.create_instructions_section(content_layout)

        # Form section
        self.create_form_section(content_layout)

        # Password requirements section
        self.create_password_requirements_section(content_layout)

        # Progress section
        self.create_progress_section(content_layout)

        # Buttons section
        self.create_buttons_section(content_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Apply styling
        self.apply_styling()

    def create_header_section(self, layout):
        """Create the header section with title and icon."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignCenter)

        # Title
        title_label = QLabel("🔧 First Time Setup")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Create Your Admin Account")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_frame)

    def create_instructions_section(self, layout):
        """Create the instructions section."""
        instructions_frame = QFrame()
        instructions_frame.setObjectName("instructionsFrame")
        instructions_layout = QVBoxLayout(instructions_frame)

        instructions_text = QLabel(
            "Welcome to ConsultEase! No admin accounts were found in the system.\n"
            "Please create your first admin account to access the admin dashboard.\n\n"
            "This account will have full administrative privileges and can create additional admin accounts later."
        )
        instructions_text.setObjectName("instructionsText")
        instructions_text.setWordWrap(True)
        instructions_text.setAlignment(Qt.AlignCenter)
        instructions_layout.addWidget(instructions_text)

        layout.addWidget(instructions_frame)

    def create_form_section(self, layout):
        """Create the form input section."""
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)

        # Username field
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        self.username_input = QLineEdit()
        self.username_input.setObjectName("inputField")
        self.username_input.setPlaceholderText("Enter admin username (e.g., admin)")
        self.username_input.setMinimumHeight(50)
        self.username_input.textChanged.connect(self.validate_form)
        form_layout.addRow(username_label, self.username_input)

        # Password field
        password_label = QLabel("Password:")
        password_label.setObjectName("fieldLabel")
        self.password_input = QLineEdit()
        self.password_input.setObjectName("inputField")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter secure password")
        self.password_input.setMinimumHeight(50)
        self.password_input.textChanged.connect(self.validate_form)
        form_layout.addRow(password_label, self.password_input)

        # Confirm password field
        confirm_label = QLabel("Confirm Password:")
        confirm_label.setObjectName("fieldLabel")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setObjectName("inputField")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setMinimumHeight(50)
        self.confirm_password_input.textChanged.connect(self.validate_form)
        form_layout.addRow(confirm_label, self.confirm_password_input)

        # Note: Email field removed as Admin model doesn't support email
        # The Admin model only has: username, password_hash, salt, is_active, force_password_change

        # Show password checkbox
        self.show_password_checkbox = QCheckBox("Show passwords")
        self.show_password_checkbox.setObjectName("showPasswordCheckbox")
        self.show_password_checkbox.toggled.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_checkbox)

        layout.addWidget(form_frame)

    def create_password_requirements_section(self, layout):
        """Create the password requirements section."""
        requirements_frame = QFrame()
        requirements_frame.setObjectName("requirementsFrame")
        requirements_layout = QVBoxLayout(requirements_frame)

        requirements_title = QLabel("Password Requirements:")
        requirements_title.setObjectName("requirementsTitle")
        requirements_layout.addWidget(requirements_title)

        # Password requirements list
        self.requirements_labels = {}
        requirements = [
            ("length", "At least 8 characters long"),
            ("uppercase", "Contains uppercase letters (A-Z)"),
            ("lowercase", "Contains lowercase letters (a-z)"),
            ("numbers", "Contains numbers (0-9)"),
            ("special", "Contains special characters (!@#$%^&*)"),
            ("match", "Passwords match")
        ]

        for req_id, req_text in requirements:
            req_label = QLabel(f"❌ {req_text}")
            req_label.setObjectName("requirementLabel")
            self.requirements_labels[req_id] = req_label
            requirements_layout.addWidget(req_label)

        layout.addWidget(requirements_frame)

    def create_progress_section(self, layout):
        """Create the progress section."""
        self.progress_frame = QFrame()
        self.progress_frame.setObjectName("progressFrame")
        self.progress_frame.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_frame)

        self.progress_label = QLabel("Creating admin account...")
        self.progress_label.setObjectName("progressLabel")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setMinimumHeight(30)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(self.progress_frame)

    def create_buttons_section(self, layout):
        """Create the buttons section."""
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setSpacing(20)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setMinimumHeight(60)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        # Create account button
        self.create_button = QPushButton("Create Admin Account")
        self.create_button.setObjectName("createButton")
        self.create_button.setMinimumHeight(60)
        self.create_button.setEnabled(False)
        self.create_button.clicked.connect(self.create_account)
        buttons_layout.addWidget(self.create_button)

        layout.addWidget(buttons_frame)

    def apply_styling(self):
        """Apply comprehensive styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            #headerFrame {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 10px;
            }

            #titleLabel {
                font-size: 28pt;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
            }

            #subtitleLabel {
                font-size: 16pt;
                color: #ecf0f1;
            }

            #instructionsFrame {
                background-color: #e8f4fd;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 15px;
            }

            #instructionsText {
                font-size: 14pt;
                color: #2c3e50;
                line-height: 1.4;
            }

            #formFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                border: 1px solid #ddd;
            }

            #fieldLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #2c3e50;
            }

            #inputField {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px;
                font-size: 14pt;
                background-color: white;
            }

            #inputField:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }

            #showPasswordCheckbox {
                font-size: 12pt;
                color: #7f8c8d;
            }

            #requirementsFrame {
                background-color: #fefefe;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }

            #requirementsTitle {
                font-size: 14pt;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }

            #requirementLabel {
                font-size: 12pt;
                margin: 3px 0;
            }

            #progressFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
            }

            #progressLabel {
                font-size: 14pt;
                color: #856404;
                margin-bottom: 10px;
            }

            #progressBar {
                border-radius: 15px;
                background-color: #e9ecef;
                border: none;
            }

            #progressBar::chunk {
                background-color: #28a745;
                border-radius: 15px;
            }

            #cancelButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px 30px;
                min-width: 150px;
            }

            #cancelButton:hover {
                background-color: #5a6268;
            }

            #createButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px 30px;
                min-width: 200px;
            }

            #createButton:hover {
                background-color: #218838;
            }

            #createButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)

    def toggle_password_visibility(self, checked):
        """Toggle password field visibility."""
        echo_mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.password_input.setEchoMode(echo_mode)
        self.confirm_password_input.setEchoMode(echo_mode)

    def validate_form(self):
        """Validate the form and update UI accordingly."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validate username
        username_valid = len(username) >= 3 and username.isalnum()

        # Validate password requirements
        requirements_met = self.check_password_requirements(password, confirm_password)

        # Update create button state
        all_valid = username_valid and all(requirements_met.values())
        self.create_button.setEnabled(all_valid)

        return all_valid

    def check_password_requirements(self, password, confirm_password):
        """Check password requirements and update UI."""
        requirements = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            'match': password == confirm_password and len(password) > 0
        }

        # Update requirement labels
        for req_id, met in requirements.items():
            label = self.requirements_labels[req_id]
            if met:
                label.setText(f"✅ {label.text()[2:]}")
                label.setStyleSheet("color: #28a745;")
            else:
                label.setText(f"❌ {label.text()[2:]}")
                label.setStyleSheet("color: #dc3545;")

        return requirements

    def create_account(self):
        """Create the admin account using the AdminController."""
        try:
            if not self.admin_controller:
                self.show_error("Critical error: Admin controller not available. Cannot create account.")
                return

            # Show progress
            self.progress_frame.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.create_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

            # Get form data
            username = self.username_input.text().strip()
            password = self.password_input.text()

            self.progress_label.setText("Creating admin account...")
            
            # Use AdminController to create the account
            result = self.admin_controller.create_admin_account(username, password, force_password_change=False)

            if result.get('success'):
                self.progress_label.setText("Account created successfully!")
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)

                logger.info(f"First admin account created successfully: {username}")

                # Emit success signal with admin info
                admin_info = result.get('admin')
                if not admin_info:
                     admin_info = {'username': username} # Fallback if admin key is missing

                # Show success message
                QTimer.singleShot(1000, lambda: self.show_success_and_close(admin_info))
            else:
                error_message = result.get('error', "An unknown error occurred.")
                self.show_error(f"Failed to create account: {error_message}")

        except Exception as e:
            logger.error(f"Error creating admin account: {e}")
            self.show_error(f"Failed to create admin account: {str(e)}")

    def show_success_and_close(self, admin_info):
        """Show success message and close dialog."""
        QMessageBox.information(
            self,
            "Success",
            f"Admin account '{admin_info['username']}' created successfully!\n\n"
            "You will now be logged into the admin dashboard."
        )

        # Emit the account created signal
        self.account_created.emit(admin_info)
        self.accept()

    def show_error(self, message):
        """Show error message and reset UI."""
        self.progress_frame.setVisible(False)
        self.create_button.setEnabled(self.validate_form())
        self.cancel_button.setEnabled(True)

        QMessageBox.critical(self, "Error", message)
