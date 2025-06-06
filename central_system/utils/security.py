import os
import hashlib
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class Security:
    """
    Security utility class for ConsultEase.
    Provides functions for password hashing, encryption, and other security operations.
    """
    
    @staticmethod
    def generate_salt():
        """
        Generate a random salt for password hashing.
        
        Returns:
            bytes: Random salt.
        """
        return os.urandom(32)
    
    @staticmethod
    def hash_password(password, salt=None):
        """
        Hash a password using PBKDF2 with SHA-256.
        
        Args:
            password (str): The password to hash.
            salt (bytes, optional): Salt to use for hashing. If None, a new salt is generated.
            
        Returns:
            tuple: (hashed_password, salt)
        """
        if salt is None:
            salt = Security.generate_salt()
        
        # Hash password using PBKDF2
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # Number of iterations
        )
        
        return password_hash, salt
    
    @staticmethod
    def verify_password(password, stored_hash, salt):
        """
        Verify a password against a stored hash.
        
        Args:
            password (str): The password to verify.
            stored_hash (bytes): The stored password hash.
            salt (bytes): The salt used for hashing.
            
        Returns:
            bool: True if password matches, False otherwise.
        """
        password_hash, _ = Security.hash_password(password, salt)
        return password_hash == stored_hash
    
    @staticmethod
    def generate_key():
        """
        Generate a Fernet encryption key.
        
        Returns:
            bytes: Encryption key.
        """
        return Fernet.generate_key()
    
    @staticmethod
    def encrypt_data(data, key):
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data (str or bytes): Data to encrypt.
            key (bytes): Encryption key.
            
        Returns:
            bytes: Encrypted data.
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        f = Fernet(key)
        return f.encrypt(data)
    
    @staticmethod
    def decrypt_data(encrypted_data, key):
        """
        Decrypt data using Fernet symmetric encryption.
        
        Args:
            encrypted_data (bytes): Data to decrypt.
            key (bytes): Encryption key.
            
        Returns:
            bytes: Decrypted data.
        """
        f = Fernet(key)
        return f.decrypt(encrypted_data)
    
    @staticmethod
    def derive_key_from_password(password, salt=None):
        """
        Derive an encryption key from a password.
        
        Args:
            password (str): Password to derive key from.
            salt (bytes, optional): Salt for key derivation. If None, a new salt is generated.
            
        Returns:
            tuple: (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        # Key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Derive key
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        
        return key, salt
    
    @staticmethod
    def generate_token(length=32):
        """
        Generate a random token.
        
        Args:
            length (int): Length of the token in bytes.
            
        Returns:
            str: Base64-encoded token.
        """
        token = os.urandom(length)
        return base64.urlsafe_b64encode(token).decode('utf-8') 