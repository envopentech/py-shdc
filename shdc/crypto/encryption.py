"""
SHDC Cryptographic Operations

This module implements all cryptographic functions required by the SHDC v1.0 protocol,
including Ed25519 digital signatures and AES-256-GCM encryption.
"""

import hashlib
import secrets
from typing import Optional, Tuple, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Constants for cryptographic operations
ED25519_PUBLIC_KEY_SIZE = 32
ED25519_PRIVATE_KEY_SIZE = 32
ED25519_SIGNATURE_SIZE = 64
AES_KEY_SIZE = 32
AES_NONCE_SIZE = 12
AES_TAG_SIZE = 16


class SHDCCryptoError(Exception):
    """Exception raised for cryptographic errors in SHDC operations"""

    pass


def generate_nonce() -> bytes:
    """
    Generate a cryptographically secure 96-bit (12-byte) nonce for AES-GCM.

    Returns:
        12-byte random nonce
    """
    return secrets.token_bytes(AES_NONCE_SIZE)


def secure_compare(a: bytes, b: bytes) -> bool:
    """
    Perform constant-time comparison of two byte strings.

    Args:
        a: First byte string
        b: Second byte string

    Returns:
        True if strings are equal, False otherwise
    """
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= x ^ y

    return result == 0


def zero_memory(data: Union[bytearray, memoryview]) -> None:
    """
    Securely zero out memory containing sensitive data.

    Args:
        data: Mutable byte array to zero out
    """
    if isinstance(data, bytearray):
        for i in range(len(data)):
            data[i] = 0
    elif isinstance(data, memoryview):
        for i in range(len(data)):
            data[i] = 0


class SHDCCrypto:
    """
    SHDC Cryptographic Operations

    Provides all cryptographic primitives required by the SHDC v1.0 protocol,
    including Ed25519 signatures and AES-256-GCM encryption.
    """

    @staticmethod
    def generate_ed25519_keypair() -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        """
        Generate a new Ed25519 keypair for device identity.

        Returns:
            Tuple of (private_key, public_key)
        """
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def serialize_ed25519_private_key(private_key: Ed25519PrivateKey) -> bytes:
        """
        Serialize Ed25519 private key to bytes.

        Args:
            private_key: Ed25519 private key

        Returns:
            32-byte private key
        """
        return private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    @staticmethod
    def serialize_ed25519_public_key(public_key: Ed25519PublicKey) -> bytes:
        """
        Serialize Ed25519 public key to bytes.

        Args:
            public_key: Ed25519 public key

        Returns:
            32-byte public key
        """
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )

    @staticmethod
    def deserialize_ed25519_private_key(key_bytes: bytes) -> Ed25519PrivateKey:
        """
        Deserialize Ed25519 private key from bytes.

        Args:
            key_bytes: 32-byte private key

        Returns:
            Ed25519 private key object
        """
        if len(key_bytes) != ED25519_PRIVATE_KEY_SIZE:
            raise SHDCCryptoError(f"Invalid private key size: {len(key_bytes)}")

        return Ed25519PrivateKey.from_private_bytes(key_bytes)

    @staticmethod
    def deserialize_ed25519_public_key(key_bytes: bytes) -> Ed25519PublicKey:
        """
        Deserialize Ed25519 public key from bytes.

        Args:
            key_bytes: 32-byte public key

        Returns:
            Ed25519 public key object
        """
        if len(key_bytes) != ED25519_PUBLIC_KEY_SIZE:
            raise SHDCCryptoError(f"Invalid public key size: {len(key_bytes)}")

        return Ed25519PublicKey.from_public_bytes(key_bytes)

    @staticmethod
    def sign_message(private_key: Ed25519PrivateKey, message: bytes) -> bytes:
        """
        Sign a message using Ed25519.

        Args:
            private_key: Ed25519 private key
            message: Message to sign

        Returns:
            64-byte signature
        """
        return private_key.sign(message)

    @staticmethod
    def verify_signature(
        public_key: Ed25519PublicKey, message: bytes, signature: bytes
    ) -> bool:
        """
        Verify an Ed25519 signature.

        Args:
            public_key: Ed25519 public key
            message: Original message
            signature: 64-byte signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if len(signature) != ED25519_SIGNATURE_SIZE:
                return False

            public_key.verify(signature, message)
            return True
        except Exception:
            return False

    @staticmethod
    def generate_aes_key() -> bytes:
        """
        Generate a random 256-bit AES key.

        Returns:
            32-byte AES key
        """
        return secrets.token_bytes(AES_KEY_SIZE)

    @staticmethod
    def generate_replay_nonce() -> bytes:
        """
        Generate a cryptographically secure nonce for replay protection.

        Returns:
            12-byte nonce
        """
        return generate_nonce()

    @staticmethod
    def encrypt_aes_gcm(
        key: bytes,
        plaintext: bytes,
        nonce: Optional[bytes] = None,
        associated_data: Optional[bytes] = None,
    ) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256-GCM.

        Args:
            key: 32-byte AES key
            plaintext: Data to encrypt
            nonce: 12-byte nonce (generated if not provided)
            associated_data: Optional associated data for authentication

        Returns:
            Tuple of (nonce, ciphertext_with_tag)
        """
        if len(key) != AES_KEY_SIZE:
            raise SHDCCryptoError(f"Invalid AES key size: {len(key)}")

        if nonce is None:
            nonce = generate_nonce()
        elif len(nonce) != AES_NONCE_SIZE:
            raise SHDCCryptoError(f"Invalid nonce size: {len(nonce)}")

        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)

        return nonce, ciphertext

    @staticmethod
    def decrypt_aes_gcm(
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Args:
            key: 32-byte AES key
            nonce: 12-byte nonce
            ciphertext: Encrypted data with authentication tag
            associated_data: Optional associated data for authentication

        Returns:
            Decrypted plaintext

        Raises:
            SHDCCryptoError: If decryption fails
        """
        if len(key) != AES_KEY_SIZE:
            raise SHDCCryptoError(f"Invalid AES key size: {len(key)}")

        if len(nonce) != AES_NONCE_SIZE:
            raise SHDCCryptoError(f"Invalid nonce size: {len(nonce)}")

        try:
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
            return plaintext
        except Exception as e:
            raise SHDCCryptoError(f"Decryption failed: {e}")

    @staticmethod
    def derive_session_key(
        shared_secret: bytes, device_id_a: int, device_id_b: int
    ) -> bytes:
        """
        Derive session key from shared secret and device IDs.

        Args:
            shared_secret: Shared secret bytes
            device_id_a: First device ID
            device_id_b: Second device ID

        Returns:
            32-byte derived session key
        """
        # Create salt from device IDs
        salt = device_id_a.to_bytes(4, "big") + device_id_b.to_bytes(4, "big")

        # Use HKDF to derive session key
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=AES_KEY_SIZE,
            salt=salt,
            info=b"SHDC_SESSION_KEY",
        )

        return hkdf.derive(shared_secret)

    @staticmethod
    def derive_broadcast_key(master_key: bytes, key_version: int) -> bytes:
        """
        Derive broadcast key from master key and version.

        Args:
            master_key: 32-byte master broadcast key
            key_version: Key version identifier (0-255)

        Returns:
            32-byte derived broadcast key
        """
        if len(master_key) != AES_KEY_SIZE:
            raise SHDCCryptoError(f"Invalid master key size: {len(master_key)}")

        if not (0 <= key_version <= 255):
            raise SHDCCryptoError(f"Invalid key version: {key_version}")

        # Create salt from key version
        salt = key_version.to_bytes(4, "big") + b"BROADCAST"

        # Use HKDF to derive broadcast key
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=AES_KEY_SIZE,
            salt=salt,
            info=b"SHDC_BROADCAST_KEY",
        )

        return hkdf.derive(master_key)

    @staticmethod
    def hash_device_fingerprint(
        device_id: int, public_key: bytes, device_type: str
    ) -> bytes:
        """
        Create a secure hash of device information for fingerprinting.

        Args:
            device_id: 32-bit device identifier
            public_key: Device's Ed25519 public key
            device_type: Device type string

        Returns:
            32-byte SHA-256 hash
        """
        hasher = hashlib.sha256()
        hasher.update(device_id.to_bytes(4, "big"))
        hasher.update(public_key)
        hasher.update(device_type.encode("utf-8"))
        return hasher.digest()

    @staticmethod
    def constant_time_verify(expected: bytes, actual: bytes) -> bool:
        """
        Perform constant-time verification of byte strings.

        Args:
            expected: Expected value
            actual: Actual value to verify

        Returns:
            True if values match, False otherwise
        """
        return secure_compare(expected, actual)

    @staticmethod
    def secure_random_bytes(length: int) -> bytes:
        """
        Generate cryptographically secure random bytes.

        Args:
            length: Number of bytes to generate

        Returns:
            Random bytes
        """
        return secrets.token_bytes(length)

    @staticmethod
    def create_message_hash(message_data: bytes) -> bytes:
        """
        Create SHA-256 hash of message data.

        Args:
            message_data: Message bytes to hash

        Returns:
            32-byte SHA-256 hash
        """
        return hashlib.sha256(message_data).digest()
