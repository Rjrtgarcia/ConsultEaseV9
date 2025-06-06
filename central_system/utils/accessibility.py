"""
Accessibility utilities for ConsultEase.
Provides keyboard navigation, screen reader support, and accessibility features.
"""

import logging
from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import QWidget, QApplication, QShortcut
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QEvent
from PyQt5.QtGui import QKeySequence, QFont, QPalette, QColor

logger = logging.getLogger(__name__)


class AccessibilityManager(QObject):
    """
    Manages accessibility features across the application.
    """
    
    # Signals
    focus_changed = pyqtSignal(QWidget)
    shortcut_activated = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize accessibility manager.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.parent_widget = parent
        self.shortcuts: Dict[str, QShortcut] = {}
        self.focus_chain: List[QWidget] = []
        self.current_focus_index = -1
        
        # Accessibility settings
        self.high_contrast_enabled = False
        self.large_text_enabled = False
        self.keyboard_navigation_enabled = True
        self.screen_reader_enabled = False
        
        # Setup accessibility features
        self._setup_keyboard_navigation()
        self._setup_focus_management()
        
        logger.debug("Accessibility manager initialized")
    
    def _setup_keyboard_navigation(self):
        """Setup keyboard navigation shortcuts."""
        if not self.parent_widget:
            return
        
        # Tab navigation
        self.add_shortcut("Tab", self._focus_next_widget, "Focus next widget")
        self.add_shortcut("Shift+Tab", self._focus_previous_widget, "Focus previous widget")
        
        # Quick navigation
        self.add_shortcut("Alt+1", lambda: self._focus_by_role("button"), "Focus first button")
        self.add_shortcut("Alt+2", lambda: self._focus_by_role("input"), "Focus first input")
        self.add_shortcut("Alt+3", lambda: self._focus_by_role("list"), "Focus first list")
        
        # Accessibility toggles
        self.add_shortcut("Ctrl+Alt+H", self.toggle_high_contrast, "Toggle high contrast")
        self.add_shortcut("Ctrl+Alt+L", self.toggle_large_text, "Toggle large text")
        
        # Help
        self.add_shortcut("F1", self.show_accessibility_help, "Show accessibility help")
    
    def _setup_focus_management(self):
        """Setup focus management."""
        if self.parent_widget:
            # Install event filter to track focus changes
            QApplication.instance().focusChanged.connect(self._on_focus_changed)
    
    def add_shortcut(self, key_sequence: str, callback, description: str = ""):
        """
        Add a keyboard shortcut.
        
        Args:
            key_sequence: Key sequence (e.g., "Ctrl+S")
            callback: Function to call when shortcut is activated
            description: Description for accessibility
        """
        if not self.parent_widget:
            return
        
        shortcut = QShortcut(QKeySequence(key_sequence), self.parent_widget)
        shortcut.activated.connect(callback)
        shortcut.setContext(Qt.ApplicationShortcut)
        
        # Store shortcut with metadata
        self.shortcuts[key_sequence] = {
            'shortcut': shortcut,
            'callback': callback,
            'description': description
        }
        
        logger.debug(f"Added keyboard shortcut: {key_sequence} - {description}")
    
    def remove_shortcut(self, key_sequence: str):
        """Remove a keyboard shortcut."""
        if key_sequence in self.shortcuts:
            shortcut_data = self.shortcuts.pop(key_sequence)
            shortcut_data['shortcut'].deleteLater()
            logger.debug(f"Removed keyboard shortcut: {key_sequence}")
    
    def get_shortcuts_help(self) -> List[Dict[str, str]]:
        """Get list of available shortcuts for help display."""
        return [
            {
                'key': key,
                'description': data['description']
            }
            for key, data in self.shortcuts.items()
            if data['description']
        ]
    
    def _focus_next_widget(self):
        """Focus the next widget in the focus chain."""
        if not self.focus_chain:
            self._build_focus_chain()
        
        if self.focus_chain:
            self.current_focus_index = (self.current_focus_index + 1) % len(self.focus_chain)
            widget = self.focus_chain[self.current_focus_index]
            if widget and widget.isVisible() and widget.isEnabled():
                widget.setFocus()
                self._announce_widget(widget)
    
    def _focus_previous_widget(self):
        """Focus the previous widget in the focus chain."""
        if not self.focus_chain:
            self._build_focus_chain()
        
        if self.focus_chain:
            self.current_focus_index = (self.current_focus_index - 1) % len(self.focus_chain)
            widget = self.focus_chain[self.current_focus_index]
            if widget and widget.isVisible() and widget.isEnabled():
                widget.setFocus()
                self._announce_widget(widget)
    
    def _focus_by_role(self, role: str):
        """Focus the first widget of a specific role."""
        if not self.parent_widget:
            return
        
        role_selectors = {
            "button": "QPushButton",
            "input": "QLineEdit",
            "list": "QListWidget"
        }
        
        selector = role_selectors.get(role)
        if selector:
            widgets = self.parent_widget.findChildren(QWidget, selector)
            for widget in widgets:
                if widget.isVisible() and widget.isEnabled():
                    widget.setFocus()
                    self._announce_widget(widget)
                    break
    
    def _build_focus_chain(self):
        """Build the focus chain for keyboard navigation."""
        if not self.parent_widget:
            return
        
        self.focus_chain = []
        
        # Find all focusable widgets
        all_widgets = self.parent_widget.findChildren(QWidget)
        for widget in all_widgets:
            if (widget.focusPolicy() != Qt.NoFocus and 
                widget.isVisible() and 
                widget.isEnabled()):
                self.focus_chain.append(widget)
        
        # Sort by tab order if available
        self.focus_chain.sort(key=lambda w: w.tabOrder() if hasattr(w, 'tabOrder') else 0)
        
        logger.debug(f"Built focus chain with {len(self.focus_chain)} widgets")
    
    def _on_focus_changed(self, old_widget: QWidget, new_widget: QWidget):
        """Handle focus change events."""
        if new_widget:
            self.focus_changed.emit(new_widget)
            
            # Update focus index
            if new_widget in self.focus_chain:
                self.current_focus_index = self.focus_chain.index(new_widget)
            
            # Announce widget for screen readers
            if self.screen_reader_enabled:
                self._announce_widget(new_widget)
    
    def _announce_widget(self, widget: QWidget):
        """Announce widget information for screen readers."""
        if not widget:
            return
        
        # Get widget information
        widget_type = widget.__class__.__name__
        widget_text = ""
        
        # Extract text based on widget type
        if hasattr(widget, 'text'):
            widget_text = widget.text()
        elif hasattr(widget, 'accessibleName'):
            widget_text = widget.accessibleName()
        elif hasattr(widget, 'toolTip'):
            widget_text = widget.toolTip()
        
        # Create announcement
        announcement = f"{widget_type}"
        if widget_text:
            announcement += f": {widget_text}"
        
        # Add state information
        if not widget.isEnabled():
            announcement += " (disabled)"
        
        logger.debug(f"Screen reader announcement: {announcement}")
        
        # In a real implementation, this would interface with screen reader APIs
        # For now, we'll use the accessible name
        if widget_text:
            widget.setAccessibleName(announcement)
    
    def toggle_high_contrast(self):
        """Toggle high contrast mode."""
        self.high_contrast_enabled = not self.high_contrast_enabled
        self._apply_high_contrast()
        
        status = "enabled" if self.high_contrast_enabled else "disabled"
        logger.info(f"High contrast mode {status}")
    
    def toggle_large_text(self):
        """Toggle large text mode."""
        self.large_text_enabled = not self.large_text_enabled
        self._apply_large_text()
        
        status = "enabled" if self.large_text_enabled else "disabled"
        logger.info(f"Large text mode {status}")
    
    def _apply_high_contrast(self):
        """Apply high contrast styling."""
        if not self.parent_widget:
            return
        
        if self.high_contrast_enabled:
            # High contrast color scheme
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(0, 0, 0))
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.Base, QColor(0, 0, 0))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
            palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
            palette.setColor(QPalette.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
            
            self.parent_widget.setPalette(palette)
        else:
            # Reset to default palette
            self.parent_widget.setPalette(QPalette())
    
    def _apply_large_text(self):
        """Apply large text styling."""
        if not self.parent_widget:
            return
        
        # Get all widgets and adjust font sizes
        all_widgets = self.parent_widget.findChildren(QWidget)
        
        for widget in all_widgets:
            if hasattr(widget, 'font'):
                font = widget.font()
                if self.large_text_enabled:
                    # Increase font size by 20%
                    new_size = int(font.pointSize() * 1.2)
                    font.setPointSize(max(new_size, 12))  # Minimum 12pt
                else:
                    # Reset to default size (this is simplified)
                    font.setPointSize(11)  # Default size
                
                widget.setFont(font)
    
    def show_accessibility_help(self):
        """Show accessibility help dialog."""
        from ..utils.user_feedback import get_feedback_manager
        
        feedback_manager = get_feedback_manager(self.parent_widget)
        if feedback_manager:
            shortcuts_text = "\n".join([
                f"{item['key']}: {item['description']}"
                for item in self.get_shortcuts_help()
            ])
            
            help_text = f"""
Accessibility Features:

Keyboard Shortcuts:
{shortcuts_text}

Current Settings:
- High Contrast: {'Enabled' if self.high_contrast_enabled else 'Disabled'}
- Large Text: {'Enabled' if self.large_text_enabled else 'Disabled'}
- Keyboard Navigation: {'Enabled' if self.keyboard_navigation_enabled else 'Disabled'}

Tips:
- Use Tab/Shift+Tab to navigate between elements
- Press Enter or Space to activate buttons
- Use arrow keys to navigate lists and menus
- Press Escape to close dialogs
            """
            
            feedback_manager.show_info(help_text.strip(), duration=0)  # Permanent until dismissed
    
    def set_widget_accessibility(self, widget: QWidget, name: str, description: str = "", 
                                role: str = ""):
        """
        Set accessibility properties for a widget.
        
        Args:
            widget: Widget to configure
            name: Accessible name
            description: Accessible description
            role: Widget role
        """
        widget.setAccessibleName(name)
        if description:
            widget.setAccessibleDescription(description)
        
        # Set focus policy for keyboard navigation
        if widget.focusPolicy() == Qt.NoFocus:
            widget.setFocusPolicy(Qt.TabFocus)
        
        logger.debug(f"Set accessibility for {widget.__class__.__name__}: {name}")
    
    def make_widget_keyboard_accessible(self, widget: QWidget, shortcut: str = ""):
        """
        Make a widget accessible via keyboard.
        
        Args:
            widget: Widget to make accessible
            shortcut: Optional keyboard shortcut
        """
        # Ensure widget can receive focus
        if widget.focusPolicy() == Qt.NoFocus:
            widget.setFocusPolicy(Qt.TabFocus)
        
        # Add to focus chain
        if widget not in self.focus_chain:
            self.focus_chain.append(widget)
        
        # Add shortcut if provided
        if shortcut and hasattr(widget, 'click'):
            self.add_shortcut(shortcut, widget.click, f"Activate {widget.accessibleName()}")


# Global accessibility manager
_accessibility_manager: Optional[AccessibilityManager] = None


def get_accessibility_manager(parent_widget: QWidget = None) -> Optional[AccessibilityManager]:
    """Get or create global accessibility manager."""
    global _accessibility_manager
    if _accessibility_manager is None and parent_widget:
        _accessibility_manager = AccessibilityManager(parent_widget)
    return _accessibility_manager


def set_accessibility_manager(manager: AccessibilityManager):
    """Set global accessibility manager."""
    global _accessibility_manager
    _accessibility_manager = manager


def make_widget_accessible(widget: QWidget, name: str, description: str = "", 
                          shortcut: str = ""):
    """
    Convenience function to make a widget accessible.
    
    Args:
        widget: Widget to make accessible
        name: Accessible name
        description: Accessible description
        shortcut: Optional keyboard shortcut
    """
    manager = get_accessibility_manager()
    if manager:
        manager.set_widget_accessibility(widget, name, description)
        if shortcut:
            manager.make_widget_keyboard_accessible(widget, shortcut)
