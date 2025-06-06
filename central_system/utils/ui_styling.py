"""
Consistent UI styling system for ConsultEase.
Provides centralized styling, themes, and responsive design utilities.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QPalette, QColor

logger = logging.getLogger(__name__)


class ColorScheme(Enum):
    """Color scheme definitions for consistent UI theming."""
    
    # Primary colors
    PRIMARY = "#3498db"
    PRIMARY_DARK = "#2980b9"
    PRIMARY_LIGHT = "#5dade2"
    
    # Secondary colors
    SECONDARY = "#95a5a6"
    SECONDARY_DARK = "#7f8c8d"
    SECONDARY_LIGHT = "#bdc3c7"
    
    # Status colors
    SUCCESS = "#27ae60"
    SUCCESS_DARK = "#229954"
    SUCCESS_LIGHT = "#58d68d"
    
    WARNING = "#f39c12"
    WARNING_DARK = "#e67e22"
    WARNING_LIGHT = "#f8c471"
    
    ERROR = "#e74c3c"
    ERROR_DARK = "#c0392b"
    ERROR_LIGHT = "#ec7063"
    
    INFO = "#3498db"
    INFO_DARK = "#2980b9"
    INFO_LIGHT = "#5dade2"
    
    # Neutral colors
    WHITE = "#ffffff"
    LIGHT_GRAY = "#f8f9fa"
    GRAY = "#6c757d"
    DARK_GRAY = "#495057"
    BLACK = "#212529"
    
    # Background colors
    BACKGROUND = "#f8f9fa"
    CARD_BACKGROUND = "#ffffff"
    SIDEBAR_BACKGROUND = "#343a40"
    
    # Border colors
    BORDER_LIGHT = "#dee2e6"
    BORDER_MEDIUM = "#ced4da"
    BORDER_DARK = "#6c757d"


class FontSize(Enum):
    """Font size definitions for consistent typography."""
    
    EXTRA_SMALL = 8
    SMALL = 10
    NORMAL = 11
    MEDIUM = 12
    LARGE = 14
    EXTRA_LARGE = 16
    HEADING = 18
    TITLE = 20
    DISPLAY = 24


class Spacing(Enum):
    """Spacing definitions for consistent layout."""
    
    NONE = 0
    EXTRA_SMALL = 4
    SMALL = 8
    MEDIUM = 12
    LARGE = 16
    EXTRA_LARGE = 20
    HUGE = 24


class BorderRadius(Enum):
    """Border radius definitions for consistent rounded corners."""
    
    NONE = 0
    SMALL = 4
    MEDIUM = 8
    LARGE = 12
    ROUND = 50  # For circular elements


class UITheme:
    """
    UI theme configuration with consistent styling rules.
    """
    
    def __init__(self, name: str = "default"):
        """
        Initialize UI theme.
        
        Args:
            name: Theme name
        """
        self.name = name
        self.colors = ColorScheme
        self.fonts = FontSize
        self.spacing = Spacing
        self.border_radius = BorderRadius
        
        # Component-specific styles
        self.button_styles = self._create_button_styles()
        self.card_styles = self._create_card_styles()
        self.input_styles = self._create_input_styles()
        self.label_styles = self._create_label_styles()
    
    def _create_button_styles(self) -> Dict[str, str]:
        """Create button style definitions."""
        return {
            "primary": f"""
                QPushButton {{
                    background-color: {self.colors.PRIMARY.value};
                    color: {self.colors.WHITE.value};
                    border: none;
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.MEDIUM.value}px {self.spacing.LARGE.value}px;
                    font-size: {self.fonts.NORMAL.value}pt;
                    font-weight: 500;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.PRIMARY_DARK.value};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.PRIMARY_DARK.value};
                    padding-top: {self.spacing.MEDIUM.value + 1}px;
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.SECONDARY.value};
                    color: {self.colors.GRAY.value};
                }}
            """,
            
            "secondary": f"""
                QPushButton {{
                    background-color: {self.colors.SECONDARY.value};
                    color: {self.colors.WHITE.value};
                    border: none;
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.MEDIUM.value}px {self.spacing.LARGE.value}px;
                    font-size: {self.fonts.NORMAL.value}pt;
                    font-weight: 500;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.SECONDARY_DARK.value};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.SECONDARY_DARK.value};
                    padding-top: {self.spacing.MEDIUM.value + 1}px;
                }}
            """,
            
            "success": f"""
                QPushButton {{
                    background-color: {self.colors.SUCCESS.value};
                    color: {self.colors.WHITE.value};
                    border: none;
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.MEDIUM.value}px {self.spacing.LARGE.value}px;
                    font-size: {self.fonts.NORMAL.value}pt;
                    font-weight: 500;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.SUCCESS_DARK.value};
                }}
            """,
            
            "danger": f"""
                QPushButton {{
                    background-color: {self.colors.ERROR.value};
                    color: {self.colors.WHITE.value};
                    border: none;
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.MEDIUM.value}px {self.spacing.LARGE.value}px;
                    font-size: {self.fonts.NORMAL.value}pt;
                    font-weight: 500;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.ERROR_DARK.value};
                }}
            """,
            
            "outline": f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.colors.PRIMARY.value};
                    border: 2px solid {self.colors.PRIMARY.value};
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.MEDIUM.value}px {self.spacing.LARGE.value}px;
                    font-size: {self.fonts.NORMAL.value}pt;
                    font-weight: 500;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.PRIMARY.value};
                    color: {self.colors.WHITE.value};
                }}
            """,
            
            "icon": f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.SMALL.value}px;
                    min-width: 32px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.LIGHT_GRAY.value};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.SECONDARY_LIGHT.value};
                }}
            """
        }
    
    def _create_card_styles(self) -> Dict[str, str]:
        """Create card style definitions."""
        return {
            "default": f"""
                QFrame {{
                    background-color: {self.colors.CARD_BACKGROUND.value};
                    border: 1px solid {self.colors.BORDER_LIGHT.value};
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.LARGE.value}px;
                }}
            """,
            
            "elevated": f"""
                QFrame {{
                    background-color: {self.colors.CARD_BACKGROUND.value};
                    border: 1px solid {self.colors.BORDER_LIGHT.value};
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.LARGE.value}px;
                }}
            """,
            
            "faculty": f"""
                QFrame {{
                    background-color: {self.colors.CARD_BACKGROUND.value};
                    border: 1px solid {self.colors.BORDER_LIGHT.value};
                    border-radius: {self.border_radius.MEDIUM.value}px;
                    padding: {self.spacing.MEDIUM.value}px;
                    min-height: 100px;
                }}
                QFrame:hover {{
                    border-color: {self.colors.PRIMARY.value};
                    background-color: {self.colors.LIGHT_GRAY.value};
                }}
            """
        }
    
    def _create_input_styles(self) -> Dict[str, str]:
        """Create input field style definitions."""
        return {
            "default": f"""
                QLineEdit {{
                    border: 2px solid {self.colors.BORDER_MEDIUM.value};
                    border-radius: {self.border_radius.SMALL.value}px;
                    padding: {self.spacing.SMALL.value}px {self.spacing.MEDIUM.value}px;
                    font-size: {self.fonts.NORMAL.value}pt;
                    background-color: {self.colors.WHITE.value};
                    min-height: 32px;
                }}
                QLineEdit:focus {{
                    border-color: {self.colors.PRIMARY.value};
                    outline: none;
                }}
                QLineEdit:disabled {{
                    background-color: {self.colors.LIGHT_GRAY.value};
                    color: {self.colors.GRAY.value};
                }}
            """,
            
            "search": f"""
                QLineEdit {{
                    border: 2px solid {self.colors.BORDER_MEDIUM.value};
                    border-radius: {self.border_radius.LARGE.value}px;
                    padding: {self.spacing.SMALL.value}px {self.spacing.LARGE.value}px;
                    font-size: {self.fonts.NORMAL.value}pt;
                    background-color: {self.colors.WHITE.value};
                    min-height: 36px;
                }}
                QLineEdit:focus {{
                    border-color: {self.colors.PRIMARY.value};
                }}
            """
        }
    
    def _create_label_styles(self) -> Dict[str, str]:
        """Create label style definitions."""
        return {
            "heading": f"""
                QLabel {{
                    font-size: {self.fonts.HEADING.value}pt;
                    font-weight: bold;
                    color: {self.colors.DARK_GRAY.value};
                    margin-bottom: {self.spacing.MEDIUM.value}px;
                }}
            """,
            
            "title": f"""
                QLabel {{
                    font-size: {self.fonts.TITLE.value}pt;
                    font-weight: bold;
                    color: {self.colors.BLACK.value};
                    margin-bottom: {self.spacing.LARGE.value}px;
                }}
            """,
            
            "subtitle": f"""
                QLabel {{
                    font-size: {self.fonts.MEDIUM.value}pt;
                    font-weight: 500;
                    color: {self.colors.GRAY.value};
                    margin-bottom: {self.spacing.SMALL.value}px;
                }}
            """,
            
            "body": f"""
                QLabel {{
                    font-size: {self.fonts.NORMAL.value}pt;
                    color: {self.colors.DARK_GRAY.value};
                    line-height: 1.4;
                }}
            """,
            
            "caption": f"""
                QLabel {{
                    font-size: {self.fonts.SMALL.value}pt;
                    color: {self.colors.GRAY.value};
                }}
            """
        }
    
    def get_button_style(self, style_type: str = "primary") -> str:
        """Get button style by type."""
        return self.button_styles.get(style_type, self.button_styles["primary"])
    
    def get_card_style(self, style_type: str = "default") -> str:
        """Get card style by type."""
        return self.card_styles.get(style_type, self.card_styles["default"])
    
    def get_input_style(self, style_type: str = "default") -> str:
        """Get input style by type."""
        return self.input_styles.get(style_type, self.input_styles["default"])
    
    def get_label_style(self, style_type: str = "body") -> str:
        """Get label style by type."""
        return self.label_styles.get(style_type, self.label_styles["body"])


class ResponsiveDesign:
    """
    Responsive design utilities for different screen sizes.
    """
    
    # Screen size breakpoints
    MOBILE_MAX = 768
    TABLET_MAX = 1024
    DESKTOP_MIN = 1025
    
    @staticmethod
    def get_screen_category(width: int) -> str:
        """
        Get screen category based on width.
        
        Args:
            width: Screen width in pixels
            
        Returns:
            str: Screen category (mobile, tablet, desktop)
        """
        if width <= ResponsiveDesign.MOBILE_MAX:
            return "mobile"
        elif width <= ResponsiveDesign.TABLET_MAX:
            return "tablet"
        else:
            return "desktop"
    
    @staticmethod
    def get_responsive_font_size(base_size: int, screen_category: str) -> int:
        """
        Get responsive font size based on screen category.
        
        Args:
            base_size: Base font size
            screen_category: Screen category
            
        Returns:
            int: Adjusted font size
        """
        multipliers = {
            "mobile": 0.9,
            "tablet": 1.0,
            "desktop": 1.1
        }
        
        multiplier = multipliers.get(screen_category, 1.0)
        return int(base_size * multiplier)
    
    @staticmethod
    def get_responsive_spacing(base_spacing: int, screen_category: str) -> int:
        """
        Get responsive spacing based on screen category.
        
        Args:
            base_spacing: Base spacing value
            screen_category: Screen category
            
        Returns:
            int: Adjusted spacing
        """
        multipliers = {
            "mobile": 0.8,
            "tablet": 1.0,
            "desktop": 1.2
        }
        
        multiplier = multipliers.get(screen_category, 1.0)
        return int(base_spacing * multiplier)


# Global theme instance
_current_theme: Optional[UITheme] = None


def get_current_theme() -> UITheme:
    """Get the current UI theme."""
    global _current_theme
    if _current_theme is None:
        _current_theme = UITheme("default")
    return _current_theme


def set_theme(theme: UITheme):
    """Set the current UI theme."""
    global _current_theme
    _current_theme = theme
    logger.info(f"UI theme set to: {theme.name}")


def apply_style_to_widget(widget, style_type: str, component_type: str = "button"):
    """
    Apply consistent styling to a widget.
    
    Args:
        widget: Qt widget to style
        style_type: Style type (e.g., "primary", "secondary")
        component_type: Component type (e.g., "button", "card", "input")
    """
    theme = get_current_theme()
    
    style_getters = {
        "button": theme.get_button_style,
        "card": theme.get_card_style,
        "input": theme.get_input_style,
        "label": theme.get_label_style
    }
    
    getter = style_getters.get(component_type)
    if getter:
        style = getter(style_type)
        widget.setStyleSheet(style)
    else:
        logger.warning(f"Unknown component type: {component_type}")


def create_responsive_font(base_size: int, screen_width: int) -> QFont:
    """
    Create a responsive font based on screen width.
    
    Args:
        base_size: Base font size
        screen_width: Screen width in pixels
        
    Returns:
        QFont: Responsive font
    """
    screen_category = ResponsiveDesign.get_screen_category(screen_width)
    responsive_size = ResponsiveDesign.get_responsive_font_size(base_size, screen_category)
    
    font = QFont()
    font.setPointSize(responsive_size)
    return font
