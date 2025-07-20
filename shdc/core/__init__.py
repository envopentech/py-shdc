"""
SHDC Core Package

Core protocol implementation and message handling for the SHDC system.

This package contains:
- protocol: Main SHDC protocol implementation with hub and sensor logic
- messages: Message types, constants, and data structures

The core package provides the fundamental building blocks for SHDC communication,
including the main protocol state machine, message serialization/deserialization,
and event handling for device interactions.
"""

from .messages import (  # Constants
    HEADER_SIZE,
    MAX_PACKET_SIZE,
    REPLAY_TOLERANCE_SECONDS,
    SHDC_BROADCAST_IP,
    SHDC_MULTICAST_IP,
    SHDC_PORT,
    SIGNATURE_SIZE,
    BroadcastCommandPayload,
    CommandType,
    EventReportPayload,
    EventType,
    HubDiscoveryRequestPayload,
    HubDiscoveryResponsePayload,
    JoinRequestPayload,
    JoinResponsePayload,
    KeyRotationPayload,
    MessageType,
    SHDCHeader,
    SHDCMessage,
)
from .protocol import DeviceRole, HubState, SensorState, SHDCProtocol

__all__ = [
    # Protocol classes
    "SHDCProtocol",
    "DeviceRole",
    "SensorState",
    "HubState",
    # Message classes
    "MessageType",
    "SHDCHeader",
    "SHDCMessage",
    "EventType",
    "CommandType",
    "JoinRequestPayload",
    "JoinResponsePayload",
    "EventReportPayload",
    "BroadcastCommandPayload",
    "KeyRotationPayload",
    "HubDiscoveryRequestPayload",
    "HubDiscoveryResponsePayload",
    # Constants
    "SHDC_PORT",
    "SHDC_MULTICAST_IP",
    "SHDC_BROADCAST_IP",
    "MAX_PACKET_SIZE",
    "HEADER_SIZE",
    "SIGNATURE_SIZE",
    "REPLAY_TOLERANCE_SECONDS",
]
