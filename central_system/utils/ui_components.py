"""
Enhanced UI component library for ConsultEase.
Provides modern, reusable UI components optimized for performance, accessibility, and user experience.
"""
import logging
from typing import Optional, Callable, Any, Dict, List
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
    QLineEdit, QGraphicsDropShadowEffect, QSizePolicy, QSpacerItem,
    QProgressBar, QMessageBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, QSize, QTimer, QCoreApplication
from PyQt5.QtGui import QColor, QPalette, QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut

from .icons import IconProvider, Icons
from .ui_performance import smart_widget_update, get_widget_state_manager
from .code_quality import safe_operation, OperationResult

logger = logging.getLogger(__name__)

class ModernButton(QPushButton):
    """
    Modern button with consistent styling, touch-friendly size, and icons.
    """

    def __init__(self, text="", icon_name=None, primary=False, danger=False, parent=None):
        """
        Initialize a modern button.

        Args:
            text (str): Button text
            icon_name (str, optional): Icon name from Icons class
            primary (bool): Whether this is a primary button (more prominent)
            danger (bool): Whether this is a danger/destructive button
            parent: Parent widget
        """
        super(ModernButton, self).__init__(text, parent)

        # Set minimum size for touch-friendliness
        self.setMinimumSize(120, 48)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        # Configure style
        if primary:
            self.setObjectName("primary_button")
        elif danger:
            self.setObjectName("danger_button")

        # Add icon if specified
        if icon_name:
            self.setIcon(IconProvider.get_button_icon(icon_name))
            self.setIconSize(QSize(24, 24))

class IconButton(QPushButton):
    """
    Icon-only button for toolbar-like functionality.
    """

    def __init__(self, icon_name, tooltip="", parent=None):
        """
        Initialize an icon button.

        Args:
            icon_name (str): Icon name from Icons class
            tooltip (str): Tooltip text
            parent: Parent widget
        """
        super(IconButton, self).__init__(parent)

        # Set fixed size for consistent layout
        self.setFixedSize(48, 48)

        # Add icon
        self.setIcon(IconProvider.get_button_icon(icon_name))
        self.setIconSize(QSize(32, 32))

        # Set tooltip
        if tooltip:
            self.setToolTip(tooltip)

        # Flat style for icon buttons
        self.setFlat(True)


class AccessibleButton(ModernButton):
    """
    Enhanced button with accessibility features and keyboard navigation.
    """

    def __init__(self, text="", icon_name=None, primary=False, danger=False,
                 shortcut=None, tooltip=None, parent=None):
        """
        Initialize an accessible button with enhanced features.

        Args:
            text (str): Button text
            icon_name (str, optional): Icon name from Icons class
            primary (bool): Whether this is a primary button
            danger (bool): Whether this is a danger/destructive button
            shortcut (str, optional): Keyboard shortcut (e.g., "Ctrl+S")
            tooltip (str, optional): Tooltip text
            parent: Parent widget
        """
        super().__init__(text, icon_name, primary, danger, parent)

        # Set tooltip if provided
        if tooltip:
            self.setToolTip(tooltip)

        # Set keyboard shortcut if provided
        if shortcut:
            self.setShortcut(QKeySequence(shortcut))

        # Enhanced accessibility
        self.setAccessibleName(text or tooltip or "Button")
        self.setAccessibleDescription(tooltip or f"Button: {text}")

        # Focus policy for keyboard navigation
        self.setFocusPolicy(Qt.StrongFocus)


class LoadingButton(ModernButton):
    """
    Button that shows loading state during operations.
    """

    def __init__(self, text="", icon_name=None, primary=False, danger=False, parent=None):
        """Initialize loading button."""
        super().__init__(text, icon_name, primary, danger, parent)

        self.original_text = text
        self.is_loading = False
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_loading_text)
        self.loading_dots = 0

    def start_loading(self, loading_text="Loading"):
        """Start loading state."""
        if not self.is_loading:
            self.is_loading = True
            self.setEnabled(False)
            self.loading_text = loading_text
            self.loading_dots = 0
            self.loading_timer.start(500)  # Update every 500ms
            self._update_loading_text()

    def stop_loading(self):
        """Stop loading state."""
        if self.is_loading:
            self.is_loading = False
            self.setEnabled(True)
            self.loading_timer.stop()
            self.setText(self.original_text)

    def _update_loading_text(self):
        """Update loading text with animated dots."""
        dots = "." * (self.loading_dots % 4)
        self.setText(f"{self.loading_text}{dots}")
        self.loading_dots += 1


class StatusIndicator(QLabel):
    """
    Visual status indicator with color coding and animations.
    """

    # Status types
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    LOADING = "loading"

    def __init__(self, status=INFO, text="", parent=None):
        """
        Initialize status indicator.

        Args:
            status (str): Status type (success, warning, error, info, loading)
            text (str): Status text
            parent: Parent widget
        """
        super().__init__(text, parent)

        self.current_status = status
        self.status_colors = {
            self.SUCCESS: "#27ae60",
            self.WARNING: "#f39c12",
            self.ERROR: "#e74c3c",
            self.INFO: "#3498db",
            self.LOADING: "#9b59b6"
        }

        # Set initial appearance
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(30)
        self.update_status(status, text)

    def update_status(self, status, text=""):
        """Update status and text."""
        self.current_status = status
        if text:
            self.setText(text)

        # Update styling based on status
        color = self.status_colors.get(status, self.status_colors[self.INFO])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: bold;
            }}
        """)

        # Add loading animation if needed
        if status == self.LOADING:
            self._start_loading_animation()
        else:
            self._stop_loading_animation()

    def _start_loading_animation(self):
        """Start loading animation."""
        if not hasattr(self, 'loading_timer'):
            self.loading_timer = QTimer()
            self.loading_timer.timeout.connect(self._animate_loading)

        self.loading_timer.start(200)

    def _stop_loading_animation(self):
        """Stop loading animation."""
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()

    def _animate_loading(self):
        """Animate loading indicator."""
        current_text = self.text()
        if current_text.endswith("..."):
            self.setText(current_text[:-3])
        elif current_text.endswith(".."):
            self.setText(current_text + ".")
        elif current_text.endswith("."):
            self.setText(current_text + ".")
        else:
            self.setText(current_text + ".")


class ProgressCard(QFrame):
    """
    Card component showing progress with status and description.
    """

    def __init__(self, title="", description="", progress=0, parent=None):
        """
        Initialize progress card.

        Args:
            title (str): Card title
            description (str): Card description
            progress (int): Progress percentage (0-100)
            parent: Parent widget
        """
        super().__init__(parent)

        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setObjectName("progress_card")

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("card_title")
        layout.addWidget(self.title_label)

        # Description
        self.description_label = QLabel(description)
        self.description_label.setObjectName("card_description")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(progress)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Status indicator
        self.status_indicator = StatusIndicator(StatusIndicator.INFO, "Ready")
        layout.addWidget(self.status_indicator)

        # Apply styling
        self._apply_styling()

    def update_progress(self, progress, status_text="", status_type=StatusIndicator.INFO):
        """Update progress and status."""
        self.progress_bar.setValue(progress)
        if status_text:
            self.status_indicator.update_status(status_type, status_text)

    def set_title(self, title):
        """Set card title."""
        self.title_label.setText(title)

    def set_description(self, description):
        """Set card description."""
        self.description_label.setText(description)

    def _apply_styling(self):
        """Apply card styling."""
        self.setStyleSheet("""
            QFrame#progress_card {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QLabel#card_title {
                font-size: 14pt;
                font-weight: bold;
                color: #2c3e50;
            }
            QLabel#card_description {
                font-size: 11pt;
                color: #7f8c8d;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)

class FacultyCard(QFrame):
    """
    Card widget displaying faculty information with availability status.
    """

    # Signal emitted when the card is clicked
    clicked = pyqtSignal(dict)

    def __init__(self, faculty_data, parent=None):
        """
        Initialize a faculty card with performance optimizations.

        Args:
            faculty_data (dict): Faculty information (id, name, department, available, etc.)
            parent: Parent widget
        """
        super(FacultyCard, self).__init__(parent)

        self.faculty_data = faculty_data
        self.widget_state_manager = get_widget_state_manager()

        # Set appropriate object name based on availability
        object_name = "faculty_card_available" if faculty_data.get("available", False) else "faculty_card_unavailable"
        self.widget_state_manager.update_property(
            self, "object_name", object_name,
            lambda: self.setObjectName(object_name)
        )

        # Set fixed size (optimized for Raspberry Pi touchscreen)
        self.setMinimumSize(280, 180)
        self.setMaximumSize(280, 220)

        # Add shadow effect (lighter for better performance)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)  # Reduced for better performance
        shadow.setColor(QColor(0, 0, 0, 60))  # Lighter shadow
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Set up the layout
        self._setup_ui()

        # Make clickable
        self.setCursor(Qt.PointingHandCursor)

    def _setup_ui(self):
        """Set up the card UI layout with improved sizing and spacing."""
        # Set fixed width and minimum height for consistent card size
        self.setFixedWidth(280)  # Wider to accommodate longer faculty names
        self.setMinimumHeight(180)

        # Set size policy to prevent stretching
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)  # Proper margins for visual separation
        layout.setSpacing(8)

        # Faculty name (bold, larger font for better readability)
        self.name_label = QLabel(self.faculty_data.get("name", "Unknown Faculty"))
        self.name_label.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            color: #2c3e50;
            border: none;
            padding: 0;
            margin: 0;
        """)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.name_label)

        # Department with improved styling
        dept_layout = QHBoxLayout()
        dept_icon = QLabel()
        dept_icon.setPixmap(IconProvider.get_icon(Icons.FACULTY).pixmap(QSize(14, 14)))
        dept_label = QLabel(self.faculty_data.get("department", "Department"))
        dept_label.setStyleSheet("""
            font-size: 12pt;
            color: #7f8c8d;
            border: none;
            padding: 0;
            margin: 0;
        """)
        dept_layout.addWidget(dept_icon)
        dept_layout.addWidget(dept_label)
        dept_layout.addStretch()
        layout.addLayout(dept_layout)

        # Status with colored dot and text (no borders as per user preference)
        status_layout = QHBoxLayout()
        status_text = "Available" if self.faculty_data.get("available", False) else "Unavailable"

        # Colored status dot without border
        status_dot = QLabel("●")
        if self.faculty_data.get("available", False):
            status_dot.setStyleSheet("font-size: 14pt; color: #27ae60; border: none;")
            status_color = "#27ae60"
        else:
            status_dot.setStyleSheet("font-size: 14pt; color: #e74c3c; border: none;")
            status_color = "#e74c3c"

        # Status text without border
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            font-size: 12pt;
            color: {status_color};
            border: none;
            padding: 0;
            margin: 0;
            font-weight: 500;
        """)

        status_layout.addWidget(status_dot)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Add room information if available
        if "room" in self.faculty_data and self.faculty_data["room"]:
            room_layout = QHBoxLayout()
            room_label = QLabel(f"Room: {self.faculty_data['room']}")
            room_label.setStyleSheet("""
                font-size: 11pt;
                color: #95a5a6;
                border: none;
                padding: 0;
                margin: 0;
            """)
            room_layout.addWidget(room_label)
            room_layout.addStretch()
            layout.addLayout(room_layout)

        # Add spacing
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Request button (only enabled if faculty is available)
        self.request_button = ModernButton("Request Consultation", icon_name=Icons.MESSAGE, primary=True)
        self.request_button.setEnabled(self.faculty_data.get("available", False))
        layout.addWidget(self.request_button)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super(FacultyCard, self).mousePressEvent(event)
        self.clicked.emit(self.faculty_data)

    def enterEvent(self, event):
        """Handle mouse enter events with subtle hover effect."""
        # Create a scale animation
        self._animate_scale(1.03)
        super(FacultyCard, self).enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave events."""
        # Create a scale animation back to normal
        self._animate_scale(1.0)
        super(FacultyCard, self).leaveEvent(event)

    def _animate_scale(self, scale_factor):
        """
        Animate the card scaling.

        Args:
            scale_factor (float): Target scale factor
        """
        # Store original size for animation
        original_size = self.size()
        target_width = int(original_size.width() * scale_factor)
        target_height = int(original_size.height() * scale_factor)

        # Create the animation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(100)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # Calculate centered position
        pos = self.pos()
        width_diff = target_width - original_size.width()
        height_diff = target_height - original_size.height()

        # Set start and end geometries
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRect(
            pos.x() - width_diff // 2,
            pos.y() - height_diff // 2,
            target_width,
            target_height
        ))

        # Start the animation
        self.animation.start()

class ModernSearchBox(QWidget):
    """
    Modern search input with clear button and search icon.
    """

    # Signal emitted when search text changes
    search_changed = pyqtSignal(str)

    def __init__(self, placeholder="Search...", parent=None):
        """
        Initialize a modern search box.

        Args:
            placeholder (str): Placeholder text
            parent: Parent widget
        """
        super(ModernSearchBox, self).__init__(parent)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search icon
        self.search_icon = QLabel()
        self.search_icon.setPixmap(IconProvider.get_icon(Icons.SEARCH).pixmap(QSize(16, 16)))
        self.search_icon.setFixedSize(36, 48)
        layout.addWidget(self.search_icon)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.setMinimumHeight(48)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input)

        # Clear button
        self.clear_button = IconButton(Icons.CANCEL, "Clear search")
        self.clear_button.setFixedSize(36, 48)
        self.clear_button.clicked.connect(self.clear)
        self.clear_button.hide()  # Initially hidden
        layout.addWidget(self.clear_button)

    def _on_text_changed(self, text):
        """Handle text changes in the search input."""
        self.clear_button.setVisible(bool(text))
        self.search_changed.emit(text)

    def clear(self):
        """Clear the search input."""
        self.search_input.clear()

    def text(self):
        """Get the current search text."""
        return self.search_input.text()

    def setFocus(self):
        """Set focus to the search input."""
        self.search_input.setFocus()

class NotificationBanner(QFrame):
    """
    Notification banner for displaying success, error, or info messages.
    Automatically disappears after a timeout.
    """

    # Message types with corresponding styles
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

    def __init__(self, parent=None):
        """
        Initialize a notification banner.

        Args:
            parent: Parent widget
        """
        super(NotificationBanner, self).__init__(parent)

        # Set up UI
        self._setup_ui()

        # Hide initially
        self.hide()

        # Animation for showing/hiding
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # Timer for auto-hide
        self.timer = None

    def _setup_ui(self):
        """Set up the banner UI."""
        # Set minimum height
        self.setMinimumHeight(60)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        layout.addWidget(self.icon_label)

        # Message
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label, 1)

        # Close button
        self.close_button = IconButton(Icons.CANCEL, "Dismiss")
        self.close_button.clicked.connect(self.hide_animation)
        layout.addWidget(self.close_button)

    def show_message(self, message, message_type=INFO, timeout=3000):
        """
        Show a notification message.

        Args:
            message (str): Message to display
            message_type (str): Type of message (INFO, SUCCESS, WARNING, ERROR)
            timeout (int): Time in ms before auto-hiding (0 for no auto-hide)
        """
        # Configure icon and style based on message type
        if message_type == self.SUCCESS:
            icon_name = Icons.SUCCESS
            self.setObjectName("success_banner")
        elif message_type == self.WARNING:
            icon_name = Icons.WARNING
            self.setObjectName("warning_banner")
        elif message_type == self.ERROR:
            icon_name = Icons.ERROR
            self.setObjectName("error_banner")
        else:  # INFO is default
            icon_name = Icons.INFO
            self.setObjectName("info_banner")

        # Update icon and message
        self.icon_label.setPixmap(IconProvider.get_icon(icon_name).pixmap(QSize(24, 24)))
        self.message_label.setText(message)

        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)

        # Show with animation
        self.show_animation()

        # Set timer for auto-hide if timeout > 0
        if timeout > 0:
            try:
                if self.timer:
                    self.timer.stop()
                self.timer = QTimer()
                self.timer.setSingleShot(True)
                self.timer.timeout.connect(self.hide_animation)
                self.timer.start(timeout)
            except Exception as e:
                logger.error(f"Error setting notification timer: {e}")

    def show_animation(self):
        """Show the banner with a slide-down animation."""
        # Stop any running animations
        self.animation.stop()

        # Make sure widget is visible
        self.show()

        # Get parent dimensions
        if self.parent():
            parent_width = self.parent().width()
        else:
            parent_width = self.width()

        # Calculate start and end positions
        start_height = self.height()
        self.animation.setStartValue(QRect(0, -start_height, parent_width, start_height))
        self.animation.setEndValue(QRect(0, 0, parent_width, start_height))

        # Start animation
        self.animation.start()

    def hide_animation(self):
        """Hide the banner with a slide-up animation."""
        # Stop any running animations
        self.animation.stop()

        # Get parent dimensions
        if self.parent():
            parent_width = self.parent().width()
        else:
            parent_width = self.width()

        # Calculate start and end positions
        start_height = self.height()
        self.animation.setStartValue(QRect(0, 0, parent_width, start_height))
        self.animation.setEndValue(QRect(0, -start_height, parent_width, start_height))

        # Connect to finished signal to hide widget
        self.animation.finished.connect(self.hide)

        # Start animation
        self.animation.start()

class LoadingOverlay(QWidget):
    """
    Semi-transparent overlay with loading indicator.
    Used to block UI during longer operations.
    """

    def __init__(self, parent=None):
        """
        Initialize a loading overlay.

        Args:
            parent: Parent widget
        """
        super(LoadingOverlay, self).__init__(parent)

        # Set up UI
        self._setup_ui()

        # Hide initially
        self.hide()

        # Track parent resizes
        if parent:
            self.resize(parent.size())
            parent.resizeEvent = self._handle_parent_resize

    def _setup_ui(self):
        """Set up the overlay UI."""
        # Set background color and opacity
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 128))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # Loading indicator (just a text label for now)
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            background-color: #313244;
            color: white;
            font-size: 16pt;
            font-weight: bold;
            padding: 20px 40px;
            border-radius: 10px;
        """)
        layout.addWidget(self.loading_label)

    def _handle_parent_resize(self, event):
        """Handle parent widget resize events."""
        # Resize overlay to match parent
        self.resize(event.size())

        # Call original parent resizeEvent if it exists
        parent = self.parent()
        if parent and hasattr(parent, "_original_resize_event"):
            parent._original_resize_event(event)

    def show_loading(self, message="Loading..."):
        """
        Show the loading overlay with specified message.

        Args:
            message (str): Loading message to display
        """
        self.loading_label.setText(message)
        self.show()

        # Ensure overlay is on top
        self.raise_()

        # Force update
        QCoreApplication.processEvents()

    def hide_loading(self):
        """Hide the loading overlay."""
        self.hide()