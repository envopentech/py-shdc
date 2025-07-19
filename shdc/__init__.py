"""
SHDC - Smart Home Device Communications Protocol

A comprehensive Python implementation of the SHDC v1.0 protocol for secure
smart home device communications with hub-sensor architecture.

Key Components:
- Protocol implementation with Ed25519 signatures and AES-256-GCM encryption
- UDP transport with multicast discovery and unicast communication
- Automatic key management and rotation
- CLI tools for hubs and sensors
- Example applications for home monitoring

Usage:
    For programmatic use:
        from shdc.core.protocol import SHDCProtocol, DeviceRole
        from shdc.crypto.keys import KeyManager
        from shdc.network.transport import UDPTransport
    
    For CLI usage:
        shdc-hub run 0x12345678
        shdc-sensor run 0x87654321 temperature
"""

# Version information
__version__ = "1.0.0"
__author__ = "Argo Nickerson"
__email__ = "argo@envopen.org"
__license__ = "LGPL v2.1"

# Core imports for convenience
from .core.protocol import SHDCProtocol, DeviceRole
from .core.messages import MessageType, SHDCMessage, SHDCHeader
from .crypto.encryption import SHDCCrypto
from .crypto.keys import KeyManager
from .network.transport import UDPTransport
from .network.discovery import HubDiscovery

# Package metadata
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    
    # Core classes
    "SHDCProtocol",
    "DeviceRole",
    "MessageType",
    "SHDCMessage",
    "SHDCHeader",
    "SHDCCrypto",
    "KeyManager",
    "UDPTransport",
    "HubDiscovery",
]

# Protocol constants
PROTOCOL_VERSION = 1
DEFAULT_PORT = 56700
MULTICAST_GROUP = "224.0.1.187"
MULTICAST_PORT = 56700

# Convenience constants
SHDC_VERSION = "1.0"
PROTOCOL_NAME = "Smart Home Device Communications Protocol"

__version__ = "1.0.0"
__author__ = "Argo Nickerson"
__email__ = "argo@envopen.org"

# Import main classes for easy access
from .core.protocol import SHDCProtocol
from .core.messages import MessageType, SHDCMessage
from .crypto.keys import KeyManager
from .network.discovery import HubDiscovery
from .network.transport import UDPTransport

__all__ = [
    "SHDCProtocol",
    "MessageType", 
    "SHDCMessage",
    "KeyManager",
    "HubDiscovery",
    "UDPTransport",
    "__version__",
]
