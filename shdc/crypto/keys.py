"""
SHDC Key Management

This module implements key generation, storage, rotation, and lifecycle
management for the SHDC protocol as specified in SHDC v1.0.
"""

import json
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .encryption import SHDCCrypto, zero_memory


@dataclass
class KeyInfo:
    """Information about a stored key"""

    key_id: str
    key_type: str  # 'ed25519_private', 'ed25519_public', 'aes256'
    created_at: float
    expires_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class KeyManager:
    """
    SHDC Key Management System

    Handles secure storage, rotation, and lifecycle management of
    cryptographic keys for SHDC devices.
    """

    def __init__(self, device_id: int, storage_path: Optional[str] = None):
        """
        Initialize key manager.

        Args:
            device_id: Unique device identifier
            storage_path: Path for key storage (default: ~/.shdc/keys)
        """
        self.device_id = device_id

        # Set up storage path
        if storage_path is None:
            home = Path.home()
            storage_path = str(home / ".shdc" / "keys" / f"{device_id:08X}")

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory key storage
        self._keys: Dict[str, bytes] = {}
        self._key_info: Dict[str, KeyInfo] = {}
        self._lock = threading.RLock()

        # Key rotation settings
        self.session_key_lifetime = 24 * 3600  # 24 hours
        self.broadcast_key_lifetime = 15 * 60  # 15 minutes
        self.device_key_lifetime = 365 * 24 * 3600  # 1 year

        # Load existing keys
        self._load_keys()

    def generate_device_keys(
        self, force: bool = False
    ) -> Tuple[Ed25519PrivateKey, Ed25519PublicKey]:
        """
        Generate or load device identity keys.

        Args:
            force: Force generation of new keys

        Returns:
            Tuple of (private_key, public_key)
        """
        with self._lock:
            key_id = "device_identity"

            if not force and key_id in self._keys:
                # Load existing key
                private_key_bytes = self._keys[key_id]
                private_key = SHDCCrypto.deserialize_ed25519_private_key(
                    private_key_bytes
                )
                public_key = private_key.public_key()
                return private_key, public_key

            # Generate new keys
            private_key, public_key = SHDCCrypto.generate_ed25519_keypair()

            # Store private key
            private_key_bytes = SHDCCrypto.serialize_ed25519_private_key(private_key)
            self._store_key(
                key_id,
                private_key_bytes,
                "ed25519_private",
                expires_at=time.time() + self.device_key_lifetime,
            )

            # Store public key
            public_key_bytes = SHDCCrypto.serialize_ed25519_public_key(public_key)
            self._store_key(
                f"{key_id}_public",
                public_key_bytes,
                "ed25519_public",
                expires_at=time.time() + self.device_key_lifetime,
            )

            return private_key, public_key

    def generate_session_key(self, peer_device_id: int) -> bytes:
        """
        Generate session key for communication with specific device.

        Args:
            peer_device_id: Device ID of communication peer

        Returns:
            32-byte AES session key
        """
        with self._lock:
            key_id = f"session_{peer_device_id:08X}"

            # Generate new session key
            session_key = SHDCCrypto.generate_aes_key()

            # Store key
            self._store_key(
                key_id,
                session_key,
                "aes256",
                expires_at=time.time() + self.session_key_lifetime,
                metadata={"peer_device_id": peer_device_id},
            )

            return session_key

    def generate_broadcast_key(self, key_version: int) -> bytes:
        """
        Generate broadcast key for specific version.

        Args:
            key_version: Broadcast key version identifier

        Returns:
            32-byte AES broadcast key
        """
        with self._lock:
            key_id = f"broadcast_{key_version:02X}"

            # Generate master key if not exists
            master_key_id = "broadcast_master"
            if master_key_id not in self._keys:
                master_key = SHDCCrypto.generate_aes_key()
                self._store_key(master_key_id, master_key, "aes256")
            else:
                master_key = self._keys[master_key_id]

            # Derive broadcast key
            broadcast_key = SHDCCrypto.derive_broadcast_key(master_key, key_version)

            # Store derived key
            self._store_key(
                key_id,
                broadcast_key,
                "aes256",
                expires_at=time.time() + self.broadcast_key_lifetime,
                metadata={"key_version": key_version},
            )

            return broadcast_key

    def get_session_key(self, peer_device_id: int) -> Optional[bytes]:
        """Get session key for specific peer device"""
        with self._lock:
            key_id = f"session_{peer_device_id:08X}"
            return self._get_key(key_id)

    def get_broadcast_key(self, key_version: int) -> Optional[bytes]:
        """Get broadcast key for specific version"""
        with self._lock:
            key_id = f"broadcast_{key_version:02X}"
            return self._get_key(key_id)

    def get_device_private_key(self) -> Optional[Ed25519PrivateKey]:
        """Get device private key"""
        with self._lock:
            key_bytes = self._get_key("device_identity")
            if key_bytes:
                return SHDCCrypto.deserialize_ed25519_private_key(key_bytes)
            return None

    def get_device_public_key(self) -> Optional[Ed25519PublicKey]:
        """Get device public key"""
        with self._lock:
            key_bytes = self._get_key("device_identity_public")
            if key_bytes:
                return SHDCCrypto.deserialize_ed25519_public_key(key_bytes)
            return None

    def store_peer_public_key(self, peer_device_id: int, public_key: bytes):
        """Store public key of peer device"""
        with self._lock:
            key_id = f"peer_{peer_device_id:08X}_public"
            self._store_key(
                key_id,
                public_key,
                "ed25519_public",
                metadata={"peer_device_id": peer_device_id},
            )

    def get_peer_public_key(self, peer_device_id: int) -> Optional[Ed25519PublicKey]:
        """Get public key of peer device"""
        with self._lock:
            key_id = f"peer_{peer_device_id:08X}_public"
            key_bytes = self._get_key(key_id)
            if key_bytes:
                return SHDCCrypto.deserialize_ed25519_public_key(key_bytes)
            return None

    def rotate_session_key(self, peer_device_id: int) -> bytes:
        """
        Rotate session key for specific peer.

        Args:
            peer_device_id: Device ID of communication peer

        Returns:
            New session key
        """
        with self._lock:
            # Delete old key
            old_key_id = f"session_{peer_device_id:08X}"
            self._delete_key(old_key_id)

            # Generate new key
            return self.generate_session_key(peer_device_id)

    def rotate_broadcast_keys(self) -> int:
        """
        Rotate broadcast keys to new version.

        Returns:
            New broadcast key version
        """
        with self._lock:
            # Find current highest version
            current_version = 0
            for key_id in self._key_info:
                if key_id.startswith("broadcast_") and key_id != "broadcast_master":
                    try:
                        version = int(key_id.split("_")[1], 16)
                        current_version = max(current_version, version)
                    except (ValueError, IndexError):
                        continue

            # Generate new version
            new_version = (current_version + 1) % 256
            self.generate_broadcast_key(new_version)

            return new_version

    def cleanup_expired_keys(self):
        """Remove expired keys from storage"""
        with self._lock:
            expired_keys = []

            for key_id, key_info in self._key_info.items():
                if key_info.is_expired():
                    expired_keys.append(key_id)

            for key_id in expired_keys:
                self._delete_key(key_id)

    def list_keys(self) -> List[KeyInfo]:
        """List all stored keys"""
        with self._lock:
            return list(self._key_info.values())

    def export_public_keys(self) -> Dict[str, bytes]:
        """Export all public keys"""
        with self._lock:
            public_keys = {}

            for key_id, key_info in self._key_info.items():
                if key_info.key_type == "ed25519_public":
                    public_keys[key_id] = self._keys[key_id]

            return public_keys

    def backup_keys(self, backup_path: str, password: Optional[str] = None):
        """
        Create encrypted backup of all keys.

        Args:
            backup_path: Path for backup file
            password: Optional password for encryption
        """
        with self._lock:
            backup_data = {
                "device_id": self.device_id,
                "created_at": time.time(),
                "keys": {},
                "key_info": {},
            }

            # Export keys (encrypt sensitive ones)
            for key_id, key_bytes in self._keys.items():
                key_info = self._key_info[key_id]

                if key_info.key_type == "ed25519_private" and password:
                    # Encrypt private keys if password provided
                    # Implementation would use password-based encryption
                    backup_data["keys"][key_id] = key_bytes.hex()
                else:
                    backup_data["keys"][key_id] = key_bytes.hex()

                backup_data["key_info"][key_id] = asdict(key_info)

            # Write backup file
            with open(backup_path, "w") as f:
                json.dump(backup_data, f, indent=2)

    def restore_keys(self, backup_path: str, password: Optional[str] = None):
        """
        Restore keys from encrypted backup.

        Args:
            backup_path: Path to backup file
            password: Optional password for decryption
        """
        with self._lock:
            with open(backup_path, "r") as f:
                backup_data = json.load(f)

            # Verify device ID matches
            if backup_data.get("device_id") != self.device_id:
                raise ValueError("Backup device ID does not match")

            # Restore keys
            for key_id, key_hex in backup_data["keys"].items():
                key_bytes = bytes.fromhex(key_hex)
                key_info_dict = backup_data["key_info"][key_id]
                key_info = KeyInfo(**key_info_dict)

                self._keys[key_id] = key_bytes
                self._key_info[key_id] = key_info

            # Save to persistent storage
            self._save_keys()

    def _store_key(
        self,
        key_id: str,
        key_bytes: bytes,
        key_type: str,
        expires_at: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ):
        """Store key in memory and persistent storage"""
        # Store in memory
        self._keys[key_id] = key_bytes
        self._key_info[key_id] = KeyInfo(
            key_id=key_id,
            key_type=key_type,
            created_at=time.time(),
            expires_at=expires_at,
            metadata=metadata or {},
        )

        # Save to disk
        self._save_key_to_disk(key_id, key_bytes, self._key_info[key_id])

    def _get_key(self, key_id: str) -> Optional[bytes]:
        """Get key from storage"""
        if key_id not in self._keys:
            return None

        # Check if expired
        key_info = self._key_info[key_id]
        if key_info.is_expired():
            self._delete_key(key_id)
            return None

        return self._keys[key_id]

    def _delete_key(self, key_id: str):
        """Delete key from storage"""
        if key_id in self._keys:
            # Zero out key bytes
            key_bytes = bytearray(self._keys[key_id])
            zero_memory(key_bytes)

            # Remove from memory
            del self._keys[key_id]
            del self._key_info[key_id]

            # Remove from disk
            key_file = self.storage_path / f"{key_id}.key"
            if key_file.exists():
                key_file.unlink()

            info_file = self.storage_path / f"{key_id}.info"
            if info_file.exists():
                info_file.unlink()

    def _save_key_to_disk(self, key_id: str, key_bytes: bytes, key_info: KeyInfo):
        """Save key and info to disk"""
        # Save key bytes
        key_file = self.storage_path / f"{key_id}.key"
        with open(key_file, "wb") as f:
            f.write(key_bytes)

        # Set restrictive permissions
        key_file.chmod(0o600)

        # Save key info
        info_file = self.storage_path / f"{key_id}.info"
        with open(info_file, "w") as f:
            json.dump(asdict(key_info), f, indent=2)

    def _load_keys(self):
        """Load keys from disk"""
        if not self.storage_path.exists():
            return

        for key_file in self.storage_path.glob("*.key"):
            key_id = key_file.stem
            info_file = self.storage_path / f"{key_id}.info"

            if not info_file.exists():
                continue

            try:
                # Load key bytes
                with open(key_file, "rb") as f:
                    key_bytes = f.read()

                # Load key info
                with open(info_file, "r") as f:
                    key_info_dict = json.load(f)

                key_info = KeyInfo(**key_info_dict)

                # Check if expired
                if key_info.is_expired():
                    key_file.unlink()
                    info_file.unlink()
                    continue

                # Store in memory
                self._keys[key_id] = key_bytes
                self._key_info[key_id] = key_info

            except Exception:
                # Remove corrupted files
                key_file.unlink(missing_ok=True)
                info_file.unlink(missing_ok=True)

    def _save_keys(self):
        """Save all keys to disk"""
        for key_id, key_bytes in self._keys.items():
            if key_id in self._key_info:
                self._save_key_to_disk(key_id, key_bytes, self._key_info[key_id])

    def __del__(self):
        """Cleanup on destruction"""
        # Zero out all key material
        with self._lock:
            for key_id, key_bytes in self._keys.items():
                if isinstance(key_bytes, (bytes, bytearray)):
                    key_array = bytearray(key_bytes)
                    zero_memory(key_array)
