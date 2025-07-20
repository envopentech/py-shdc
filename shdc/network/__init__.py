"""
SHDC Network Package

Network communication and discovery for the SHDC protocol.

This package provides:
- transport: UDP transport layer with multicast, broadcast, and unicast support
- discovery: Hub discovery mechanism with automatic retry and continuous monitoring

The network package handles all low-level networking operations for SHDC,
including reliable UDP communication, automatic hub discovery, and connection
management between devices.

Network Features:
- Asyncio-based UDP transport for high performance
- Multicast hub discovery on 224.0.1.187:56700
- Automatic retry and reconnection logic
- Support for multiple network interfaces
- Robust error handling and recovery
"""

from .discovery import (
    ContinuousDiscovery,
    DiscoveredHub,
    HubDiscovery,
)
from .transport import (  # Constants
    DEFAULT_BUFFER_SIZE,
    MAX_PACKET_SIZE,
    TransportError,
    UDPTransport,
)

__all__ = [
    # Transport classes
    "UDPTransport",
    "TransportError",
    # Discovery classes
    "HubDiscovery",
    "DiscoveredHub",
    "ContinuousDiscovery",
    # Transport constants
    "DEFAULT_BUFFER_SIZE",
    "MAX_PACKET_SIZE",
]
