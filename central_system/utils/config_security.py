"""
Configuration security utilities for ConsultEase system.
Provides encryption and secure handling of sensitive configuration data.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class ConfigSecurity:
    """
    Handles encryption and decryption of sensitive configuration data.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize configuration security.
        
        Args:
            master_key: Master key for encryption (if None, will be generated/loaded)
        """
        self.key_file = '.consultease_key'
        self.encrypted_config_file = 'config_secure.enc'
        
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = self._load_or_generate_master_key()
        
        self.fernet = self._create_fernet()
    
    def _load_or_generate_master_key(self) -> bytes:
        """
        Load existing master key or generate a new one.
        
        Returns:
            bytes: Master key
        """
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load master key: {e}")
        
        # Generate new master key
        master_key = os.urandom(32)
        
        try:
            # Save master key with restricted permissions
            with open(self.key_file, 'wb') as f:
                f.write(master_key)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(self.key_file, 0o600)
            logger.info("Generated new master key for configuration encryption")
        except Exception as e:
            logger.error(f"Failed to save master key: {e}")
        
        return master_key
    
    def _create_fernet(self) -> Fernet:
        """
        Create Fernet encryption instance from master key.
        
        Returns:
            Fernet: Encryption instance
        """
        # Derive encryption key from master key using PBKDF2
        salt = b'consultease_salt'  # In production, use a random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key)
    
    def encrypt_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Encrypt configuration data and save to file.
        
        Args:
            config_data: Configuration dictionary to encrypt
            
        Returns:
            bool: True if successful
        """
        try:
            # Convert to JSON
            json_data = json.dumps(config_data, indent=2)
            
            # Encrypt
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            # Save to file
            with open(self.encrypted_config_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.encrypted_config_file, 0o600)
            
            logger.info("Configuration data encrypted and saved")
            return True
        except Exception as e:
            logger.error(f"Failed to encrypt configuration: {e}")
            return False
    
    def decrypt_config(self) -> Optional[Dict[str, Any]]:
        """
        Decrypt configuration data from file.
        
        Returns:
            dict: Decrypted configuration data or None if failed
        """
        if not os.path.exists(self.encrypted_config_file):
            logger.warning("Encrypted configuration file not found")
            return None
        
        try:
            # Load encrypted data
            with open(self.encrypted_config_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # Parse JSON
            config_data = json.loads(decrypted_data.decode())
            
            logger.debug("Configuration data decrypted successfully")
            return config_data
        except Exception as e:
            logger.error(f"Failed to decrypt configuration: {e}")
            return None
    
    def encrypt_value(self, value: str) -> str:
        """
        Encrypt a single value.
        
        Args:
            value: Value to encrypt
            
        Returns:
            str: Base64 encoded encrypted value
        """
        try:
            encrypted = self.fernet.encrypt(value.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            return value
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a single value.
        
        Args:
            encrypted_value: Base64 encoded encrypted value
            
        Returns:
            str: Decrypted value
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            return encrypted_value
    
    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value appears to be encrypted.
        
        Args:
            value: Value to check
            
        Returns:
            bool: True if value appears encrypted
        """
        try:
            # Try to decode as base64
            decoded = base64.b64decode(value.encode())
            # Check if it looks like Fernet token (starts with version byte)
            return len(decoded) > 32 and decoded[0] == 0x80
        except:
            return False
    
    def migrate_config_to_encrypted(self, plain_config: Dict[str, Any], 
                                   sensitive_keys: list) -> Dict[str, Any]:
        """
        Migrate plain configuration to encrypted format.
        
        Args:
            plain_config: Plain configuration dictionary
            sensitive_keys: List of keys that should be encrypted
            
        Returns:
            dict: Configuration with sensitive values encrypted
        """
        encrypted_config = plain_config.copy()
        
        for key_path in sensitive_keys:
            # Support nested keys like "database.password"
            keys = key_path.split('.')
            current = encrypted_config
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key in current and isinstance(current[key], dict):
                    current = current[key]
                else:
                    break
            else:
                # Encrypt the final key if it exists
                final_key = keys[-1]
                if final_key in current and isinstance(current[final_key], str):
                    if not self.is_encrypted(current[final_key]):
                        current[final_key] = self.encrypt_value(current[final_key])
                        logger.info(f"Encrypted configuration key: {key_path}")
        
        return encrypted_config
    
    def decrypt_config_values(self, config: Dict[str, Any], 
                             sensitive_keys: list) -> Dict[str, Any]:
        """
        Decrypt sensitive values in configuration.
        
        Args:
            config: Configuration dictionary
            sensitive_keys: List of keys that should be decrypted
            
        Returns:
            dict: Configuration with sensitive values decrypted
        """
        decrypted_config = config.copy()
        
        for key_path in sensitive_keys:
            # Support nested keys like "database.password"
            keys = key_path.split('.')
            current = decrypted_config
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key in current and isinstance(current[key], dict):
                    current = current[key]
                else:
                    break
            else:
                # Decrypt the final key if it exists and is encrypted
                final_key = keys[-1]
                if final_key in current and isinstance(current[final_key], str):
                    if self.is_encrypted(current[final_key]):
                        current[final_key] = self.decrypt_value(current[final_key])
        
        return decrypted_config


# Global configuration security instance
_config_security = None


def get_config_security() -> ConfigSecurity:
    """
    Get the global configuration security instance.
    
    Returns:
        ConfigSecurity: Global configuration security instance
    """
    global _config_security
    if _config_security is None:
        _config_security = ConfigSecurity()
    return _config_security


def encrypt_sensitive_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt sensitive configuration values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        dict: Configuration with sensitive values encrypted
    """
    sensitive_keys = [
        'database.password',
        'mqtt.password',
        'security.secret_key',
        'email.password',
        'api.secret_key'
    ]
    
    config_security = get_config_security()
    return config_security.migrate_config_to_encrypted(config, sensitive_keys)


def decrypt_sensitive_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrypt sensitive configuration values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        dict: Configuration with sensitive values decrypted
    """
    sensitive_keys = [
        'database.password',
        'mqtt.password',
        'security.secret_key',
        'email.password',
        'api.secret_key'
    ]
    
    config_security = get_config_security()
    return config_security.decrypt_config_values(config, sensitive_keys)
