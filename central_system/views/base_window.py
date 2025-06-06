from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QShortcut, QPushButton,
                             QStatusBar, QApplication, QLineEdit, QTextEdit,
                             QPlainTextEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QEvent
from PyQt5.QtGui import QKeySequence, QIcon
import logging
import sys
import os
import subprocess

# Add parent directory to path to help with imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import utilities
from central_system.utils.icons import IconProvider, Icons  # Import IconProvider and Icons

logger = logging.getLogger(__name__)

class BaseWindow(QMainWindow):
    """
    Base window class for ConsultEase.
    All windows should inherit from this class.
    """
    # Signal for changing windows
    change_window = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Basic window setup
        self.setWindowTitle("ConsultEase")
        self.setGeometry(100, 100, 1024, 768) # Default size

        # Set application icon (use helper from icons module)
        app_icon = IconProvider.get_icon(Icons.APP_ICON if hasattr(Icons, 'APP_ICON') else "app", QSize(64, 64))
        if app_icon and not app_icon.isNull():
            self.setWindowIcon(app_icon)
        else:
            logger.warning("Could not load application icon.")

        # Initialize UI (must be called after basic setup)
        self.init_ui()

        # Add F11 shortcut to toggle fullscreen
        self.fullscreen_shortcut = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

        # Store fullscreen state preference (will be set by ConsultEaseApp)
        self.fullscreen = False

    def init_ui(self):
        """
        Initialize the UI components.
        This method should be overridden by subclasses.
        """
        # Set window properties
        self.setMinimumSize(800, 480)  # Minimum size for Raspberry Pi 7" touchscreen
        self.apply_touch_friendly_style()

        # Add status bar
        self.statusBar().setStyleSheet("QStatusBar { border-top: 1px solid #cccccc; }")

        # Center window on screen
        self.center()

    def apply_touch_friendly_style(self):
        """
        Apply touch-friendly styles to the application
        """
        self.setStyleSheet('''
            /* General styles */
            QWidget {
                font-size: 14pt;
            }

            QMainWindow {
                background-color: #f0f0f0;
            }

            /* Touch-friendly buttons */
            QPushButton {
                min-height: 50px;
                padding: 10px 20px;
                font-size: 14pt;
                border-radius: 5px;
                background-color: #4a86e8;
                color: white;
            }

            QPushButton:hover {
                background-color: #5a96f8;
            }

            QPushButton:pressed {
                background-color: #3a76d8;
            }

            /* Touch-friendly input fields */
            QLineEdit, QTextEdit, QComboBox {
                min-height: 40px;
                padding: 5px 10px;
                font-size: 14pt;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }

            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #4a86e8;
            }

            /* Table headers and cells */
            QTableWidget {
                font-size: 12pt;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 8px;
                font-size: 12pt;
                font-weight: bold;
            }

            /* Tabs for better touch */
            QTabBar::tab {
                min-width: 120px;
                min-height: 40px;
                padding: 8px 16px;
                font-size: 14pt;
            }

            /* Dialog buttons */
            QDialogButtonBox > QPushButton {
                min-width: 100px;
                min-height: 40px;
            }
        ''')
        logger.info("Applied touch-optimized UI settings")

    def center(self):
        """
        Center the window on the screen.
        """
        # Get the screen geometry
        screen = QApplication.desktop().screenGeometry()
        # Get the window geometry
        window = self.geometry()
        # Calculate the center position
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        # Move the window to the center
        self.move(x, y)

    def keyPressEvent(self, event):
        """
        Handle key press events.
        """
        # Handle Escape key to exit fullscreen
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
            self.center()
        else:
            super().keyPressEvent(event)

    def toggle_fullscreen(self):
        """
        Toggle between fullscreen and normal window state.
        """
        if self.isFullScreen():
            logger.info("Exiting fullscreen mode")
            self.showNormal()
            # Re-center after exiting fullscreen
            self.center()
        else:
            logger.info("Entering fullscreen mode")
            self.showFullScreen()

    def showEvent(self, event):
        """
        Override showEvent to apply fullscreen if needed.
        """
        # This ensures the window respects the initial fullscreen setting
        # The `fullscreen` flag is set by ConsultEaseApp
        if hasattr(self, 'fullscreen') and self.fullscreen:
            if not self.isFullScreen(): # Avoid toggling if already fullscreen
                self.showFullScreen()

        super().showEvent(event)