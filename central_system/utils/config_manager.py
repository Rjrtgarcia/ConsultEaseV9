"""
Configuration manager for ConsultEase system.
Provides centralized configuration management with environment variable support,
validation, and security features.
"""

import os
import logging
import json
import re
from typing import Any, Dict, Optional, Union, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigManager:
    """
    Centralized configuration manager with validation and security features.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'database': {
            'url': 'sqlite:///consultease.db',
            'echo': False,
            'pool_size': 5,
            'max_overflow': 10
        },
        'mqtt': {
            'broker_host': 'localhost',
            'broker_port': 1883,
            'username': None,
            'password': None,
            'keepalive': 60,
            'qos': 1
        },
        'ui': {
            'refresh_interval': 180000,  # 3 minutes
            'max_refresh_interval': 600000,  # 10 minutes
            'cache_ttl': 120,  # 2 minutes
            'batch_update_delay': 100,  # 100ms
            'faculty_card_width': 280,
            'grid_spacing': 15
        },
        'security': {
            'password_min_length': 8,
            'password_require_uppercase': True,
            'password_require_lowercase': True,
            'password_require_digits': True,
            'password_require_special': False,
            'session_timeout': 3600,  # 1 hour
            'max_login_attempts': 5
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'consultease.log',
            'max_size': 10485760,  # 10MB
            'backup_count': 5
        },
        'performance': {
            'enable_caching': True,
            'enable_ui_batching': True,
            'enable_smart_refresh': True,
            'max_cache_size': 1000,
            'ui_update_timeout': 5000  # 5 seconds
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or os.getenv('CONSULTEASE_CONFIG', 'config.json')
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables."""
        # Load from file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                self._merge_config(self._config, file_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        # Override with environment variables
        self._load_env_config()
    
    def _load_env_config(self):
        """Load configuration from environment variables."""
        env_mappings = {
            'CONSULTEASE_DB_URL': ('database', 'url'),
            'CONSULTEASE_DB_ECHO': ('database', 'echo'),
            'CONSULTEASE_MQTT_HOST': ('mqtt', 'broker_host'),
            'CONSULTEASE_MQTT_PORT': ('mqtt', 'broker_port'),
            'CONSULTEASE_MQTT_USERNAME': ('mqtt', 'username'),
            'CONSULTEASE_MQTT_PASSWORD': ('mqtt', 'password'),
            'CONSULTEASE_LOG_LEVEL': ('logging', 'level'),
            'CONSULTEASE_LOG_FILE': ('logging', 'file'),
            'CONSULTEASE_CACHE_ENABLED': ('performance', 'enable_caching'),
            'CONSULTEASE_UI_BATCHING': ('performance', 'enable_ui_batching'),
            'CONSULTEASE_SMART_REFRESH': ('performance', 'enable_smart_refresh'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(value)
                self._config[section][key] = converted_value
                logger.debug(f"Set {section}.{key} = {converted_value} from {env_var}")
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _merge_config(self, base: Dict, override: Dict):
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _validate_config(self):
        """Validate configuration values."""
        try:
            # Validate database configuration
            db_url = self.get('database.url')
            if not db_url:
                raise ConfigValidationError("Database URL is required")
            
            # Validate MQTT configuration
            mqtt_port = self.get('mqtt.broker_port')
            if not isinstance(mqtt_port, int) or mqtt_port <= 0 or mqtt_port > 65535:
                raise ConfigValidationError("MQTT port must be between 1 and 65535")
            
            # Validate UI configuration
            refresh_interval = self.get('ui.refresh_interval')
            if not isinstance(refresh_interval, int) or refresh_interval < 1000:
                raise ConfigValidationError("UI refresh interval must be at least 1000ms")
            
            # Validate security configuration
            min_length = self.get('security.password_min_length')
            if not isinstance(min_length, int) or min_length < 4:
                raise ConfigValidationError("Password minimum length must be at least 4")
            
            logger.info("Configuration validation passed")
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigValidationError(f"Invalid configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'database.url')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        logger.debug(f"Set configuration {key} = {value}")
    
    def save(self, file_path: Optional[str] = None):
        """
        Save current configuration to file.
        
        Args:
            file_path: Path to save configuration (uses default if None)
        """
        save_path = file_path or self.config_file
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {save_path}: {e}")
            raise
    
    def validate_password(self, password: str) -> tuple[bool, List[str]]:
        """
        Validate password against security requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check minimum length
        min_length = self.get('security.password_min_length', 8)
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")
        
        # Check uppercase requirement
        if self.get('security.password_require_uppercase', True):
            if not re.search(r'[A-Z]', password):
                errors.append("Password must contain at least one uppercase letter")
        
        # Check lowercase requirement
        if self.get('security.password_require_lowercase', True):
            if not re.search(r'[a-z]', password):
                errors.append("Password must contain at least one lowercase letter")
        
        # Check digits requirement
        if self.get('security.password_require_digits', True):
            if not re.search(r'\d', password):
                errors.append("Password must contain at least one digit")
        
        # Check special characters requirement
        if self.get('security.password_require_special', False):
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return self._config.copy()


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """
    Get configuration value using dot notation.
    
    Args:
        key: Configuration key in dot notation
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any):
    """
    Set configuration value using dot notation.
    
    Args:
        key: Configuration key in dot notation
        value: Value to set
    """
    get_config_manager().set(key, value)


def validate_password(password: str) -> tuple[bool, List[str]]:
    """
    Validate password against security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return get_config_manager().validate_password(password)
