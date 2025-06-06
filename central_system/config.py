"""
Central configuration management for ConsultEase.
Provides a unified interface for accessing configuration settings from various sources.
Supports secure configuration with encrypted sensitive data.
"""
import os
import json
import logging
import pathlib

logger = logging.getLogger(__name__)

class Config:
    """Central configuration management for ConsultEase."""

    # Default configuration
    DEFAULT_CONFIG = {
        "database": {
            "type": "sqlite",
            "host": "localhost",
            "port": 5432,
            "name": "consultease",
            "user": "",
            "password": "",
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800
        },
        "mqtt": {
            "broker_host": "localhost",
            "broker_port": 1883,
            "use_tls": False,
            "username": "",
            "password": "",
            "client_id": "central_system"
        },
        "ui": {
            "fullscreen": True,
            "transition_type": "fade",
            "transition_duration": 300,
            "theme": "default"
        },
        "keyboard": {
            "type": "squeekboard",
            "fallback": "onboard"
        },
        "security": {
            "min_password_length": 8,
            "password_lockout_threshold": 5,
            "password_lockout_duration": 900,  # 15 minutes in seconds
            "session_timeout": 1800  # 30 minutes in seconds
        },
        "logging": {
            "level": "INFO",
            "file": "consultease.log",
            "max_size": 10485760,  # 10MB
            "backup_count": 5
        }
    }

    # Singleton instance
    _instance = None
    _config = None

    @classmethod
    def instance(cls):
        """Get the singleton instance of the configuration manager."""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    def __init__(self):
        """Initialize the configuration manager."""
        # Prevent multiple initialization of the singleton
        if Config._instance is not None:
            return

        # Load configuration
        self._config = self.load()

    @classmethod
    def load(cls):
        """Load configuration from file or environment with security support."""
        config = cls.DEFAULT_CONFIG.copy()

        # Try to load from encrypted config first
        try:
            from .utils.config_security import get_config_security, decrypt_sensitive_config
            config_security = get_config_security()
            encrypted_config = config_security.decrypt_config()

            if encrypted_config:
                # Update config with encrypted file values
                cls._update_dict(config, encrypted_config)
                logger.info("Loaded configuration from encrypted file")
            else:
                # Fall back to plain text config files
                cls._load_plain_config(config)
        except ImportError:
            # Config security not available, use plain text
            logger.warning("Configuration security not available, using plain text config")
            cls._load_plain_config(config)
        except Exception as e:
            logger.error(f"Failed to load encrypted configuration: {e}")
            cls._load_plain_config(config)

        # Override with environment variables
        cls._override_from_env(config)

        # Decrypt sensitive values if they're encrypted
        try:
            from .utils.config_security import decrypt_sensitive_config
            config = decrypt_sensitive_config(config)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Failed to decrypt sensitive configuration values: {e}")

        return config

    @classmethod
    def _load_plain_config(cls, config):
        """Load configuration from plain text files."""
        config_paths = [
            os.environ.get('CONSULTEASE_CONFIG'),
            'config.json',
            os.path.join(os.path.dirname(__file__), 'config.json'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        ]

        for config_path in config_paths:
            if config_path and os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        file_config = json.load(f)
                        # Update config with file values
                        cls._update_dict(config, file_config)
                    logger.info(f"Loaded configuration from {config_path}")
                    break
                except Exception as e:
                    logger.error(f"Failed to load configuration from {config_path}: {e}")

    @staticmethod
    def _update_dict(target, source):
        """
        Recursively update a dictionary with values from another dictionary.

        Args:
            target (dict): Target dictionary to update
            source (dict): Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                Config._update_dict(target[key], value)
            else:
                target[key] = value

    @staticmethod
    def _override_from_env(config):
        """
        Override configuration values from environment variables.

        Args:
            config (dict): Configuration dictionary to update
        """
        # Database configuration
        if 'DB_TYPE' in os.environ:
            config['database']['type'] = os.environ['DB_TYPE']
        if 'DB_HOST' in os.environ:
            config['database']['host'] = os.environ['DB_HOST']
        if 'DB_PORT' in os.environ:
            config['database']['port'] = int(os.environ['DB_PORT'])
        if 'DB_NAME' in os.environ:
            config['database']['name'] = os.environ['DB_NAME']
        if 'DB_USER' in os.environ:
            config['database']['user'] = os.environ['DB_USER']
        if 'DB_PASSWORD' in os.environ:
            config['database']['password'] = os.environ['DB_PASSWORD']
        if 'DB_POOL_SIZE' in os.environ:
            config['database']['pool_size'] = int(os.environ['DB_POOL_SIZE'])
        if 'DB_MAX_OVERFLOW' in os.environ:
            config['database']['max_overflow'] = int(os.environ['DB_MAX_OVERFLOW'])

        # MQTT configuration
        if 'MQTT_BROKER_HOST' in os.environ:
            config['mqtt']['broker_host'] = os.environ['MQTT_BROKER_HOST']
        if 'MQTT_BROKER_PORT' in os.environ:
            config['mqtt']['broker_port'] = int(os.environ['MQTT_BROKER_PORT'])
        if 'MQTT_USERNAME' in os.environ:
            config['mqtt']['username'] = os.environ['MQTT_USERNAME']
        if 'MQTT_PASSWORD' in os.environ:
            config['mqtt']['password'] = os.environ['MQTT_PASSWORD']

        # UI configuration
        if 'CONSULTEASE_FULLSCREEN' in os.environ:
            config['ui']['fullscreen'] = os.environ['CONSULTEASE_FULLSCREEN'].lower() in ('true', 'yes', '1')
        if 'CONSULTEASE_THEME' in os.environ:
            config['ui']['theme'] = os.environ['CONSULTEASE_THEME']

        # Keyboard configuration
        if 'CONSULTEASE_KEYBOARD' in os.environ:
            config['keyboard']['type'] = os.environ['CONSULTEASE_KEYBOARD']

    def get(self, key, default=None):
        """
        Get a configuration value by key.

        Args:
            key (str): Configuration key (dot notation for nested keys)
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key, value):
        """
        Set a configuration value by key.

        Args:
            key (str): Configuration key (dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def save(self, config_path=None, encrypt_sensitive=True):
        """
        Save the configuration to a file with optional encryption.

        Args:
            config_path (str, optional): Path to save the configuration file
            encrypt_sensitive (bool): Whether to encrypt sensitive values

        Returns:
            bool: True if successful, False otherwise
        """
        if not config_path:
            config_path = os.environ.get('CONSULTEASE_CONFIG', 'config.json')

        try:
            config_to_save = self._config.copy()

            # Encrypt sensitive values if requested
            if encrypt_sensitive:
                try:
                    from .utils.config_security import encrypt_sensitive_config, get_config_security
                    config_to_save = encrypt_sensitive_config(config_to_save)

                    # Save as encrypted file
                    config_security = get_config_security()
                    success = config_security.encrypt_config(config_to_save)
                    if success:
                        logger.info("Saved encrypted configuration")
                        return True
                except ImportError:
                    logger.warning("Configuration security not available, saving as plain text")
                except Exception as e:
                    logger.error(f"Failed to encrypt configuration: {e}")

            # Fall back to plain text save
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)

            # Write configuration to file
            with open(config_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)

            logger.info(f"Saved configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            return False

    def migrate_to_secure_config(self):
        """
        Migrate current configuration to encrypted format.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from .utils.config_security import encrypt_sensitive_config, get_config_security

            # Encrypt sensitive values
            encrypted_config = encrypt_sensitive_config(self._config)

            # Save encrypted configuration
            config_security = get_config_security()
            success = config_security.encrypt_config(encrypted_config)

            if success:
                logger.info("Successfully migrated configuration to encrypted format")
                return True
            else:
                logger.error("Failed to save encrypted configuration")
                return False
        except ImportError:
            logger.error("Configuration security not available for migration")
            return False
        except Exception as e:
            logger.error(f"Failed to migrate configuration to encrypted format: {e}")
            return False

# Convenience function to get the configuration instance
def get_config():
    """Get the configuration instance."""
    return Config.instance()
