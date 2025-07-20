"""
SHDC Message Types and Constants

This module defines all message types, constants, and data structures
used in the SHDC v1.0 protocol specification.
"""

import struct
from dataclasses import dataclass
from enum import IntEnum


class MessageType(IntEnum):
    """SHDC Message Type Constants"""

    HUB_DISCOVERY_REQ = 0x00  # Sensor → Hub: Broadcast to discover hub
    EVENT_REPORT = 0x01  # Sensor → Hub: Event or status message
    JOIN_REQUEST = 0x02  # Sensor → Hub: Join handshake initiation
    JOIN_RESPONSE = 0x03  # Hub → Sensor: Response with keys/config
    BROADCAST_COMMAND = 0x04  # Hub → Sensor: Broadcasted command
    KEY_ROTATION = 0x05  # Any: Key update
    HUB_DISCOVERY_RESP = 0x06  # Hub → Sensor: Unicast response with identity


class EventType(IntEnum):
    """Common Event Types for EVENT_REPORT messages"""

    MOTION = 0x01
    DOOR_OPEN = 0x02
    DOOR_CLOSE = 0x03
    WINDOW_OPEN = 0x04
    WINDOW_CLOSE = 0x05
    TEMPERATURE = 0x06
    HUMIDITY = 0x07
    SMOKE = 0x08
    GLASS_BREAK = 0x09
    VIBRATION = 0x0A
    HEARTBEAT = 0xFF


class CommandType(IntEnum):
    """Broadcast Command Types"""

    LOCKDOWN = 0x01
    UNLOCK = 0x02
    ARM_SYSTEM = 0x03
    DISARM_SYSTEM = 0x04
    EMERGENCY = 0x05
    TEST_MODE = 0x06
    RESET = 0x07


# Protocol Constants
SHDC_PORT = 56700
SHDC_MULTICAST_IP = "239.255.0.1"
SHDC_BROADCAST_IP = "255.255.255.255"
MAX_PACKET_SIZE = 512
HEADER_SIZE = 12
SIGNATURE_SIZE = 64
REPLAY_TOLERANCE_SECONDS = 30


@dataclass
class SHDCHeader:
    """SHDC Packet Header Structure"""

    msg_type: int  # 1 byte: Message type code
    device_id: int  # 4 bytes: Unique device identifier
    timestamp: int  # 4 bytes: UNIX time
    nonce: bytes  # 3 bytes: Random nonce for replay defense

    def to_bytes(self) -> bytes:
        """Serialize header to 12-byte format"""
        header = struct.pack(">B", self.msg_type)
        header += struct.pack(">I", self.device_id)
        header += struct.pack(">I", self.timestamp)
        header += self.nonce
        return header

    @classmethod
    def from_bytes(cls, data: bytes) -> "SHDCHeader":
        """Deserialize header from 12-byte format"""
        if len(data) != HEADER_SIZE:
            raise ValueError(f"Header must be {HEADER_SIZE} bytes")

        msg_type = struct.unpack(">B", data[0:1])[0]
        device_id = struct.unpack(">I", data[1:5])[0]
        timestamp = struct.unpack(">I", data[5:9])[0]
        nonce = data[9:12]

        return cls(msg_type, device_id, timestamp, nonce)


@dataclass
class SHDCMessage:
    """Complete SHDC Message Structure"""

    header: SHDCHeader
    payload: bytes
    signature: bytes

    def to_bytes(self) -> bytes:
        """Serialize complete message"""
        return self.header.to_bytes() + self.payload + self.signature

    @classmethod
    def from_bytes(cls, data: bytes) -> "SHDCMessage":
        """Deserialize complete message"""
        if len(data) < HEADER_SIZE + SIGNATURE_SIZE:
            raise ValueError("Message too short")

        header = SHDCHeader.from_bytes(data[:HEADER_SIZE])
        signature = data[-SIGNATURE_SIZE:]
        payload = data[HEADER_SIZE:-SIGNATURE_SIZE]

        return cls(header, payload, signature)


@dataclass
class JoinRequestPayload:
    """JOIN_REQUEST message payload"""

    public_key: bytes  # 32 bytes: Sensor's Ed25519 public key
    device_info: str  # Variable: Optional text/model info

    def to_bytes(self) -> bytes:
        """Serialize payload"""
        data = self.public_key
        if self.device_info:
            data += self.device_info.encode("utf-8")
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> "JoinRequestPayload":
        """Deserialize payload"""
        if len(data) < 32:
            raise ValueError("Payload too short for public key")

        public_key = data[:32]
        device_info = data[32:].decode("utf-8") if len(data) > 32 else ""

        return cls(public_key, device_info)


@dataclass
class JoinResponsePayload:
    """JOIN_RESPONSE message payload (before encryption)"""

    assigned_id: int  # 4 bytes: Unique numeric ID for sensor
    session_key: bytes  # 32 bytes: AES-GCM key
    broadcast_key_id: int  # 1 byte: Group key version/tag

    def to_bytes(self) -> bytes:
        """Serialize payload"""
        data = struct.pack(">I", self.assigned_id)
        data += self.session_key
        data += struct.pack(">B", self.broadcast_key_id)
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> "JoinResponsePayload":
        """Deserialize payload"""
        if len(data) != 37:  # 4 + 32 + 1
            raise ValueError("Invalid JOIN_RESPONSE payload size")

        assigned_id = struct.unpack(">I", data[0:4])[0]
        session_key = data[4:36]
        broadcast_key_id = struct.unpack(">B", data[36:37])[0]

        return cls(assigned_id, session_key, broadcast_key_id)


@dataclass
class EventReportPayload:
    """EVENT_REPORT message payload (before encryption)"""

    event_type: int  # 1 byte: Event type code
    data: bytes  # Variable: Sensor-specific info

    def to_bytes(self) -> bytes:
        """Serialize payload"""
        payload = struct.pack(">B", self.event_type)
        payload += struct.pack(">B", len(self.data))
        payload += self.data
        return payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "EventReportPayload":
        """Deserialize payload"""
        if len(data) < 2:
            raise ValueError("Payload too short")

        event_type = struct.unpack(">B", data[0:1])[0]
        data_length = struct.unpack(">B", data[1:2])[0]

        if len(data) != 2 + data_length:
            raise ValueError("Data length mismatch")

        event_data = data[2 : 2 + data_length]

        return cls(event_type, event_data)


@dataclass
class BroadcastCommandPayload:
    """BROADCAST_COMMAND message payload (before encryption)"""

    command_type: int  # 1 byte: Command type
    command_data: bytes  # Variable: Command-specific data
    broadcast_key_id: int  # 1 byte: Key version tracking

    def to_bytes(self) -> bytes:
        """Serialize payload"""
        payload = struct.pack(">B", self.command_type)
        payload += self.command_data
        payload += struct.pack(">B", self.broadcast_key_id)
        return payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "BroadcastCommandPayload":
        """Deserialize payload"""
        if len(data) < 2:
            raise ValueError("Payload too short")

        command_type = struct.unpack(">B", data[0:1])[0]
        broadcast_key_id = struct.unpack(
            ">B",
            data[-1:],
        )[0]
        command_data = data[1:-1]

        return cls(command_type, command_data, broadcast_key_id)


@dataclass
class KeyRotationPayload:
    """KEY_ROTATION message payload (before encryption)"""

    new_key: bytes  # 32 bytes: New encryption key
    valid_from: int  # 4 bytes: UNIX time for activation

    def to_bytes(self) -> bytes:
        """Serialize payload"""
        return self.new_key + struct.pack(">I", self.valid_from)

    @classmethod
    def from_bytes(cls, data: bytes) -> "KeyRotationPayload":
        """Deserialize payload"""
        if len(data) != 36:  # 32 + 4
            raise ValueError("Invalid KEY_ROTATION payload size")

        new_key = data[:32]
        valid_from = struct.unpack(">I", data[32:36])[0]

        return cls(new_key, valid_from)


@dataclass
class HubDiscoveryRequestPayload:
    """HUB_DISCOVERY_REQ message payload"""

    public_key: bytes  # 32 bytes: Sensor's Ed25519 public key
    device_info: str  # Variable: Optional textual identifier

    def to_bytes(self) -> bytes:
        """Serialize payload"""
        data = self.public_key
        if self.device_info:
            data += self.device_info.encode("utf-8")
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> "HubDiscoveryRequestPayload":
        """Deserialize payload"""
        if len(data) < 32:
            raise ValueError("Payload too short for public key")

        public_key = data[:32]
        device_info = data[32:].decode("utf-8") if len(data) > 32 else ""

        return cls(public_key, device_info)


@dataclass
class HubDiscoveryResponsePayload:
    """HUB_DISCOVERY_RESP message payload"""

    hub_id: int  # 4 bytes: Unique hub identifier
    hub_public_key: bytes  # 32 bytes: Hub's Ed25519 public key
    capabilities: str  # Variable: Optional version/capability info

    def to_bytes(self) -> bytes:
        """Serialize payload"""
        data = struct.pack(">I", self.hub_id)
        data += self.hub_public_key
        if self.capabilities:
            data += self.capabilities.encode("utf-8")
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> "HubDiscoveryResponsePayload":
        """Deserialize payload"""
        if len(data) < 36:  # 4 + 32
            raise ValueError("Payload too short")

        hub_id = struct.unpack(">I", data[0:4])[0]
        hub_public_key = data[4:36]
        capabilities = data[36:].decode("utf-8") if len(data) > 36 else ""

        return cls(hub_id, hub_public_key, capabilities)


# Utility functions for message validation
def validate_device_id(device_id: int) -> bool:
    """Validate device ID is in valid range"""
    return 0 <= device_id <= 0xFFFFFFFF


def validate_timestamp(
    timestamp: int, tolerance: int = REPLAY_TOLERANCE_SECONDS
) -> bool:
    """Validate timestamp is within acceptable range"""
    import time

    current_time = int(time.time())
    return abs(current_time - timestamp) <= tolerance


def validate_message_type(msg_type: int) -> bool:
    """Validate message type is known"""
    return msg_type in [e.value for e in MessageType]


def get_message_name(msg_type: int) -> str:
    """Get human-readable message type name"""
    try:
        return MessageType(msg_type).name
    except ValueError:
        return f"UNKNOWN_{msg_type:02X}"
