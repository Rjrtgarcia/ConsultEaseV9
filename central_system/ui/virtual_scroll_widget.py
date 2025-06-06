"""
Virtual scrolling widget for improved performance with large lists.
Optimized for Raspberry Pi touch interface.
"""

import logging
from typing import List, Callable, Any, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QFrame, 
                             QSizePolicy, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QPainter, QResizeEvent

logger = logging.getLogger(__name__)


class VirtualScrollWidget(QScrollArea):
    """
    Virtual scrolling widget that only renders visible items for performance.
    Optimized for touch interfaces and large datasets.
    """
    
    # Signals
    item_clicked = pyqtSignal(int, object)  # index, item_data
    selection_changed = pyqtSignal(int)     # selected_index
    
    def __init__(self, parent=None):
        """
        Initialize virtual scroll widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configuration
        self.item_height = 120  # Default item height in pixels
        self.visible_buffer = 2  # Extra items to render above/below visible area
        self.scroll_sensitivity = 20  # Pixels per scroll step
        
        # Data management
        self.items: List[Any] = []
        self.item_widgets: dict = {}  # index -> widget mapping
        self.item_creator: Optional[Callable] = None
        self.item_updater: Optional[Callable] = None
        
        # Viewport management
        self.viewport_start = 0
        self.viewport_end = 0
        self.visible_start = 0
        self.visible_end = 0
        
        # Selection
        self.selected_index = -1
        self.multi_select = False
        self.selected_indices = set()
        
        # Performance optimization
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_viewport)
        self.update_delay = 16  # ~60 FPS
        
        # Setup UI
        self._setup_ui()
        
        logger.debug("Virtual scroll widget initialized")
    
    def _setup_ui(self):
        """Setup the virtual scroll UI."""
        # Configure scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        self.content_widget = QFrame()
        self.content_widget.setFrameStyle(QFrame.NoFrame)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Set content widget
        self.setWidget(self.content_widget)
        
        # Connect scroll events
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        # Touch-friendly configuration
        self.setFocusPolicy(Qt.StrongFocus)
        
    def set_item_creator(self, creator: Callable[[Any, int], QWidget]):
        """
        Set the function to create item widgets.
        
        Args:
            creator: Function that takes (item_data, index) and returns QWidget
        """
        self.item_creator = creator
        logger.debug("Item creator function set")
    
    def set_item_updater(self, updater: Callable[[QWidget, Any, int], None]):
        """
        Set the function to update existing item widgets.
        
        Args:
            updater: Function that takes (widget, item_data, index) and updates widget
        """
        self.item_updater = updater
        logger.debug("Item updater function set")
    
    def set_items(self, items: List[Any]):
        """
        Set the list of items to display.
        
        Args:
            items: List of item data
        """
        self.items = items
        self.selected_index = -1
        self.selected_indices.clear()
        
        # Clear existing widgets
        self._clear_widgets()
        
        # Update content size
        total_height = len(self.items) * self.item_height
        self.content_widget.setFixedHeight(total_height)
        
        # Update viewport
        self._schedule_viewport_update()
        
        logger.debug(f"Set {len(items)} items for virtual scrolling")
    
    def add_item(self, item: Any):
        """Add a single item to the list."""
        self.items.append(item)
        
        # Update content size
        total_height = len(self.items) * self.item_height
        self.content_widget.setFixedHeight(total_height)
        
        # Update viewport if needed
        self._schedule_viewport_update()
    
    def remove_item(self, index: int):
        """Remove item at specified index."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            
            # Remove widget if it exists
            if index in self.item_widgets:
                widget = self.item_widgets.pop(index)
                widget.setParent(None)
                widget.deleteLater()
            
            # Shift widget indices
            new_widgets = {}
            for widget_index, widget in self.item_widgets.items():
                if widget_index > index:
                    new_widgets[widget_index - 1] = widget
                else:
                    new_widgets[widget_index] = widget
            self.item_widgets = new_widgets
            
            # Update content size
            total_height = len(self.items) * self.item_height
            self.content_widget.setFixedHeight(total_height)
            
            # Update selection
            if self.selected_index == index:
                self.selected_index = -1
            elif self.selected_index > index:
                self.selected_index -= 1
            
            # Update viewport
            self._schedule_viewport_update()
    
    def update_item(self, index: int, item: Any):
        """Update item data at specified index."""
        if 0 <= index < len(self.items):
            self.items[index] = item
            
            # Update widget if it exists and updater is available
            if index in self.item_widgets and self.item_updater:
                widget = self.item_widgets[index]
                self.item_updater(widget, item, index)
    
    def _schedule_viewport_update(self):
        """Schedule a viewport update with debouncing."""
        if not self.update_timer.isActive():
            self.update_timer.start(self.update_delay)
    
    def _on_scroll(self, value):
        """Handle scroll events."""
        self._schedule_viewport_update()
    
    def _update_viewport(self):
        """Update the visible viewport and render necessary widgets."""
        if not self.items or not self.item_creator:
            return
        
        # Calculate visible range
        scroll_value = self.verticalScrollBar().value()
        viewport_height = self.viewport().height()
        
        # Calculate which items should be visible
        start_index = max(0, (scroll_value // self.item_height) - self.visible_buffer)
        end_index = min(len(self.items), 
                       ((scroll_value + viewport_height) // self.item_height) + self.visible_buffer + 1)
        
        # Remove widgets that are no longer needed
        widgets_to_remove = []
        for index in self.item_widgets:
            if index < start_index or index >= end_index:
                widgets_to_remove.append(index)
        
        for index in widgets_to_remove:
            widget = self.item_widgets.pop(index)
            widget.setParent(None)
            widget.deleteLater()
        
        # Create widgets for newly visible items
        for index in range(start_index, end_index):
            if index not in self.item_widgets:
                try:
                    widget = self.item_creator(self.items[index], index)
                    if widget:
                        # Position widget
                        y_pos = index * self.item_height
                        widget.setGeometry(0, y_pos, self.content_widget.width(), self.item_height)
                        widget.setParent(self.content_widget)
                        widget.show()
                        
                        # Store widget
                        self.item_widgets[index] = widget
                        
                        # Connect click events if widget supports it
                        if hasattr(widget, 'clicked'):
                            widget.clicked.connect(lambda idx=index: self._on_item_clicked(idx))
                        elif hasattr(widget, 'mousePressEvent'):
                            # Override mousePressEvent for click detection
                            original_mouse_press = widget.mousePressEvent
                            def mouse_press_wrapper(event, idx=index):
                                original_mouse_press(event)
                                self._on_item_clicked(idx)
                            widget.mousePressEvent = mouse_press_wrapper
                
                except Exception as e:
                    logger.error(f"Error creating widget for item {index}: {e}")
        
        # Update viewport tracking
        self.viewport_start = start_index
        self.viewport_end = end_index
        
        logger.debug(f"Updated viewport: {start_index}-{end_index} ({len(self.item_widgets)} widgets)")
    
    def _on_item_clicked(self, index: int):
        """Handle item click events."""
        if 0 <= index < len(self.items):
            # Update selection
            if self.multi_select:
                if index in self.selected_indices:
                    self.selected_indices.remove(index)
                else:
                    self.selected_indices.add(index)
            else:
                self.selected_index = index
                self.selected_indices = {index}
            
            # Emit signals
            self.item_clicked.emit(index, self.items[index])
            self.selection_changed.emit(index)
            
            logger.debug(f"Item clicked: {index}")
    
    def _clear_widgets(self):
        """Clear all item widgets."""
        for widget in self.item_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
        self.item_widgets.clear()
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle resize events."""
        super().resizeEvent(event)
        
        # Update widget widths
        new_width = event.size().width()
        for widget in self.item_widgets.values():
            widget.setFixedWidth(new_width)
        
        # Schedule viewport update
        self._schedule_viewport_update()
    
    def get_selected_items(self):
        """Get currently selected items."""
        if self.multi_select:
            return [self.items[i] for i in self.selected_indices if 0 <= i < len(self.items)]
        elif self.selected_index >= 0:
            return [self.items[self.selected_index]]
        return []
    
    def clear_selection(self):
        """Clear current selection."""
        self.selected_index = -1
        self.selected_indices.clear()
        self.selection_changed.emit(-1)
    
    def scroll_to_item(self, index: int):
        """Scroll to make the specified item visible."""
        if 0 <= index < len(self.items):
            y_pos = index * self.item_height
            self.verticalScrollBar().setValue(y_pos)
    
    def set_item_height(self, height: int):
        """Set the height of each item."""
        self.item_height = height
        
        # Update content size
        total_height = len(self.items) * self.item_height
        self.content_widget.setFixedHeight(total_height)
        
        # Update viewport
        self._schedule_viewport_update()
