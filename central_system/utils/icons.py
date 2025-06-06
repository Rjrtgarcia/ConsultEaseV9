"""
Icons utility for ConsultEase UI.
Provides access to modern, touch-friendly icons for the application.
"""

import os
import logging
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize, Qt

logger = logging.getLogger(__name__)

# Base directory for icons
ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')

# Create icons directory if it doesn't exist
os.makedirs(ICONS_DIR, exist_ok=True)

# Flag to track initialization status
_initialized = False

class IconProvider:
    """
    Provider for accessing application icons.
    """
    
    # Default icon size for buttons (touch-friendly)
    DEFAULT_BUTTON_SIZE = QSize(32, 32)
    
    # Icon cache to avoid reloading icons
    _icon_cache = {}
    
    @staticmethod
    def get_icon(name, size=None):
        """
        Get an icon by name.
        
        Args:
            name (str): Icon name (without extension)
            size (QSize, optional): Desired icon size
            
        Returns:
            QIcon: The requested icon or a fallback if not found
        """
        # Ensure icons are initialized
        if not _initialized:
            logger.warning("Icons not initialized, returning empty icon")
            return QIcon()
            
        # Check if icon is in cache
        cache_key = f"{name}_{size.width()}x{size.height()}" if size else name
        if cache_key in IconProvider._icon_cache:
            return IconProvider._icon_cache[cache_key]
        
        # Look for icon in different formats
        icon_extensions = ['.png', '.svg', '.jpg']
        icon_path = None
        
        for ext in icon_extensions:
            path = os.path.join(ICONS_DIR, f"{name}{ext}")
            if os.path.exists(path):
                icon_path = path
                break
        
        if icon_path:
            icon = QIcon(icon_path)
            if size:
                # Create a pixmap of the requested size
                pixmap = icon.pixmap(size)
                sized_icon = QIcon()
                sized_icon.addPixmap(pixmap)
                IconProvider._icon_cache[cache_key] = sized_icon
                return sized_icon
            else:
                IconProvider._icon_cache[cache_key] = icon
                return icon
        else:
            logger.warning(f"Icon '{name}' not found, using fallback")
            return IconProvider._create_fallback_icon(name, size)
    
    @staticmethod
    def _create_fallback_icon(name, size=None):
        """
        Create a fallback icon for when the requested icon is not found.
        
        Args:
            name (str): Icon name
            size (QSize, optional): Desired icon size
            
        Returns:
            QIcon: A simple colored fallback icon
        """
        if size is None:
            size = IconProvider.DEFAULT_BUTTON_SIZE
        
        # Create a colored pixmap
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        # Cache and return the icon
        icon = QIcon(pixmap)
        cache_key = f"{name}_{size.width()}x{size.height()}" if size else name
        IconProvider._icon_cache[cache_key] = icon
        return icon
    
    @staticmethod
    def get_button_icon(name):
        """
        Get an icon sized appropriately for a button.
        
        Args:
            name (str): Icon name
            
        Returns:
            QIcon: Icon sized for a button
        """
        return IconProvider.get_icon(name, IconProvider.DEFAULT_BUTTON_SIZE)
    
    @staticmethod
    def set_default_button_size(width, height):
        """
        Set the default button icon size.
        
        Args:
            width (int): Width in pixels
            height (int): Height in pixels
        """
        IconProvider.DEFAULT_BUTTON_SIZE = QSize(width, height)

# Define standard icon names for consistency
class Icons:
    """
    Standard icon names used throughout the application.
    Using this class ensures consistency in icon usage.
    """
    # Navigation icons
    HOME = "home"
    BACK = "back"
    FORWARD = "forward"
    MENU = "menu"
    
    # Action icons
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    SAVE = "save"
    CANCEL = "cancel"
    REFRESH = "refresh"
    SEARCH = "search"
    
    # Status icons
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    WAITING = "waiting"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    
    # User icons
    USER = "user"
    FACULTY = "faculty"
    STUDENT = "student"
    ADMIN = "admin"
    
    # Misc icons
    SETTINGS = "settings"
    HELP = "help"
    LOGOUT = "logout"
    CALENDAR = "calendar"
    CLOCK = "clock"
    MESSAGE = "message"
    NOTIFICATION = "notification"
    
    # Feature icons
    CONSULTATION = "consultation"
    APPOINTMENT = "appointment"
    RFID = "rfid"
    REPORTS = "reports"
    DATABASE = "database"

def setup_default_icons():
    """
    Generate basic default icons if they don't exist.
    This ensures the application has some basic icons available.
    """
    global _initialized
    
    # List of essential icons to create if missing
    essential_icons = [
        Icons.AVAILABLE,
        Icons.UNAVAILABLE,
        Icons.ADD,
        Icons.EDIT,
        Icons.DELETE,
        Icons.USER,
        Icons.FACULTY,
        Icons.STUDENT,
        Icons.SETTINGS
    ]
    
    # Define colors for each icon type
    icon_colors = {
        Icons.AVAILABLE: "#40a02b",    # Green
        Icons.UNAVAILABLE: "#d20f39",  # Red
        Icons.ADD: "#1e66f5",          # Blue
        Icons.EDIT: "#df8e1d",         # Orange
        Icons.DELETE: "#d20f39",       # Red
        Icons.USER: "#7287fd",         # Purple
        Icons.FACULTY: "#1e66f5",      # Blue
        Icons.STUDENT: "#40a02b",      # Green
        Icons.SETTINGS: "#df8e1d",     # Orange
    }
    
    # Create simple colored square icons as fallbacks
    for icon_name in essential_icons:
        icon_path = os.path.join(ICONS_DIR, f"{icon_name}.png")
        if not os.path.exists(icon_path):
            try:
                # Create a simple colored icon as fallback
                size = 64
                pixmap = QPixmap(size, size)
                color = icon_colors.get(icon_name, "#7287fd")  # Default purple
                pixmap.fill(Qt.transparent)
                pixmap.save(icon_path)
                logger.info(f"Created fallback icon for {icon_name}")
            except Exception as e:
                logger.error(f"Failed to create fallback icon for {icon_name}: {e}")
    
    _initialized = True
    logger.info("Icon system initialized")

def initialize():
    """
    Initialize the icon system.
    Call this after QApplication is created.
    """
    setup_default_icons()

# NOTE: No automatic initialization here.
# You must call initialize() after creating QApplication 