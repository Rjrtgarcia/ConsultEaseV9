"""
Modern stylesheet for ConsultEase UI.
Provides light and dark themes with responsive, touch-friendly styling.
"""

def get_dark_stylesheet():
    """
    Returns a modern dark-themed stylesheet for ConsultEase.
    
    Returns:
        str: The complete stylesheet as a string.
    """
    return """
    /* Global styles */
    QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        font-family: 'Segoe UI', Roboto, Ubuntu, 'Open Sans', sans-serif;
        font-size: 12pt;
    }
    
    /* Main windows */
    QMainWindow, QDialog {
        background-color: #1e1e2e;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #7287fd;
        color: #ffffff;
        border-radius: 8px;
        padding: 12px 20px;
        text-align: center;
        font-weight: bold;
        font-size: 13pt;
        border: none;
    }
    
    QPushButton:hover {
        background-color: #8ca0ff;
    }
    
    QPushButton:pressed {
        background-color: #5e6ecc;
    }
    
    QPushButton:disabled {
        background-color: #45475a;
        color: #6c7086;
    }
    
    /* Large buttons for main actions */
    QPushButton#primary_button {
        background-color: #94e2d5;
        color: #1e1e2e;
        font-size: 14pt;
        padding: 15px 25px;
    }
    
    QPushButton#primary_button:hover {
        background-color: #a6e3d8;
    }
    
    /* Danger buttons */
    QPushButton#danger_button {
        background-color: #f38ba8;
        color: #ffffff;
    }
    
    QPushButton#danger_button:hover {
        background-color: #f5a3b9;
    }
    
    /* Input fields */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #313244;
        color: #cdd6f4;
        border: 2px solid #45475a;
        border-radius: 6px;
        padding: 10px;
        font-size: 13pt;
        selection-background-color: #7287fd;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #7287fd;
    }
    
    /* Labels */
    QLabel {
        font-size: 12pt;
        color: #cdd6f4;
    }
    
    QLabel#heading {
        font-size: 18pt;
        font-weight: bold;
        color: #94e2d5;
        margin-bottom: 10px;
    }
    
    QLabel#subheading {
        font-size: 14pt;
        color: #89b4fa;
    }
    
    /* Dropdowns */
    QComboBox {
        background-color: #313244;
        color: #cdd6f4;
        border: 2px solid #45475a;
        border-radius: 6px;
        padding: 10px;
        min-width: 200px;
        font-size: 13pt;
    }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: none;
    }
    
    QComboBox QAbstractItemView {
        background-color: #313244;
        color: #cdd6f4;
        border: 2px solid #7287fd;
        selection-background-color: #7287fd;
        selection-color: #ffffff;
        border-radius: 6px;
    }
    
    /* Tables */
    QTableView, QTableWidget {
        background-color: #313244;
        alternate-background-color: #292c3c;
        color: #cdd6f4;
        border: none;
        gridline-color: #45475a;
        font-size: 12pt;
    }
    
    QTableView::item:selected, QTableWidget::item:selected {
        background-color: #7287fd;
        color: #ffffff;
    }
    
    QHeaderView::section {
        background-color: #45475a;
        color: #cdd6f4;
        font-weight: bold;
        padding: 10px;
        border: none;
    }
    
    /* Scrollbars */
    QScrollBar:vertical {
        border: none;
        background-color: #45475a;
        width: 14px;
        margin: 0px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #7287fd;
        border-radius: 7px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #8ca0ff;
    }
    
    QScrollBar:horizontal {
        border: none;
        background-color: #45475a;
        height: 14px;
        margin: 0px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #7287fd;
        border-radius: 7px;
        min-width: 30px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #8ca0ff;
    }
    
    /* Tabs */
    QTabWidget::pane {
        border: 2px solid #45475a;
        border-radius: 6px;
    }
    
    QTabBar::tab {
        background-color: #45475a;
        color: #cdd6f4;
        padding: 15px 25px;
        font-size: 13pt;
        font-weight: bold;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #7287fd;
        color: #ffffff;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #585b70;
    }
    
    /* Status indicators */
    QLabel#available {
        color: #a6e3a1;
        font-weight: bold;
    }
    
    QLabel#unavailable {
        color: #f38ba8;
        font-weight: bold;
    }
    
    /* Menu */
    QMenuBar {
        background-color: #1e1e2e;
        color: #cdd6f4;
    }
    
    QMenuBar::item:selected {
        background-color: #7287fd;
        color: #ffffff;
    }
    
    QMenu {
        background-color: #313244;
        color: #cdd6f4;
        border: 1px solid #45475a;
    }
    
    QMenu::item:selected {
        background-color: #7287fd;
        color: #ffffff;
    }
    
    /* Faculty card styling */
    QFrame#faculty_card {
        background-color: #313244;
        border-radius: 10px;
        padding: 15px;
        margin: 8px;
    }
    
    QFrame#faculty_card_available {
        background-color: #313244;
        border: 2px solid #a6e3a1;
        border-radius: 10px;
        padding: 15px;
        margin: 8px;
    }
    
    QFrame#faculty_card_unavailable {
        background-color: #313244;
        border: 2px solid #f38ba8;
        border-radius: 10px;
        padding: 15px;
        margin: 8px;
    }
    """

def get_light_stylesheet():
    """
    Returns a modern light-themed stylesheet for ConsultEase.
    White background with navy blue and gold accents.
    
    Returns:
        str: The complete stylesheet as a string.
    """
    return """
    /* Global styles */
    QWidget {
        background-color: #ffffff;
        color: #333333;
        font-family: 'Segoe UI', Roboto, Ubuntu, 'Open Sans', sans-serif;
        font-size: 12pt;
    }
    
    /* Main windows */
    QMainWindow, QDialog {
        background-color: #ffffff;
    }
    
    /* Buttons */
    QPushButton {
        background-color: #0d3b66;
        color: #ffffff;
        border-radius: 8px;
        padding: 12px 20px;
        text-align: center;
        font-weight: bold;
        font-size: 13pt;
        border: none;
    }
    
    QPushButton:hover {
        background-color: #1a4b7c;
    }
    
    QPushButton:pressed {
        background-color: #072a4f;
    }
    
    QPushButton:disabled {
        background-color: #cccccc;
        color: #888888;
    }
    
    /* Large buttons for main actions */
    QPushButton#primary_button {
        background-color: #ffc233;
        color: #0d3b66;
        font-size: 14pt;
        padding: 15px 25px;
    }
    
    QPushButton#primary_button:hover {
        background-color: #ffcd57;
    }
    
    /* Danger buttons */
    QPushButton#danger_button {
        background-color: #e63946;
        color: #ffffff;
    }
    
    QPushButton#danger_button:hover {
        background-color: #f25965;
    }
    
    /* Input fields */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        color: #333333;
        border: 2px solid #cccccc;
        border-radius: 6px;
        padding: 10px;
        font-size: 13pt;
        selection-background-color: #0d3b66;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #ffc233;
    }
    
    /* Labels */
    QLabel {
        font-size: 12pt;
        color: #333333;
    }
    
    QLabel#heading {
        font-size: 18pt;
        font-weight: bold;
        color: #0d3b66;
        margin-bottom: 10px;
    }
    
    QLabel#subheading {
        font-size: 14pt;
        color: #ffc233;
    }
    
    /* Dropdowns */
    QComboBox {
        background-color: #ffffff;
        color: #333333;
        border: 2px solid #cccccc;
        border-radius: 6px;
        padding: 10px;
        min-width: 200px;
        font-size: 13pt;
    }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: none;
    }
    
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #333333;
        border: 2px solid #0d3b66;
        selection-background-color: #0d3b66;
        selection-color: #ffffff;
        border-radius: 6px;
    }
    
    /* Tables */
    QTableView, QTableWidget {
        background-color: #ffffff;
        alternate-background-color: #f5f5f5;
        color: #333333;
        border: none;
        gridline-color: #cccccc;
        font-size: 12pt;
    }
    
    QTableView::item:selected, QTableWidget::item:selected {
        background-color: #0d3b66;
        color: #ffffff;
    }
    
    QHeaderView::section {
        background-color: #ffc233;
        color: #0d3b66;
        font-weight: bold;
        padding: 10px;
        border: none;
    }
    
    /* Scrollbars */
    QScrollBar:vertical {
        border: none;
        background-color: #eeeeee;
        width: 14px;
        margin: 0px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #0d3b66;
        border-radius: 7px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #1a4b7c;
    }
    
    QScrollBar:horizontal {
        border: none;
        background-color: #eeeeee;
        height: 14px;
        margin: 0px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #0d3b66;
        border-radius: 7px;
        min-width: 30px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #1a4b7c;
    }
    
    /* Tabs */
    QTabWidget::pane {
        border: 2px solid #cccccc;
        border-radius: 6px;
    }
    
    QTabBar::tab {
        background-color: #eeeeee;
        color: #333333;
        padding: 15px 25px;
        font-size: 13pt;
        font-weight: bold;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #0d3b66;
        color: #ffffff;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #dddddd;
    }
    
    /* Status indicators */
    QLabel#available {
        color: #28a745;
        font-weight: bold;
    }
    
    QLabel#unavailable {
        color: #e63946;
        font-weight: bold;
    }
    
    /* Menu */
    QMenuBar {
        background-color: #ffffff;
        color: #333333;
    }
    
    QMenuBar::item:selected {
        background-color: #0d3b66;
        color: #ffffff;
    }
    
    QMenu {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cccccc;
    }
    
    QMenu::item:selected {
        background-color: #0d3b66;
        color: #ffffff;
    }
    
    /* Faculty card styling */
    QFrame#faculty_card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin: 8px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    QFrame#faculty_card_available {
        background-color: #ffffff;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 15px;
        margin: 8px;
    }
    
    QFrame#faculty_card_unavailable {
        background-color: #ffffff;
        border: 2px solid #e63946;
        border-radius: 10px;
        padding: 15px;
        margin: 8px;
    }
    """

def apply_stylesheet(app, theme="dark"):
    """
    Apply the selected stylesheet to the application.
    
    Args:
        app: QApplication instance
        theme (str): Theme to apply ("dark" or "light")
    """
    if theme.lower() == "light":
        app.setStyleSheet(get_light_stylesheet())
    else:
        app.setStyleSheet(get_dark_stylesheet()) 