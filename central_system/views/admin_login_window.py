from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QLineEdit, QFrame, QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon

import os
import logging
from .base_window import BaseWindow
from .admin_account_creation_dialog import AdminAccountCreationDialog

logger = logging.getLogger(__name__)

class AdminLoginWindow(BaseWindow):
    """
    Admin login window for secure access to the admin interface.
    """
    # Signal to notify when an admin is authenticated
    admin_authenticated = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.admin_controller = None  # Will be set by main application
        self.first_time_setup_shown = False  # Flag to prevent multiple setup dialogs
        self.init_ui()

    def set_admin_controller(self, admin_controller):
        """Set the admin controller for first-time setup detection."""
        self.admin_controller = admin_controller

    def init_ui(self):
        """
        Initialize the UI components.
        """
        # Set window properties
        self.setWindowTitle('ConsultEase - Admin Login')

        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Dark header background
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #232323; color: white;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel('Admin Login')
        title_label.setStyleSheet('font-size: 36pt; font-weight: bold; color: white;')
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)

        # Add header to main layout
        main_layout.addWidget(header_frame, 0)

        # Content area - white background
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: #f5f5f5;")
        content_frame_layout = QVBoxLayout(content_frame)
        content_frame_layout.setContentsMargins(50, 50, 50, 50)

        # Create form layout for inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Username input
        username_label = QLabel('Username:')
        username_label.setStyleSheet('font-size: 16pt; font-weight: bold;')
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Enter username')
        self.username_input.setMinimumHeight(50)  # Make touch-friendly
        self.username_input.setProperty("keyboardOnFocus", True)  # Custom property to help keyboard handler
        self.username_input.setStyleSheet('''
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14pt;
            }
            QLineEdit:focus {
                border: 2px solid #4a86e8;
            }
        ''')
        form_layout.addRow(username_label, self.username_input)

        # Password input
        password_label = QLabel('Password:')
        password_label.setStyleSheet('font-size: 16pt; font-weight: bold;')
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Enter password')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(50)  # Make touch-friendly
        self.password_input.setProperty("keyboardOnFocus", True)  # Custom property to help keyboard handler
        self.password_input.setStyleSheet('''
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14pt;
            }
            QLineEdit:focus {
                border: 2px solid #4a86e8;
            }
        ''')
        form_layout.addRow(password_label, self.password_input)

        # Add form layout to content layout
        content_frame_layout.addLayout(form_layout)

        # Add error message label (hidden by default)
        self.error_label = QLabel('')
        self.error_label.setStyleSheet('color: #f44336; font-weight: bold; font-size: 14pt;')
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        content_frame_layout.addWidget(self.error_label)

        # Add spacer
        content_frame_layout.addStretch()

        # Add content to main layout
        main_layout.addWidget(content_frame, 1)

        # Footer with buttons
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background-color: #232323;")
        footer_frame.setMinimumHeight(80)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(50, 10, 50, 10)

        # Back button
        self.back_button = QPushButton('Back')
        self.back_button.setStyleSheet('''
            QPushButton {
                background-color: #808080;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14pt;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #909090;
            }
        ''')
        self.back_button.clicked.connect(self.back_to_login)

        # Login button
        self.login_button = QPushButton('Login')
        self.login_button.setStyleSheet('''
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14pt;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        ''')
        self.login_button.clicked.connect(self.login)

        footer_layout.addWidget(self.back_button)
        footer_layout.addStretch()
        footer_layout.addWidget(self.login_button)

        # Add footer to main layout
        main_layout.addWidget(footer_frame, 0)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Set up keyboard shortcuts
        self.password_input.returnPressed.connect(self.login)
        self.username_input.returnPressed.connect(self.focus_password)

        # Configure tab order for better keyboard navigation
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.login_button)
        self.setTabOrder(self.login_button, self.back_button)

    def clear_login_form(self):
        """
        Clear all login form fields and reset error state.
        This should be called when logging out or when switching away from admin login.
        """
        logger.info("Clearing admin login form")
        
        # Clear all input fields
        self.username_input.clear()
        self.password_input.clear()
        
        # Hide any error messages
        self.error_label.setVisible(False)
        self.error_label.setText('')
        
        # Reset focus to username field
        self.username_input.setFocus()
        
        # Clear any stored login attempt data in the main application
        try:
            if hasattr(self.parent(), '_admin_login_attempts'):
                self.parent()._admin_login_attempts.clear()
                logger.debug("Cleared admin login attempt tracking")
        except Exception as e:
            logger.debug(f"Could not clear login attempt tracking: {e}")

    def reset_form_state(self):
        """
        Reset the form to its initial state.
        """
        self.clear_login_form()
        
        # Reset first-time setup flag if needed
        self.first_time_setup_shown = False
        
        # Ensure the form is ready for new input
        self.username_input.setStyleSheet('''
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14pt;
            }
            QLineEdit:focus {
                border: 2px solid #4a86e8;
            }
        ''')
        
        self.password_input.setStyleSheet('''
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14pt;
            }
            QLineEdit:focus {
                border: 2px solid #4a86e8;
            }
        ''')

    def focus_password(self):
        """
        Focus on the password input field.
        """
        self.password_input.setFocus()

    def show_login_error(self, message):
        """
        Show an error message on the login form with improved user feedback.

        Args:
            message (str): The error message to display.
        """
        self.error_label.setText(message)
        self.error_label.setVisible(True)

        # Only clear the password field for security, keep username for user convenience
        self.password_input.clear()
        self.password_input.setFocus()  # Focus on password field for retry
        
        # Add visual feedback with subtle color change
        self.password_input.setStyleSheet('''
            QLineEdit {
                border: 2px solid #f44336;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14pt;
                background-color: #ffeaea;
            }
            QLineEdit:focus {
                border: 2px solid #d32f2f;
                background-color: white;
            }
        ''')
        
        # Reset the styling after a short delay
        QTimer.singleShot(3000, self._reset_password_field_styling)

    def _reset_password_field_styling(self):
        """
        Reset the password field styling to normal.
        """
        self.password_input.setStyleSheet('''
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14pt;
            }
            QLineEdit:focus {
                border: 2px solid #4a86e8;
            }
        ''')

    def login(self):
        """
        Handle login button click with improved validation and user feedback.
        """
        # Hide any previous error message
        self.error_label.setVisible(False)

        # Get username and password
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Validate inputs with better user feedback
        if not username:
            self.show_login_error('Please enter a username')
            self.username_input.setFocus()
            self.username_input.setStyleSheet('''
                QLineEdit {
                    border: 2px solid #f44336;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 14pt;
                    background-color: #ffeaea;
                }
                QLineEdit:focus {
                    border: 2px solid #4a86e8;
                    background-color: white;
                }
            ''')
            QTimer.singleShot(3000, lambda: self.username_input.setStyleSheet('''
                QLineEdit {
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-size: 14pt;
                }
                QLineEdit:focus {
                    border: 2px solid #4a86e8;
                }
            '''))
            return

        if not password:
            self.show_login_error('Please enter a password')
            self.password_input.setFocus()
            return

        # Disable login button temporarily to prevent spam clicking
        self.login_button.setEnabled(False)
        self.login_button.setText('Authenticating...')
        
        # Re-enable button after a short delay
        QTimer.singleShot(2000, self._reset_login_button)

        # Emit the signal with the credentials as a tuple
        self.admin_authenticated.emit((username, password))

    def _reset_login_button(self):
        """
        Reset the login button to its normal state.
        """
        self.login_button.setEnabled(True)
        self.login_button.setText('Login')

    def back_to_login(self):
        """
        Go back to the login screen and clear the form.
        """
        self.clear_login_form()
        self.change_window.emit('login', None)

    def showEvent(self, event):
        """
        Override showEvent to check for first-time setup and prepare the form.
        """
        super().showEvent(event)
        
        # Clear the form when showing the window (important for logout scenario)
        self.clear_login_form()

        # Only check for first-time setup once to prevent multiple dialogs
        if self.first_time_setup_shown:
            logger.info("First-time setup already shown, skipping check")
            return

        # Check for first-time setup
        try:
            if self.admin_controller and self.admin_controller.is_first_time_setup():
                logger.info("First-time setup detected, showing setup dialog")
                self.first_time_setup_shown = True  # Set flag to prevent multiple dialogs
                self.show_first_time_setup()
            else:
                if self.admin_controller:
                    logger.info("Existing admin accounts found, showing normal login")
                else:
                    logger.warning("AdminController not set, cannot check first-time setup")
        except Exception as e:
            logger.error(f"Error checking first-time setup: {str(e)}")
            # If there's an error, assume normal login
            logger.info("Error occurred, defaulting to normal login")

    def show_first_time_setup(self):
        """
        Show the first-time setup dialog for creating an admin account.
        """
        try:
            logger.info("🎭 Creating AdminAccountCreationDialog...")
            dialog = AdminAccountCreationDialog(self)
            if self.admin_controller:
                dialog.set_admin_controller(self.admin_controller)  # Pass the controller
            else:
                logger.error("AdminController not available in AdminLoginWindow when showing setup dialog.")
                QMessageBox.critical(self, "Error", "Critical error: Admin controller not found. Cannot proceed with setup.")
                return
                
            logger.info("✅ AdminAccountCreationDialog created successfully")

            logger.info("🔗 Connecting account_created signal...")
            dialog.account_created.connect(self.handle_account_created)
            logger.info("✅ Signal connected successfully")

            logger.info("📱 Showing first-time setup dialog...")
            # Show the dialog
            result = dialog.exec_()
            logger.info(f"📋 Dialog result: {result}")

            if result == dialog.Rejected:
                logger.info("❌ User cancelled first-time setup")
                # User cancelled - show message and allow manual login attempt
                QMessageBox.information(
                    self,
                    "Setup Cancelled",
                    "First-time setup was cancelled.\n\n"
                    "You can still try to login if an admin account exists, "
                    "or restart the application to run setup again."
                )
            else:
                logger.info("✅ First-time setup dialog completed")

        except Exception as e:
            logger.error(f"❌ Error showing first-time setup dialog: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            QMessageBox.critical(
                self,
                "Setup Error",
                f"Failed to show account creation dialog: {str(e)}\n\n"
                "Please try logging in manually or restart the application."
            )

    def handle_account_created(self, admin_info):
        """
        Handle successful account creation from the first-time setup dialog.

        Args:
            admin_info (dict): Information about the created admin account
        """
        try:
            logger.info(f"Admin account created successfully: {admin_info['username']}")

            # Refresh the admin controller cache
            if self.admin_controller:
                self.admin_controller.check_admin_accounts_exist(force_refresh=True)

            # Automatically authenticate the newly created admin
            # Emit the authentication signal to proceed to dashboard
            self.admin_authenticated.emit((admin_info['username'], None))  # Password not needed for auto-login

        except Exception as e:
            logger.error(f"Error handling account creation: {e}")
            QMessageBox.critical(
                self,
                "Login Error",
                f"Account was created but automatic login failed: {str(e)}\n\n"
                "Please try logging in manually with your new credentials."
            )