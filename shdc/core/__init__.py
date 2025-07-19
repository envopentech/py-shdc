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

from .protocol import SHDCProtocol, DeviceRole, SensorState, HubState
from .messages import (
    MessageType,
    SHDCHeader,
    SHDCMessage,
    EventType,
    CommandType,
    JoinRequestPayload,
    JoinResponsePayload,
    EventReportPayload,
    BroadcastCommandPayload,
    KeyRotationPayload,
    HubDiscoveryRequestPayload,
    HubDiscoveryResponsePayload,
    # Constants
    SHDC_PORT,
    SHDC_MULTICAST_IP,
    SHDC_BROADCAST_IP,
    MAX_PACKET_SIZE,
    HEADER_SIZE,
    SIGNATURE_SIZE,
    REPLAY_TOLERANCE_SECONDS,
)

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
