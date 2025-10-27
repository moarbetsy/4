"""
Cryptographic utilities for secure storage of sensitive data like proxy credentials.
"""
import os
import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class CryptoManager:
    """Manages encryption/decryption of sensitive data using Fernet symmetric encryption."""
    
    def __init__(self, key_file: str = "encryption.key"):
        self.key_file = key_file
        self._fernet = None
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption with existing key or create new one."""
        try:
            if os.path.exists(self.key_file):
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                self._fernet = Fernet(key)
                logger.info("Loaded existing encryption key")
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions (owner read/write only)
                os.chmod(self.key_file, 0o600)
                self._fernet = Fernet(key)
                logger.info("Generated new encryption key")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise RuntimeError("Encryption initialization failed. Cannot store sensitive data securely.")
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")
        
        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext and return plaintext string."""
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")
        
        try:
            encrypted_bytes = base64.b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if encryption is properly initialized."""
        return self._fernet is not None

# Global crypto manager instance
_crypto_manager: Optional[CryptoManager] = None

def get_crypto_manager() -> CryptoManager:
    """Get the global crypto manager instance."""
    global _crypto_manager
    if _crypto_manager is None:
        _crypto_manager = CryptoManager()
    return _crypto_manager

def encrypt_sensitive_data(data: str) -> str:
    """Convenience function to encrypt sensitive data."""
    return get_crypto_manager().encrypt(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Convenience function to decrypt sensitive data."""
    return get_crypto_manager().decrypt(encrypted_data)

def is_encryption_available() -> bool:
    """Check if encryption is available."""
    try:
        return get_crypto_manager().is_available()
    except Exception:
        return False