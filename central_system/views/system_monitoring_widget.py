"""
System monitoring widget for ConsultEase admin dashboard.
Displays real-time system health and performance metrics.
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QGroupBox, QGridLayout, QTextEdit, QPushButton, QFrame,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette

from ..utils.system_monitor import get_system_monitor, SystemMonitor
from ..utils.ui_components import ModernButton

logger = logging.getLogger(__name__)


class MetricWidget(QWidget):
    """Widget for displaying a single metric with progress bar."""

    def __init__(self, title: str, unit: str = "%", max_value: float = 100):
        super().__init__()
        self.title = title
        self.unit = unit
        self.max_value = max_value
        self.init_ui()

    def init_ui(self):
        """Initialize the metric widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # Value label
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(int(self.max_value))
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)

    def update_value(self, value: float, status: str = "normal"):
        """
        Update the metric value and appearance.

        Args:
            value: The metric value
            status: Status indicator ('normal', 'warning', 'critical')
        """
        # Update value label
        if self.unit == "GB":
            self.value_label.setText(f"{value:.1f} {self.unit}")
        else:
            self.value_label.setText(f"{value:.1f}{self.unit}")

        # Update progress bar
        self.progress_bar.setValue(int(value))

        # Update colors based on status
        if status == "critical":
            color = "#f44336"  # Red
        elif status == "warning":
            color = "#ff9800"  # Orange
        else:
            color = "#4caf50"  # Green

        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)


class ServiceStatusWidget(QWidget):
    """Widget for displaying service status."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the service status widget UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Service Status")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # Services grid
        self.services_layout = QGridLayout()
        self.service_labels = {}

        services = ['ConsultEase', 'PostgreSQL', 'MQTT Broker', 'Squeekboard']
        for i, service in enumerate(services):
            # Service name
            name_label = QLabel(service)
            name_label.setFont(QFont("Arial", 10))
            self.services_layout.addWidget(name_label, i, 0)

            # Status indicator
            status_label = QLabel("Unknown")
            status_label.setFont(QFont("Arial", 10, QFont.Bold))
            status_label.setFixedWidth(80)
            status_label.setAlignment(Qt.AlignCenter)
            self.services_layout.addWidget(status_label, i, 1)

            self.service_labels[service.lower().replace(' ', '_')] = status_label

        layout.addLayout(self.services_layout)

    def update_service_status(self, service_name: str, status: str):
        """Update the status of a service."""
        widget_key = service_name.lower().replace(' ', '_')
        if widget_key in self.service_labels:
            label = self.service_labels[widget_key]
            label.setText(status.title())

            # Update color based on status
            if status == "running":
                color = "#4caf50"  # Green
                text_color = "white"
            elif status == "stopped":
                color = "#f44336"  # Red
                text_color = "white"
            else:
                color = "#ff9800"  # Orange
                text_color = "white"

            label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: {text_color};
                    border-radius: 4px;
                    padding: 2px 4px;
                }}
            """)


class AlertsWidget(QWidget):
    """Widget for displaying system alerts."""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the alerts widget UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Recent Alerts")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)

        # Alerts text area
        self.alerts_text = QTextEdit()
        self.alerts_text.setMaximumHeight(150)
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setPlaceholderText("No recent alerts")
        layout.addWidget(self.alerts_text)

        # Clear button
        clear_button = QPushButton("Clear Alerts")
        clear_button.clicked.connect(self.clear_alerts)
        layout.addWidget(clear_button)

    def update_alerts(self, alerts: list):
        """Update the alerts display."""
        if not alerts:
            self.alerts_text.setPlainText("No recent alerts")
            return

        alert_text = ""
        for alert in alerts[-10:]:  # Show last 10 alerts
            timestamp = alert['timestamp'].strftime("%H:%M:%S")
            severity = alert['severity'].upper()
            message = alert['message']
            alert_text += f"[{timestamp}] {severity}: {message}\n"

        self.alerts_text.setPlainText(alert_text)

        # Scroll to bottom
        cursor = self.alerts_text.textCursor()
        cursor.movePosition(cursor.End)
        self.alerts_text.setTextCursor(cursor)

    def clear_alerts(self):
        """Clear the alerts display."""
        self.alerts_text.setPlainText("No recent alerts")


class SystemMonitoringWidget(QWidget):
    """
    Main system monitoring widget for the admin dashboard.
    """

    monitoring_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_monitor = get_system_monitor()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.init_ui()

    def init_ui(self):
        """Initialize the system monitoring widget UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel("System Monitoring")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Control buttons
        self.start_button = ModernButton("Start Monitoring", primary=True)
        self.start_button.clicked.connect(self.start_monitoring)
        header_layout.addWidget(self.start_button)

        self.stop_button = ModernButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        header_layout.addWidget(self.stop_button)

        main_layout.addLayout(header_layout)

        # Status indicator
        self.status_label = QLabel("Monitoring: Stopped")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #666; margin: 5px 0;")
        main_layout.addWidget(self.status_label)

        # Metrics section
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QGridLayout(metrics_group)

        # Create metric widgets
        self.cpu_widget = MetricWidget("CPU Usage", "%")
        self.memory_widget = MetricWidget("Memory Usage", "%")
        self.disk_widget = MetricWidget("Disk Usage", "%")
        self.memory_avail_widget = MetricWidget("Available Memory", "GB", 8.0)

        metrics_layout.addWidget(self.cpu_widget, 0, 0)
        metrics_layout.addWidget(self.memory_widget, 0, 1)
        metrics_layout.addWidget(self.disk_widget, 1, 0)
        metrics_layout.addWidget(self.memory_avail_widget, 1, 1)

        main_layout.addWidget(metrics_group)

        # Services and alerts section
        bottom_layout = QHBoxLayout()

        # Service status
        self.service_widget = ServiceStatusWidget()
        bottom_layout.addWidget(self.service_widget)

        # Alerts
        self.alerts_widget = AlertsWidget()
        bottom_layout.addWidget(self.alerts_widget)

        main_layout.addLayout(bottom_layout)

    def start_monitoring(self):
        """Start system monitoring."""
        try:
            self.system_monitor.start_monitoring()
            self.update_timer.start(5000)  # Update every 5 seconds

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Monitoring: Active")
            self.status_label.setStyleSheet("color: #4caf50; margin: 5px 0;")

            self.monitoring_toggled.emit(True)
            logger.info("System monitoring started from admin dashboard")

        except Exception as e:
            logger.error(f"Error starting system monitoring: {e}")

    def stop_monitoring(self):
        """Stop system monitoring."""
        try:
            self.system_monitor.stop_monitoring()
            self.update_timer.stop()

            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Monitoring: Stopped")
            self.status_label.setStyleSheet("color: #666; margin: 5px 0;")

            self.monitoring_toggled.emit(False)
            logger.info("System monitoring stopped from admin dashboard")

        except Exception as e:
            logger.error(f"Error stopping system monitoring: {e}")

    def update_display(self):
        """Update the monitoring display."""
        try:
            # Get current metrics
            current_metrics = self.system_monitor.get_current_metrics()
            if current_metrics:
                # Update metric widgets
                self.cpu_widget.update_value(
                    current_metrics.cpu_percent,
                    "critical" if current_metrics.cpu_percent > 80 else
                    "warning" if current_metrics.cpu_percent > 60 else "normal"
                )

                self.memory_widget.update_value(
                    current_metrics.memory_percent,
                    "critical" if current_metrics.memory_percent > 85 else
                    "warning" if current_metrics.memory_percent > 70 else "normal"
                )

                self.disk_widget.update_value(
                    current_metrics.disk_percent,
                    "critical" if current_metrics.disk_percent > 90 else
                    "warning" if current_metrics.disk_percent > 80 else "normal"
                )

                self.memory_avail_widget.update_value(
                    current_metrics.memory_available_gb,
                    "critical" if current_metrics.memory_available_gb < 0.5 else
                    "warning" if current_metrics.memory_available_gb < 1.0 else "normal"
                )

            # Update service statuses
            service_statuses = self.system_monitor.get_service_statuses()
            for service_name, status in service_statuses.items():
                display_name = service_name.replace('_', ' ').title()
                if service_name == 'consultease':
                    display_name = 'ConsultEase'
                elif service_name == 'postgresql':
                    display_name = 'PostgreSQL'
                elif service_name == 'mosquitto':
                    display_name = 'MQTT Broker'

                self.service_widget.update_service_status(display_name, status.status)

            # Update alerts
            recent_alerts = self.system_monitor.get_recent_alerts(60)  # Last hour
            self.alerts_widget.update_alerts(recent_alerts)

        except Exception as e:
            logger.error(f"Error updating monitoring display: {e}")

    def closeEvent(self, event):
        """Handle widget close event."""
        if self.update_timer.isActive():
            self.update_timer.stop()
        event.accept()
