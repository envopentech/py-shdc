"""
SHDC Cryptographic Package

Cryptographic operations and key management for the SHDC protocol.

This package provides:
- encryption: Core cryptographic functions using Ed25519 and AES-256-GCM
- keys: Key generation, storage, rotation, and lifecycle management

The crypto package implements the security foundation of the SHDC protocol,
ensuring all communications are properly authenticated and encrypted according
to the SHDC v1.0 specification.

Security Features:
- Ed25519 digital signatures for device authentication
- AES-256-GCM encryption for message confidentiality
- Secure key storage with automatic rotation
- Defense against replay attacks and tampering
"""

from .encryption import (  # Constants
    AES_KEY_SIZE,
    AES_NONCE_SIZE,
    AES_TAG_SIZE,
    ED25519_PRIVATE_KEY_SIZE,
    ED25519_PUBLIC_KEY_SIZE,
    ED25519_SIGNATURE_SIZE,
    SHDCCrypto,
    SHDCCryptoError,
    generate_nonce,
    secure_compare,
    zero_memory,
)
from .keys import KeyInfo, KeyManager

__all__ = [
    # Main crypto class
    "SHDCCrypto",
    # Utility functions
    "generate_nonce",
    "secure_compare",
    "zero_memory",
    # Key management
    "KeyManager",
    "KeyInfo",
    # Exceptions
    "SHDCCryptoError",
    # Constants
    "ED25519_PUBLIC_KEY_SIZE",
    "ED25519_PRIVATE_KEY_SIZE",
    "ED25519_SIGNATURE_SIZE",
    "AES_KEY_SIZE",
    "AES_NONCE_SIZE",
    "AES_TAG_SIZE",
]
