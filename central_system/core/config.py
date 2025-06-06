"""
Configuration settings for ConsultEase Central System.
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Settings:
    """Configuration settings for the application."""
    
    def __init__(self):
        """Initialize default settings."""
        # Database configuration
        self.DATABASE = {
            "TYPE": "sqlite",
            "PATH": "./consultease.db",
            "POOL_SIZE": 5,
            "MAX_OVERFLOW": 10,
            "POOL_TIMEOUT": 30,
            "POOL_RECYCLE": 1800
        }
        
        # MQTT configuration
        self.MQTT = {
            "BROKER": "localhost",
            "PORT": 1883,
            "KEEPALIVE": 60,
            "CLIENT_ID": "consultease_central",
            "RECONNECT_DELAY": 5
        }
        
        # System configuration
        self.SYSTEM = {
            "DEBUG": True,
            "LOG_LEVEL": "INFO",
            "SECRET_KEY": "consultease_secret_key",
            "TIMEZONE": "UTC"
        }
        
        # UI configuration
        self.UI = {
            "THEME": "default",
            "FULLSCREEN": False,
            "KEYBOARD": "auto"
        }
        
        # Load environment variables
        self._load_from_env()
        
        logger.info("Configuration loaded")
    
    def _load_from_env(self):
        """Load settings from environment variables."""
        # Database settings
        if os.environ.get("DB_TYPE"):
            self.DATABASE["TYPE"] = os.environ.get("DB_TYPE")
        if os.environ.get("DB_PATH"):
            self.DATABASE["PATH"] = os.environ.get("DB_PATH")
            
        # MQTT settings
        if os.environ.get("MQTT_BROKER"):
            self.MQTT["BROKER"] = os.environ.get("MQTT_BROKER")
        if os.environ.get("MQTT_PORT"):
            self.MQTT["PORT"] = int(os.environ.get("MQTT_PORT"))
            
        # System settings
        if os.environ.get("DEBUG"):
            self.SYSTEM["DEBUG"] = os.environ.get("DEBUG").lower() in ("true", "1", "yes")
        if os.environ.get("LOG_LEVEL"):
            self.SYSTEM["LOG_LEVEL"] = os.environ.get("LOG_LEVEL")
        if os.environ.get("SECRET_KEY"):
            self.SYSTEM["SECRET_KEY"] = os.environ.get("SECRET_KEY")
            
        # UI settings
        if os.environ.get("UI_THEME"):
            self.UI["THEME"] = os.environ.get("UI_THEME")
        if os.environ.get("UI_FULLSCREEN"):
            self.UI["FULLSCREEN"] = os.environ.get("UI_FULLSCREEN").lower() in ("true", "1", "yes")
        if os.environ.get("UI_KEYBOARD"):
            self.UI["KEYBOARD"] = os.environ.get("UI_KEYBOARD")


# Create global settings instance
settings = Settings() 