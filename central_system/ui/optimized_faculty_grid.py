"""
Optimized faculty grid component with virtual scrolling and performance enhancements.
Designed for Raspberry Pi touch interface with large faculty lists.
"""

import logging
import hashlib
from typing import List, Dict, Callable, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPalette, QPixmap

from .virtual_scroll_widget import VirtualScrollWidget
from ..utils.ui_components import FacultyCard
from ..ui.pooled_faculty_card import get_faculty_card_manager

logger = logging.getLogger(__name__)


class OptimizedFacultyGrid(QWidget):
    """
    Optimized faculty grid with virtual scrolling and performance optimizations.
    Uses component pooling and efficient rendering for large faculty lists.
    """
    
    # Signals
    faculty_selected = pyqtSignal(dict)  # faculty_data
    consultation_requested = pyqtSignal(dict)  # faculty_data
    
    def __init__(self, parent=None):
        """
        Initialize optimized faculty grid.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configuration
        self.grid_columns = 3  # Number of columns in grid
        self.card_width = 280
        self.card_height = 120
        self.card_spacing = 15
        
        # Data management
        self.faculty_data: List[Dict] = []
        self.filtered_data: List[Dict] = []
        self.data_hash = ""
        
        # Performance optimization
        self.faculty_card_manager = get_faculty_card_manager()
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._perform_update)
        self.update_delay = 100  # 100ms debounce
        
        # Callbacks
        self.consultation_callback: Optional[Callable] = None
        
        # Setup UI
        self._setup_ui()
        
        logger.debug("Optimized faculty grid initialized")
    
    def _setup_ui(self):
        """Setup the optimized faculty grid UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Faculty Members")
        header_label.setObjectName("section_header")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Virtual scroll widget for faculty grid
        self.scroll_widget = VirtualScrollWidget()
        self.scroll_widget.set_item_creator(self._create_faculty_row)
        self.scroll_widget.set_item_updater(self._update_faculty_row)
        self.scroll_widget.set_item_height(self.card_height + self.card_spacing)
        
        # Connect signals
        self.scroll_widget.item_clicked.connect(self._on_faculty_clicked)
        
        layout.addWidget(self.scroll_widget)
        
        # Configure size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def _create_faculty_row(self, row_data: List[Dict], row_index: int) -> QWidget:
        """
        Create a row widget containing faculty cards.
        
        Args:
            row_data: List of faculty data for this row
            row_index: Row index
            
        Returns:
            QWidget: Row widget containing faculty cards
        """
        try:
            row_widget = QFrame()
            row_widget.setFrameStyle(QFrame.NoFrame)
            row_widget.setFixedHeight(self.card_height)
            
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(self.card_spacing)
            
            # Create faculty cards for this row
            for faculty_data in row_data:
                try:
                    # Get pooled faculty card
                    faculty_card = self.faculty_card_manager.get_faculty_card(
                        faculty_data, self.consultation_callback
                    )
                    
                    # Configure card size
                    faculty_card.setFixedSize(self.card_width, self.card_height)
                    
                    # Store faculty data reference
                    faculty_card.faculty_data = faculty_data
                    
                    row_layout.addWidget(faculty_card)
                    
                except Exception as e:
                    logger.error(f"Error creating faculty card for {faculty_data.get('name', 'Unknown')}: {e}")
                    continue
            
            # Add stretch to fill remaining space
            row_layout.addStretch()
            
            return row_widget
            
        except Exception as e:
            logger.error(f"Error creating faculty row {row_index}: {e}")
            # Return empty widget as fallback
            return QFrame()
    
    def _update_faculty_row(self, row_widget: QWidget, row_data: List[Dict], row_index: int):
        """
        Update an existing row widget with new data.
        
        Args:
            row_widget: Existing row widget
            row_data: New faculty data for this row
            row_index: Row index
        """
        try:
            layout = row_widget.layout()
            if not layout:
                return
            
            # Get existing cards
            existing_cards = []
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, 'faculty_data'):
                        existing_cards.append(widget)
            
            # Update existing cards or create new ones
            for i, faculty_data in enumerate(row_data):
                if i < len(existing_cards):
                    # Update existing card
                    card = existing_cards[i]
                    if hasattr(card, 'configure'):
                        card.configure(faculty_data, self.consultation_callback)
                    card.faculty_data = faculty_data
                else:
                    # Create new card
                    faculty_card = self.faculty_card_manager.get_faculty_card(
                        faculty_data, self.consultation_callback
                    )
                    faculty_card.setFixedSize(self.card_width, self.card_height)
                    faculty_card.faculty_data = faculty_data
                    layout.insertWidget(i, faculty_card)
            
            # Remove excess cards
            while len(existing_cards) > len(row_data):
                card = existing_cards.pop()
                layout.removeWidget(card)
                self.faculty_card_manager.return_faculty_card(card.faculty_data.get('id'))
                
        except Exception as e:
            logger.error(f"Error updating faculty row {row_index}: {e}")
    
    def set_faculty_data(self, faculty_list: List[Dict]):
        """
        Set the faculty data to display.
        
        Args:
            faculty_list: List of faculty dictionaries
        """
        # Calculate data hash for change detection
        data_str = str(sorted(faculty_list, key=lambda x: x.get('id', 0)))
        new_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        # Only update if data has changed
        if new_hash != self.data_hash:
            self.faculty_data = faculty_list.copy()
            self.data_hash = new_hash
            
            # Schedule update
            self._schedule_update()
            
            logger.debug(f"Faculty data updated: {len(faculty_list)} faculty members")
        else:
            logger.debug("Faculty data unchanged, skipping update")
    
    def set_consultation_callback(self, callback: Callable):
        """
        Set the callback function for consultation requests.
        
        Args:
            callback: Function to call when consultation is requested
        """
        self.consultation_callback = callback
        logger.debug("Consultation callback set")
    
    def filter_faculty(self, filter_func: Callable[[Dict], bool]):
        """
        Apply a filter to the faculty data.
        
        Args:
            filter_func: Function that takes faculty dict and returns bool
        """
        try:
            self.filtered_data = [f for f in self.faculty_data if filter_func(f)]
            self._schedule_update()
            logger.debug(f"Applied filter: {len(self.filtered_data)}/{len(self.faculty_data)} faculty shown")
        except Exception as e:
            logger.error(f"Error applying faculty filter: {e}")
            self.filtered_data = self.faculty_data.copy()
    
    def clear_filter(self):
        """Clear any applied filters."""
        self.filtered_data = self.faculty_data.copy()
        self._schedule_update()
        logger.debug("Faculty filter cleared")
    
    def _schedule_update(self):
        """Schedule a UI update with debouncing."""
        if not self.update_timer.isActive():
            self.update_timer.start(self.update_delay)
    
    def _perform_update(self):
        """Perform the actual UI update."""
        try:
            # Use filtered data if available, otherwise use all data
            data_to_display = self.filtered_data if self.filtered_data else self.faculty_data
            
            # Group faculty into rows
            rows = []
            for i in range(0, len(data_to_display), self.grid_columns):
                row_data = data_to_display[i:i + self.grid_columns]
                rows.append(row_data)
            
            # Update virtual scroll widget
            self.scroll_widget.set_items(rows)
            
            logger.debug(f"Updated faculty grid: {len(rows)} rows, {len(data_to_display)} faculty")
            
        except Exception as e:
            logger.error(f"Error updating faculty grid: {e}")
    
    def _on_faculty_clicked(self, row_index: int, row_data: List[Dict]):
        """
        Handle faculty card click events.
        
        Args:
            row_index: Index of clicked row
            row_data: Faculty data for the row
        """
        # For now, just emit signal for first faculty in row
        # Future enhancement: detect which specific card was clicked
        if row_data:
            faculty_data = row_data[0]
            self.faculty_selected.emit(faculty_data)
            logger.debug(f"Faculty selected: {faculty_data.get('name', 'Unknown')}")
    
    def refresh(self):
        """Force refresh the faculty grid."""
        self.data_hash = ""  # Force update
        self._perform_update()
        logger.debug("Faculty grid refreshed")
    
    def get_visible_faculty_count(self) -> int:
        """Get the number of currently visible faculty members."""
        return len(self.filtered_data) if self.filtered_data else len(self.faculty_data)
    
    def scroll_to_faculty(self, faculty_id: int):
        """
        Scroll to make a specific faculty member visible.
        
        Args:
            faculty_id: ID of faculty member to scroll to
        """
        try:
            data_to_display = self.filtered_data if self.filtered_data else self.faculty_data
            
            # Find faculty index
            faculty_index = -1
            for i, faculty in enumerate(data_to_display):
                if faculty.get('id') == faculty_id:
                    faculty_index = i
                    break
            
            if faculty_index >= 0:
                # Calculate row index
                row_index = faculty_index // self.grid_columns
                self.scroll_widget.scroll_to_item(row_index)
                logger.debug(f"Scrolled to faculty {faculty_id} at row {row_index}")
            else:
                logger.warning(f"Faculty {faculty_id} not found in current view")
                
        except Exception as e:
            logger.error(f"Error scrolling to faculty {faculty_id}: {e}")
    
    def set_grid_columns(self, columns: int):
        """
        Set the number of columns in the grid.
        
        Args:
            columns: Number of columns (1-5)
        """
        if 1 <= columns <= 5:
            self.grid_columns = columns
            self._schedule_update()
            logger.debug(f"Grid columns set to {columns}")
    
    def set_card_size(self, width: int, height: int):
        """
        Set the size of faculty cards.
        
        Args:
            width: Card width in pixels
            height: Card height in pixels
        """
        self.card_width = width
        self.card_height = height
        self.scroll_widget.set_item_height(height + self.card_spacing)
        self._schedule_update()
        logger.debug(f"Card size set to {width}x{height}")
