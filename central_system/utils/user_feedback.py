"""
Enhanced user feedback and error handling system for ConsultEase.
Provides consistent, user-friendly feedback across the application.
"""

import logging
from typing import Optional, Callable, Any, Dict, List
from enum import Enum
from PyQt5.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QMessageBox, QApplication,
    QDialogButtonBox, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor

from .ui_components import ModernButton, StatusIndicator, AccessibleButton
from .code_quality import OperationResult

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of user feedback."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    LOADING = "loading"


class ToastNotification(QFrame):
    """
    Toast notification widget for non-intrusive user feedback.
    """
    
    # Signals
    clicked = pyqtSignal()
    dismissed = pyqtSignal()
    
    def __init__(self, message: str, feedback_type: FeedbackType = FeedbackType.INFO,
                 duration: int = 3000, parent: Optional[QWidget] = None):
        """
        Initialize toast notification.
        
        Args:
            message: Notification message
            feedback_type: Type of feedback
            duration: Display duration in milliseconds (0 = permanent)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.feedback_type = feedback_type
        self.duration = duration
        
        # Setup UI
        self._setup_ui(message)
        
        # Auto-dismiss timer
        if duration > 0:
            self.dismiss_timer = QTimer()
            self.dismiss_timer.setSingleShot(True)
            self.dismiss_timer.timeout.connect(self.dismiss)
            self.dismiss_timer.start(duration)
        
        # Animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _setup_ui(self, message: str):
        """Setup the notification UI."""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setFixedHeight(60)
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Status indicator
        self.status_indicator = StatusIndicator(
            self.feedback_type.value, 
            ""
        )
        self.status_indicator.setFixedSize(20, 20)
        layout.addWidget(self.status_indicator)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.message_label)
        
        # Dismiss button
        self.dismiss_button = QPushButton("×")
        self.dismiss_button.setFixedSize(20, 20)
        self.dismiss_button.setFlat(True)
        self.dismiss_button.clicked.connect(self.dismiss)
        layout.addWidget(self.dismiss_button)
        
        # Apply styling
        self._apply_styling()
    
    def _apply_styling(self):
        """Apply styling based on feedback type."""
        colors = {
            FeedbackType.SUCCESS: {"bg": "#d4edda", "border": "#c3e6cb", "text": "#155724"},
            FeedbackType.INFO: {"bg": "#d1ecf1", "border": "#bee5eb", "text": "#0c5460"},
            FeedbackType.WARNING: {"bg": "#fff3cd", "border": "#ffeaa7", "text": "#856404"},
            FeedbackType.ERROR: {"bg": "#f8d7da", "border": "#f5c6cb", "text": "#721c24"},
            FeedbackType.LOADING: {"bg": "#e2e3e5", "border": "#d6d8db", "text": "#383d41"}
        }
        
        color_scheme = colors.get(self.feedback_type, colors[FeedbackType.INFO])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color_scheme["bg"]};
                border: 1px solid {color_scheme["border"]};
                border-radius: 8px;
            }}
            QLabel {{
                color: {color_scheme["text"]};
                font-weight: 500;
            }}
            QPushButton {{
                color: {color_scheme["text"]};
                font-weight: bold;
                border: none;
                background: transparent;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }}
        """)
    
    def show_animated(self):
        """Show notification with fade-in animation."""
        self.setWindowOpacity(0.0)
        self.show()
        
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
    
    def dismiss(self):
        """Dismiss notification with fade-out animation."""
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()
        
        self.dismissed.emit()
    
    def mousePressEvent(self, event):
        """Handle mouse click."""
        super().mousePressEvent(event)
        self.clicked.emit()


class ProgressDialog(QDialog):
    """
    Enhanced progress dialog with detailed feedback.
    """
    
    # Signals
    cancelled = pyqtSignal()
    
    def __init__(self, title: str = "Processing", message: str = "Please wait...",
                 cancelable: bool = False, parent: Optional[QWidget] = None):
        """
        Initialize progress dialog.
        
        Args:
            title: Dialog title
            message: Initial message
            cancelable: Whether the operation can be cancelled
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.cancelable = cancelable
        self.is_cancelled = False
        
        # Setup UI
        self._setup_ui(title, message)
        
        # Configure dialog
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        if not cancelable:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
    
    def _setup_ui(self, title: str, message: str):
        """Setup the dialog UI."""
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(11)
        self.message_label.setFont(font)
        layout.addWidget(self.message_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 10pt;")
        layout.addWidget(self.status_label)
        
        # Cancel button
        if self.cancelable:
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            self.cancel_button = ModernButton("Cancel", danger=True)
            self.cancel_button.clicked.connect(self._on_cancel)
            button_layout.addWidget(self.cancel_button)
            
            layout.addLayout(button_layout)
    
    def update_progress(self, value: int, message: str = "", status: str = ""):
        """
        Update progress and messages.
        
        Args:
            value: Progress value (0-100)
            message: Main message
            status: Status message
        """
        self.progress_bar.setValue(value)
        
        if message:
            self.message_label.setText(message)
        
        if status:
            self.status_label.setText(status)
        
        # Process events to keep UI responsive
        QApplication.processEvents()
    
    def set_indeterminate(self, indeterminate: bool = True):
        """Set progress bar to indeterminate mode."""
        if indeterminate:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(0)
        else:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.is_cancelled = True
        self.cancelled.emit()
        self.reject()
    
    def closeEvent(self, event):
        """Handle close event."""
        if self.cancelable:
            self._on_cancel()
        else:
            event.ignore()


class ErrorDetailsDialog(QDialog):
    """
    Dialog for showing detailed error information.
    """
    
    def __init__(self, title: str, message: str, details: str = "",
                 parent: Optional[QWidget] = None):
        """
        Initialize error details dialog.
        
        Args:
            title: Error title
            message: User-friendly error message
            details: Technical error details
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 400)
        
        # Setup UI
        self._setup_ui(message, details)
    
    def _setup_ui(self, message: str, details: str):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Error icon and message
        header_layout = QHBoxLayout()
        
        # Error icon (using text for now)
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 24pt;")
        header_layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        header_layout.addWidget(message_label)
        
        layout.addLayout(header_layout)
        
        # Details section
        if details:
            details_label = QLabel("Technical Details:")
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(details_label)
            
            # Scrollable details
            details_text = QTextEdit()
            details_text.setPlainText(details)
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(200)
            layout.addWidget(details_text)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class FeedbackManager:
    """
    Centralized feedback management system.
    """
    
    def __init__(self, parent_widget: QWidget):
        """
        Initialize feedback manager.
        
        Args:
            parent_widget: Parent widget for notifications
        """
        self.parent_widget = parent_widget
        self.active_toasts: List[ToastNotification] = []
        self.toast_position_offset = 10
    
    def show_toast(self, message: str, feedback_type: FeedbackType = FeedbackType.INFO,
                   duration: int = 3000) -> ToastNotification:
        """
        Show a toast notification.
        
        Args:
            message: Notification message
            feedback_type: Type of feedback
            duration: Display duration in milliseconds
            
        Returns:
            ToastNotification instance
        """
        toast = ToastNotification(message, feedback_type, duration, self.parent_widget)
        
        # Position toast
        self._position_toast(toast)
        
        # Connect signals
        toast.dismissed.connect(lambda: self._remove_toast(toast))
        
        # Add to active toasts
        self.active_toasts.append(toast)
        
        # Show with animation
        toast.show_animated()
        
        return toast
    
    def show_success(self, message: str, duration: int = 3000) -> ToastNotification:
        """Show success toast."""
        return self.show_toast(message, FeedbackType.SUCCESS, duration)
    
    def show_error(self, message: str, duration: int = 5000) -> ToastNotification:
        """Show error toast."""
        return self.show_toast(message, FeedbackType.ERROR, duration)
    
    def show_warning(self, message: str, duration: int = 4000) -> ToastNotification:
        """Show warning toast."""
        return self.show_toast(message, FeedbackType.WARNING, duration)
    
    def show_info(self, message: str, duration: int = 3000) -> ToastNotification:
        """Show info toast."""
        return self.show_toast(message, FeedbackType.INFO, duration)
    
    def show_progress_dialog(self, title: str = "Processing", 
                           message: str = "Please wait...",
                           cancelable: bool = False) -> ProgressDialog:
        """
        Show progress dialog.
        
        Args:
            title: Dialog title
            message: Initial message
            cancelable: Whether operation can be cancelled
            
        Returns:
            ProgressDialog instance
        """
        dialog = ProgressDialog(title, message, cancelable, self.parent_widget)
        return dialog
    
    def show_error_details(self, title: str, message: str, details: str = ""):
        """
        Show detailed error dialog.
        
        Args:
            title: Error title
            message: User-friendly message
            details: Technical details
        """
        dialog = ErrorDetailsDialog(title, message, details, self.parent_widget)
        dialog.exec_()
    
    def handle_operation_result(self, result: OperationResult, 
                              success_message: str = "Operation completed successfully"):
        """
        Handle operation result with appropriate feedback.
        
        Args:
            result: Operation result
            success_message: Message to show on success
        """
        if result.is_success():
            self.show_success(success_message)
        else:
            error_message = result.get_error_message() or "An error occurred"
            self.show_error(error_message)
            
            # Show details if available
            if result.metadata and result.metadata.get('details'):
                self.show_error_details(
                    "Error Details",
                    error_message,
                    result.metadata['details']
                )
    
    def _position_toast(self, toast: ToastNotification):
        """Position toast notification."""
        parent_rect = self.parent_widget.rect()
        
        # Calculate position (top-right corner)
        x = parent_rect.width() - toast.width() - 20
        y = 20 + (len(self.active_toasts) * (toast.height() + 10))
        
        toast.move(x, y)
    
    def _remove_toast(self, toast: ToastNotification):
        """Remove toast from active list and reposition others."""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            toast.deleteLater()
            
            # Reposition remaining toasts
            for i, active_toast in enumerate(self.active_toasts):
                parent_rect = self.parent_widget.rect()
                x = parent_rect.width() - active_toast.width() - 20
                y = 20 + (i * (active_toast.height() + 10))
                active_toast.move(x, y)
    
    def clear_all_toasts(self):
        """Clear all active toast notifications."""
        for toast in self.active_toasts[:]:
            toast.dismiss()


# Global feedback manager instance
_feedback_manager: Optional[FeedbackManager] = None


def get_feedback_manager(parent_widget: QWidget = None) -> FeedbackManager:
    """Get or create global feedback manager."""
    global _feedback_manager
    if _feedback_manager is None and parent_widget:
        _feedback_manager = FeedbackManager(parent_widget)
    return _feedback_manager


def set_feedback_manager(manager: FeedbackManager):
    """Set global feedback manager."""
    global _feedback_manager
    _feedback_manager = manager
