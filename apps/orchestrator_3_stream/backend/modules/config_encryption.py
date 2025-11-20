#!/usr/bin/env python3
"""
Configuration Encryption Module

Handles encryption and decryption of sensitive configuration data
including passwords, private keys, certificates, and other secrets.
Supports multiple encryption methods and key management.
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Optional, Dict, Any, Union, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .logger import get_logger
from .config_models import EncryptionMethod

logger = get_logger()


class EncryptionError(Exception):
    """Base exception for encryption operations"""
    pass


class KeyManagementError(Exception):
    """Exception for key management operations"""
    pass


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive configuration data.

    Supports multiple encryption methods and provides secure key management
    with local key storage and optional AWS KMS integration.
    """

    def __init__(
        self,
        encryption_method: EncryptionMethod = EncryptionMethod.AES256_GCM,
        master_key_path: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_kms_key_id: Optional[str] = None
    ):
        """
        Initialize encryption manager.

        Args:
            encryption_method: Primary encryption method to use
            master_key_path: Path to master key file (for local key storage)
            aws_region: AWS region for KMS operations
            aws_kms_key_id: AWS KMS key ID for envelope encryption
        """
        self.encryption_method = encryption_method
        self.master_key_path = master_key_path or os.getenv("ENV_SYNC_KEY_PATH", os.path.expanduser("~/.env_sync/master.key"))
        self.aws_region = aws_region or os.getenv("AWS_REGION")
        self.aws_kms_key_id = aws_kms_key_id or os.getenv("AWS_KMS_KEY_ID")

        # Initialize encryption backends
        self._master_key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
        self._aesgcm: Optional[AESGCM] = None
        self._chacha: Optional[ChaCha20Poly1305] = None
        self._kms_client = None

        # Load or create master key
        self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize encryption backend with master key"""
        try:
            # Load or generate master key
            if not os.path.exists(self.master_key_path):
                logger.info(f"Generating new master key at {self.master_key_path}")
                self._generate_master_key()

            self._master_key = self._load_master_key()

            # Initialize encryption backends based on method
            if self.encryption_method == EncryptionMethod.AES256_GCM:
                self._aesgcm = AESGCM(self._master_key)
                logger.debug("Initialized AES-256-GCM encryption")
            elif self.encryption_method == EncryptionMethod.CHACHA20_POLY1305:
                self._chacha = ChaCha20Poly1305(self._master_key)
                logger.debug("Initialized ChaCha20-Poly1305 encryption")

            # Also initialize Fernet for compatibility
            self._fernet = Fernet(base64.urlsafe_b64encode(self._master_key[:32]))

            # Initialize KMS client if AWS credentials are available
            if self.aws_region and self.aws_kms_key_id:
                try:
                    self._kms_client = boto3.client('kms', region_name=self.aws_region)
                    logger.info("AWS KMS client initialized")
                except NoCredentialsError:
                    logger.warning("AWS credentials not found, KMS integration disabled")

            logger.success("Encryption manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize encryption manager: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")

    def _generate_master_key(self):
        """Generate and store a new master key"""
        try:
            # Generate secure random key
            master_key = secrets.token_bytes(32)  # 256-bit key

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.master_key_path), mode=0o700, exist_ok=True)

            # Store key with secure permissions
            with open(self.master_key_path, "wb") as f:
                os.chmod(self.master_key_path, 0o600)  # Owner read/write only
                f.write(master_key)

            logger.info(f"Master key generated and stored at {self.master_key_path}")

        except Exception as e:
            raise KeyManagementError(f"Failed to generate master key: {e}")

    def _load_master_key(self) -> bytes:
        """Load master key from file"""
        try:
            with open(self.master_key_path, "rb") as f:
                master_key = f.read()

            if len(master_key) < 32:
                raise KeyManagementError("Master key too short (minimum 32 bytes)")

            return master_key[:32]  # Use first 32 bytes

        except FileNotFoundError:
            raise KeyManagementError(f"Master key file not found: {self.master_key_path}")
        except Exception as e:
            raise KeyManagementError(f"Failed to load master key: {e}")

    def encrypt(self, data: Union[str, bytes], context: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Encrypt sensitive data.

        Args:
            data: Data to encrypt (string or bytes)
            context: Additional context for encryption (used with KMS)

        Returns:
            Dictionary containing encrypted data with metadata
        """
        try:
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data

            # Use KMS if available and configured
            if self._kms_client and context:
                return self._encrypt_with_kms(data_bytes, context)

            # Use local encryption
            return self._encrypt_locally(data_bytes)

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, encrypted_data: Dict[str, Any]) -> Union[str, bytes]:
        """
        Decrypt sensitive data.

        Args:
            encrypted_data: Dictionary containing encrypted data with metadata

        Returns:
            Decrypted data (string if original was string, bytes otherwise)
        """
        try:
            # Check for KMS encryption
            if 'kms_encrypted' in encrypted_data and encrypted_data.get('kms_encrypted'):
                return self._decrypt_with_kms(encrypted_data)

            # Use local decryption
            return self._decrypt_locally(encrypted_data)

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")

    def _encrypt_locally(self, data: bytes) -> Dict[str, Any]:
        """Encrypt data using local encryption"""
        try:
            timestamp = datetime.utcnow().isoformat()

            if self.encryption_method == EncryptionMethod.AES256_GCM:
                # Generate nonce for AES-GCM
                nonce = secrets.token_bytes(12)  # 96-bit nonce
                encrypted_data = self._aesgcm.encrypt(nonce, data, None)

                result = {
                    'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                    'nonce': base64.b64encode(nonce).decode('utf-8'),
                    'encryption_method': self.encryption_method.value,
                    'timestamp': timestamp,
                    'kms_encrypted': False
                }

            elif self.encryption_method == EncryptionMethod.CHACHA20_POLY1305:
                # Generate nonce for ChaCha20-Poly1305
                nonce = secrets.token_bytes(12)  # 96-bit nonce
                encrypted_data = self._chacha.encrypt(nonce, data, None)

                result = {
                    'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                    'nonce': base64.b64encode(nonce).decode('utf-8'),
                    'encryption_method': self.encryption_method.value,
                    'timestamp': timestamp,
                    'kms_encrypted': False
                }
            else:
                # Fallback to Fernet for compatibility
                encrypted_data = self._fernet.encrypt(data)
                result = {
                    'encrypted_data': encrypted_data.decode('utf-8'),
                    'encryption_method': 'fernet',
                    'timestamp': timestamp,
                    'kms_encrypted': False
                }

            logger.debug(f"Data encrypted using {self.encryption_method.value}")
            return result

        except Exception as e:
            raise EncryptionError(f"Local encryption failed: {e}")

    def _decrypt_locally(self, encrypted_data: Dict[str, Any]) -> Union[str, bytes]:
        """Decrypt data using local encryption"""
        try:
            encryption_method = encrypted_data.get('encryption_method')
            encrypted_bytes = base64.b64decode(encrypted_data['encrypted_data'])

            if encryption_method == EncryptionMethod.AES256_GCM.value:
                nonce = base64.b64decode(encrypted_data['nonce'])
                decrypted_data = self._aesgcm.decrypt(nonce, encrypted_bytes, None)

            elif encryption_method == EncryptionMethod.CHACHA20_POLY1305.value:
                nonce = base64.b64decode(encrypted_data['nonce'])
                decrypted_data = self._chacha.decrypt(nonce, encrypted_bytes, None)

            elif encryption_method == 'fernet':
                decrypted_data = self._fernet.decrypt(encrypted_bytes)

            else:
                raise EncryptionError(f"Unsupported encryption method: {encryption_method}")

            logger.debug(f"Data decrypted using {encryption_method}")

            # Return string if original was likely string (heuristic)
            try:
                return decrypted_data.decode('utf-8')
            except UnicodeDecodeError:
                return decrypted_data

        except Exception as e:
            raise EncryptionError(f"Local decryption failed: {e}")

    def _encrypt_with_kms(self, data: bytes, context: Dict[str, str]) -> Dict[str, Any]:
        """Encrypt data using AWS KMS envelope encryption"""
        try:
            # Generate data key
            response = self._kms_client.generate_data_key(
                KeyId=self.aws_kms_key_id,
                EncryptionContext=context,
                KeySpec='AES_256'
            )

            plaintext_key = response['Plaintext']
            encrypted_key = response['CiphertextBlob']

            # Encrypt data with generated key
            aesgcm = AESGCM(plaintext_key)
            nonce = secrets.token_bytes(12)
            encrypted_data = aesgcm.encrypt(nonce, data, None)

            result = {
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
                'nonce': base64.b64encode(nonce).decode('utf-8'),
                'encryption_method': 'kms_envelope',
                'kms_key_id': self.aws_kms_key_id,
                'encryption_context': context,
                'timestamp': datetime.utcnow().isoformat(),
                'kms_encrypted': True
            }

            logger.debug("Data encrypted using AWS KMS envelope encryption")
            return result

        except ClientError as e:
            raise EncryptionError(f"KMS encryption failed: {e}")

    def _decrypt_with_kms(self, encrypted_data: Dict[str, Any]) -> Union[str, bytes]:
        """Decrypt data using AWS KMS envelope encryption"""
        try:
            # Decrypt data key
            response = self._kms_client.decrypt(
                CiphertextBlob=base64.b64decode(encrypted_data['encrypted_key']),
                EncryptionContext=encrypted_data.get('encryption_context', {})
            )

            plaintext_key = response['Plaintext']

            # Decrypt data with decrypted key
            aesgcm = AESGCM(plaintext_key)
            nonce = base64.b64decode(encrypted_data['nonce'])
            encrypted_bytes = base64.b64decode(encrypted_data['encrypted_data'])
            decrypted_data = aesgcm.decrypt(nonce, encrypted_bytes, None)

            logger.debug("Data decrypted using AWS KMS envelope encryption")

            # Return string if original was likely string
            try:
                return decrypted_data.decode('utf-8')
            except UnicodeDecodeError:
                return decrypted_data

        except ClientError as e:
            raise EncryptionError(f"KMS decryption failed: {e}")

    def encrypt_auth_method(self, auth_method: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in authentication method.

        Args:
            auth_method: Authentication method dictionary

        Returns:
            Auth method with sensitive fields encrypted
        """
        try:
            encrypted_auth = auth_method.copy()

            # Fields to encrypt
            sensitive_fields = ['password', 'private_key_data', 'certificate_data', 'passphrase']

            for field in sensitive_fields:
                if field in encrypted_auth and encrypted_auth[field]:
                    context = {'field': field, 'type': 'auth_method'}
                    encrypted_auth[field] = self.encrypt(encrypted_auth[field], context)

            logger.debug("Authentication method encrypted")
            return encrypted_auth

        except Exception as e:
            raise EncryptionError(f"Failed to encrypt auth method: {e}")

    def decrypt_auth_method(self, encrypted_auth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in authentication method.

        Args:
            encrypted_auth: Authentication method with encrypted fields

        Returns:
            Auth method with sensitive fields decrypted
        """
        try:
            decrypted_auth = encrypted_auth.copy()

            # Fields to decrypt
            sensitive_fields = ['password', 'private_key_data', 'certificate_data', 'passphrase']

            for field in sensitive_fields:
                if field in decrypted_auth and isinstance(decrypted_auth[field], dict):
                    decrypted_auth[field] = self.decrypt(decrypted_auth[field])
                elif field in decrypted_auth and decrypted_auth[field]:
                    # Might be a string (legacy format)
                    try:
                        if isinstance(decrypted_auth[field], str) and decrypted_auth[field].startswith('{'):
                            # Try to parse as JSON encrypted data
                            encrypted_dict = json.loads(decrypted_auth[field])
                            decrypted_auth[field] = self.decrypt(encrypted_dict)
                    except (json.JSONDecodeError, EncryptionError):
                        # Leave as-is if it's not encrypted
                        pass

            logger.debug("Authentication method decrypted")
            return decrypted_auth

        except Exception as e:
            raise EncryptionError(f"Failed to decrypt auth method: {e}")

    def rotate_key(self, new_key_path: Optional[str] = None) -> bool:
        """
        Rotate encryption key.

        Args:
            new_key_path: Path for new key file (optional)

        Returns:
            True if rotation successful
        """
        try:
            logger.info("Starting encryption key rotation")

            # Generate new key
            new_key_path = new_key_path or f"{self.master_key_path}.new"
            old_master_key = self._master_key

            # Create backup of old key
            backup_path = f"{self.master_key_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(self.master_key_path, "rb") as src, open(backup_path, "wb") as dst:
                dst.write(src.read())
            os.chmod(backup_path, 0o600)

            # Generate new master key
            self._generate_master_key()
            self._master_key = self._load_master_key()

            # Re-initialize encryption backends
            self._initialize_encryption()

            logger.success(f"Key rotation completed. Old key backed up to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            # Restore old key if rotation failed
            if 'old_master_key' in locals():
                self._master_key = old_master_key
                self._initialize_encryption()
            return False

    def validate_key_access(self) -> bool:
        """
        Validate that encryption key is accessible and functional.

        Returns:
            True if key access is valid
        """
        try:
            test_data = "test_validation_data"

            # Encrypt and decrypt test data
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)

            if decrypted == test_data:
                logger.debug("Encryption key access validation successful")
                return True
            else:
                logger.error("Encryption key validation failed: data mismatch")
                return False

        except Exception as e:
            logger.error(f"Encryption key validation failed: {e}")
            return False

    def get_encryption_info(self) -> Dict[str, Any]:
        """
        Get information about current encryption configuration.

        Returns:
            Dictionary with encryption configuration details
        """
        return {
            'encryption_method': self.encryption_method.value,
            'master_key_path': self.master_key_path,
            'key_accessible': self.validate_key_access(),
            'kms_enabled': self._kms_client is not None,
            'aws_region': self.aws_region,
            'kms_key_id': self.aws_kms_key_id if self._kms_client else None
        }


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get the global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def initialize_encryption_manager(
    encryption_method: EncryptionMethod = EncryptionMethod.AES256_GCM,
    master_key_path: Optional[str] = None,
    aws_region: Optional[str] = None,
    aws_kms_key_id: Optional[str] = None
) -> EncryptionManager:
    """
    Initialize the global encryption manager.

    Args:
        encryption_method: Primary encryption method
        master_key_path: Path to master key file
        aws_region: AWS region for KMS
        aws_kms_key_id: AWS KMS key ID

    Returns:
        Initialized encryption manager
    """
    global _encryption_manager
    _encryption_manager = EncryptionManager(
        encryption_method=encryption_method,
        master_key_path=master_key_path,
        aws_region=aws_region,
        aws_kms_key_id=aws_kms_key_id
    )
    return _encryption_manager