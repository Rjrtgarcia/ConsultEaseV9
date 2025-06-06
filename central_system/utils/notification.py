"""
Notification utility module.
Provides standardized notification and loading indicator functionality.
"""

from PyQt5.QtWidgets import (QMessageBox, QDialog, QVBoxLayout, QLabel, 
                            QProgressBar, QPushButton, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import logging

# Set up logging
logger = logging.getLogger(__name__)

class NotificationManager:
    """
    Utility class for standardized notifications and message boxes.
    """
    
    # Notification types
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    
    # Notification styles
    STYLES = {
        INFO: {
            "color": "#0d3b66",
            "bg_color": "#e3f2fd",
            "icon": QMessageBox.Information
        },
        SUCCESS: {
            "color": "#2e7d32",
            "bg_color": "#e8f5e9",
            "icon": QMessageBox.Information
        },
        WARNING: {
            "color": "#f57c00",
            "bg_color": "#fff3e0",
            "icon": QMessageBox.Warning
        },
        ERROR: {
            "color": "#c62828",
            "bg_color": "#ffebee",
            "icon": QMessageBox.Critical
        }
    }
    
    @staticmethod
    def show_message(parent, title, message, message_type=INFO):
        """
        Show a standardized message box.
        
        Args:
            parent: Parent widget
            title (str): Message title
            message (str): Message content
            message_type (str): Message type (info, success, warning, error)
        """
        # Get style for message type
        style = NotificationManager.STYLES.get(message_type, NotificationManager.STYLES[NotificationManager.INFO])
        
        # Create message box
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(f"<b>{title}</b>")
        msg_box.setInformativeText(message)
        msg_box.setIcon(style["icon"])
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Apply styling
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {style["bg_color"]};
            }}
            QLabel {{
                color: {style["color"]};
                font-size: 12pt;
            }}
            QPushButton {{
                background-color: {style["color"]};
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {style["color"]};
                opacity: 0.9;
            }}
        """)
        
        # Show message box
        return msg_box.exec_()
    
    @staticmethod
    def show_confirmation(parent, title, message, yes_text="Yes", no_text="No"):
        """
        Show a standardized confirmation dialog.
        
        Args:
            parent: Parent widget
            title (str): Dialog title
            message (str): Dialog message
            yes_text (str): Text for the Yes button
            no_text (str): Text for the No button
            
        Returns:
            bool: True if Yes was clicked, False otherwise
        """
        # Create confirmation dialog
        confirm_box = QMessageBox(parent)
        confirm_box.setWindowTitle(title)
        confirm_box.setText(f"<b>{title}</b>")
        confirm_box.setInformativeText(message)
        confirm_box.setIcon(QMessageBox.Question)
        
        # Create custom buttons
        yes_button = confirm_box.addButton(yes_text, QMessageBox.YesRole)
        no_button = confirm_box.addButton(no_text, QMessageBox.NoRole)
        
        # Apply styling
        confirm_box.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #0d3b66;
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
        
        # Show dialog and get result
        confirm_box.exec_()
        
        # Return True if Yes was clicked
        return confirm_box.clickedButton() == yes_button


class LoadingDialog(QDialog):
    """
    Loading indicator dialog with progress bar.
    """
    # Signal to update progress
    progress_updated = pyqtSignal(int)
    
    def __init__(self, parent=None, title="Loading", message="Please wait...", cancelable=False):
        """
        Initialize the loading dialog.
        
        Args:
            parent: Parent widget
            title (str): Dialog title
            message (str): Dialog message
            cancelable (bool): Whether the dialog can be canceled
        """
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setFixedSize(400, 150)
        self.setModal(True)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("font-size: 14pt; color: #0d3b66;")
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #0d3b66;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Cancel button (if cancelable)
        if cancelable:
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.cancel_button.clicked.connect(self.reject)
            layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)
        
        # Connect progress signal
        self.progress_updated.connect(self.update_progress)
        
        # Apply dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 10px;
            }
        """)
    
    def update_progress(self, value):
        """
        Update the progress bar value.
        
        Args:
            value (int): Progress value (0-100)
        """
        self.progress_bar.setValue(value)
        QApplication.processEvents()  # Ensure UI updates
    
    def update_message(self, message):
        """
        Update the dialog message.
        
        Args:
            message (str): New message
        """
        self.message_label.setText(message)
        QApplication.processEvents()  # Ensure UI updates
    
    @staticmethod
    def show_loading(parent, operation_func, title="Loading", message="Please wait...", cancelable=False):
        """
        Show loading dialog while executing an operation.
        
        Args:
            parent: Parent widget
            operation_func: Function to execute (should accept a progress_callback parameter)
            title (str): Dialog title
            message (str): Dialog message
            cancelable (bool): Whether the dialog can be canceled
            
        Returns:
            The result of operation_func
        """
        # Create loading dialog
        loading_dialog = LoadingDialog(parent, title, message, cancelable)
        
        # Result container
        result = [None]
        error = [None]
        
        # Progress callback
        def progress_callback(value, status_message=None):
            loading_dialog.progress_updated.emit(value)
            if status_message:
                loading_dialog.update_message(status_message)
        
        # Operation thread
        def run_operation():
            try:
                result[0] = operation_func(progress_callback)
            except Exception as e:
                logger.error(f"Error in operation: {str(e)}")
                error[0] = e
            finally:
                # Close dialog when done
                loading_dialog.accept()
        
        # Use timer to start operation after dialog is shown
        QTimer.singleShot(100, run_operation)
        
        # Show dialog (blocks until operation completes)
        loading_dialog.exec_()
        
        # Raise any error that occurred
        if error[0]:
            raise error[0]
        
        # Return operation result
        return result[0]
