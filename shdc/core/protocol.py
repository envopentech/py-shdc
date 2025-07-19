"""
SHDC Protocol Implementation

This module implements the core SHDC v1.0 protocol logic for both
hub and sensor devices, including message handling, state management,
and security operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Tuple, Any
from enum import Enum

from ..crypto.encryption import SHDCCrypto
from ..crypto.keys import KeyManager
from ..network.transport import UDPTransport
from ..network.discovery import HubDiscovery
from .messages import (
    MessageType, SHDCHeader, SHDCMessage, EventType, CommandType,
    JoinRequestPayload, JoinResponsePayload, EventReportPayload,
    BroadcastCommandPayload, KeyRotationPayload,
    HubDiscoveryRequestPayload, HubDiscoveryResponsePayload,
    SHDC_PORT, MAX_PACKET_SIZE, validate_timestamp, validate_device_id
)


class DeviceRole(Enum):
    """Device role in SHDC network"""
    HUB = "hub"
    SENSOR = "sensor"


class SensorState(Enum):
    """Sensor device states"""
    DISCONNECTED = "disconnected"
    DISCOVERING = "discovering"
    JOINING = "joining"
    CONNECTED = "connected"
    ERROR = "error"


class HubState(Enum):
    """Hub device states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


class SHDCProtocol:
    """
    Main SHDC Protocol Implementation
    
    Handles both hub and sensor roles with complete protocol support
    including discovery, joining, messaging, and key management.
    """
    
    def __init__(self, role: DeviceRole, device_id: Optional[int] = None, 
                 port: int = SHDC_PORT, hub_ip: Optional[str] = None):
        """
        Initialize SHDC protocol instance.
        
        Args:
            role: Device role (hub or sensor)
            device_id: Unique device identifier (auto-generated if None)
            port: Network port to use
            hub_ip: Hub IP address (for sensors, if known)
        """
        self.role = role
        self.device_id = device_id or self._generate_device_id()
        self.port = port
        self.hub_ip = hub_ip
        
        # Cryptographic components
        self.crypto = SHDCCrypto()
        self.key_manager = KeyManager(self.device_id)
        
        # Network components
        self.transport = UDPTransport(port)
        self.discovery = HubDiscovery()
        
        # Device keys
        self.private_key, self.public_key = SHDCCrypto.generate_ed25519_keypair()
        
        # State management
        self.state = SensorState.DISCONNECTED if role == DeviceRole.SENSOR else HubState.STOPPED
        self.session_key: Optional[bytes] = None
        self.broadcast_key_id: int = 0
        
        # Hub-specific data
        if role == DeviceRole.HUB:
            self.connected_sensors: Dict[int, Dict[str, Any]] = {}
            self.broadcast_master_key = SHDCCrypto.generate_aes_key()
            
        # Sensor-specific data
        if role == DeviceRole.SENSOR:
            self.hub_public_key: Optional[bytes] = None
            self.assigned_id: Optional[int] = None
            
        # Event handlers
        self.event_handlers: Dict[MessageType, List[Callable]] = {msg_type: [] for msg_type in MessageType}
        
        # Logger
        self.logger = logging.getLogger(f"shdc.{role.value}.{self.device_id:08X}")
        
    def _generate_device_id(self) -> int:
        """Generate a random device ID"""
        import random
        return random.randint(0x10000000, 0xFFFFFFFF)
    
    # =============================================================================
    # Event Handler Registration
    # =============================================================================
    
    def on_event(self, message_type: MessageType, handler: Callable):
        """Register an event handler for a specific message type"""
        self.event_handlers[message_type].append(handler)
        
    def emit_event(self, message_type: MessageType, *args, **kwargs):
        """Emit an event to all registered handlers"""
        for handler in self.event_handlers[message_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(*args, **kwargs))
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in event handler: {e}")


# Legacy compatibility class
class BaseSHDCProtocol(SHDCProtocol):
    """
    Legacy compatibility class for BaseSHDCProtocol.
    Use SHDCProtocol directly for new implementations.
    """
    
    def __init__(self, role: str = "sensor", **kwargs):
        # Convert string role to enum
        device_role = DeviceRole.HUB if role.lower() == "hub" else DeviceRole.SENSOR
        super().__init__(device_role, **kwargs)
