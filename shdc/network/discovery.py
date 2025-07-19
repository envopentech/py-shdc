"""
SHDC Hub Discovery

This module implements the hub discovery mechanism for SHDC sensors
to automatically locate hubs on the local network using UDP broadcast
and multicast as specified in SHDC v1.0.
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional, Callable, Tuple

from .transport import UDPTransport, SHDC_PORT, SHDC_MULTICAST_IP, SHDC_BROADCAST_IP
from ..core.messages import (
    MessageType, SHDCHeader, SHDCMessage,
    HubDiscoveryRequestPayload, HubDiscoveryResponsePayload
)
from ..crypto.encryption import SHDCCrypto


class DiscoveredHub:
    """Information about a discovered hub"""
    
    def __init__(self, hub_id: int, address: str, port: int, 
                 public_key: bytes, capabilities: str = ""):
        self.hub_id = hub_id
        self.address = address
        self.port = port
        self.public_key = public_key
        self.capabilities = capabilities
        self.discovered_at = time.time()
        self.response_time = 0.0
    
    def __str__(self):
        return f"Hub {self.hub_id:08X} at {self.address}:{self.port}"


class HubDiscovery:
    """
    Hub Discovery Service
    
    Implements the SHDC hub discovery protocol allowing sensors
    to automatically locate hubs on the local network.
    """
    
    def __init__(self):
        """Initialize hub discovery service"""
        self.discovered_hubs: Dict[int, DiscoveredHub] = {}
        self.discovery_handlers: List[Callable[[DiscoveredHub], None]] = []
        self.logger = logging.getLogger("shdc.discovery")
        
        # Discovery parameters
        self.discovery_timeout = 5.0  # seconds
        self.retry_interval = 5.0     # seconds
        self.max_retries = 6          # 30 seconds total
        self.exponential_backoff = True
        
    def on_hub_discovered(self, handler: Callable[[DiscoveredHub], None]):
        """Register a handler for hub discovery events"""
        self.discovery_handlers.append(handler)
    
    def _emit_hub_discovered(self, hub: DiscoveredHub):
        """Emit hub discovered event to all handlers"""
        for handler in self.discovery_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(hub))
                else:
                    handler(hub)
            except Exception as e:
                self.logger.error(f"Error in discovery handler: {e}")
    
    async def discover_hubs(self, device_private_key, device_public_key,
                          device_info: str = "SHDC Sensor",
                          timeout: Optional[float] = None) -> List[DiscoveredHub]:
        """
        Discover hubs on the local network.
        
        Args:
            device_private_key: Sensor's private key for signing
            device_public_key: Sensor's public key to include in request
            device_info: Device identification string
            timeout: Discovery timeout in seconds
            
        Returns:
            List of discovered hubs
        """
        if timeout is None:
            timeout = self.discovery_timeout
        
        self.logger.info(f"Starting hub discovery (timeout: {timeout}s)")
        
        # Clear previous discoveries
        self.discovered_hubs.clear()
        
        # Create transport for discovery
        transport = UDPTransport()
        
        try:
            await transport.start()
            
            # Set up discovery response handler
            transport.on_message(self._handle_discovery_response)
            
            # Send discovery request
            await self._send_discovery_request(transport, device_private_key, 
                                             device_public_key, device_info)
            
            # Wait for responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                await asyncio.sleep(0.1)
            
            self.logger.info(f"Discovery completed: found {len(self.discovered_hubs)} hubs")
            
            return list(self.discovered_hubs.values())
            
        finally:
            await transport.stop()
    
    async def discover_hubs_with_retry(self, device_private_key, device_public_key,
                                     device_info: str = "SHDC Sensor") -> List[DiscoveredHub]:
        """
        Discover hubs with retry logic and exponential backoff.
        
        Args:
            device_private_key: Sensor's private key for signing
            device_public_key: Sensor's public key to include in request
            device_info: Device identification string
            
        Returns:
            List of discovered hubs
        """
        retry_count = 0
        retry_interval = self.retry_interval
        
        while retry_count < self.max_retries:
            self.logger.info(f"Hub discovery attempt {retry_count + 1}/{self.max_retries}")
            
            hubs = await self.discover_hubs(device_private_key, device_public_key, device_info)
            
            if hubs:
                self.logger.info(f"Successfully discovered {len(hubs)} hubs")
                return hubs
            
            retry_count += 1
            
            if retry_count < self.max_retries:
                self.logger.info(f"No hubs found, retrying in {retry_interval}s...")
                await asyncio.sleep(retry_interval)
                
                # Exponential backoff
                if self.exponential_backoff:
                    retry_interval = min(retry_interval * 2, 30.0)
        
        self.logger.warning("Hub discovery failed after all retries")
        return []
    
    async def _send_discovery_request(self, transport: UDPTransport, 
                                    device_private_key, device_public_key,
                                    device_info: str):
        """Send hub discovery request"""
        try:
            # Create discovery request payload
            payload = HubDiscoveryRequestPayload(
                public_key=SHDCCrypto.serialize_ed25519_public_key(device_public_key),
                device_info=device_info
            )
            
            # Create header with unassigned device ID
            header = SHDCHeader(
                msg_type=MessageType.HUB_DISCOVERY_REQ,
                device_id=0x00000000,  # Unassigned
                timestamp=int(time.time()),
                nonce=SHDCCrypto.generate_replay_nonce()
            )
            
            # Sign the message
            payload_bytes = payload.to_bytes()
            signed_data = header.to_bytes() + payload_bytes
            signature = SHDCCrypto.sign_message(signed_data, device_private_key)
            
            # Create complete message
            message = SHDCMessage(header, payload_bytes, signature)
            message_bytes = message.to_bytes()
            
            # Send broadcast first
            self.logger.debug("Sending broadcast discovery request")
            await transport.send_broadcast(message_bytes)
            
            # Send multicast as backup
            self.logger.debug("Sending multicast discovery request")
            await transport.send_multicast(message_bytes)
            
        except Exception as e:
            self.logger.error(f"Error sending discovery request: {e}")
            raise
    
    async def _handle_discovery_response(self, data: bytes, addr: Tuple[str, int]):
        """Handle hub discovery response"""
        try:
            # Parse message
            message = SHDCMessage.from_bytes(data)
            
            # Check if it's a discovery response
            if message.header.msg_type != MessageType.HUB_DISCOVERY_RESP:
                return
            
            self.logger.debug(f"Received discovery response from {addr}")
            
            # Parse payload
            payload = HubDiscoveryResponsePayload.from_bytes(message.payload)
            
            # TODO: Verify hub signature (requires known hub public keys or PKI)
            # For now, we accept all responses
            
            # Check if we already know this hub
            hub_id = payload.hub_id
            if hub_id in self.discovered_hubs:
                # Update response time if this is a better response
                existing_hub = self.discovered_hubs[hub_id]
                if addr[0] != existing_hub.address:
                    self.logger.debug(f"Hub {hub_id:08X} responded from different address: {addr[0]}")
                return
            
            # Create discovered hub entry
            hub = DiscoveredHub(
                hub_id=hub_id,
                address=addr[0],
                port=addr[1],
                public_key=payload.hub_public_key,
                capabilities=payload.capabilities
            )
            
            # Store discovered hub
            self.discovered_hubs[hub_id] = hub
            
            self.logger.info(f"Discovered hub: {hub} - {hub.capabilities}")
            
            # Emit discovery event
            self._emit_hub_discovered(hub)
            
        except Exception as e:
            self.logger.debug(f"Error parsing discovery response from {addr}: {e}")
    
    def get_best_hub(self) -> Optional[DiscoveredHub]:
        """
        Get the best hub from discovered hubs.
        
        Selection criteria:
        1. Lowest response time
        2. Most recent discovery
        3. Specific capabilities (if needed)
        
        Returns:
            Best hub or None if no hubs discovered
        """
        if not self.discovered_hubs:
            return None
        
        # For now, return the first hub found
        # In production, implement proper selection logic
        hubs = list(self.discovered_hubs.values())
        
        # Sort by discovery time (most recent first)
        hubs.sort(key=lambda h: h.discovered_at, reverse=True)
        
        return hubs[0]
    
    def get_hub_by_id(self, hub_id: int) -> Optional[DiscoveredHub]:
        """Get specific hub by ID"""
        return self.discovered_hubs.get(hub_id)
    
    def get_all_hubs(self) -> List[DiscoveredHub]:
        """Get all discovered hubs"""
        return list(self.discovered_hubs.values())
    
    def clear_discovered_hubs(self):
        """Clear all discovered hubs"""
        self.discovered_hubs.clear()
        self.logger.debug("Cleared discovered hubs")
    
    def is_hub_reachable(self, hub: DiscoveredHub) -> bool:
        """
        Check if a hub is still reachable.
        
        Args:
            hub: Hub to check
            
        Returns:
            True if hub is likely still reachable
        """
        # Simple time-based check
        age = time.time() - hub.discovered_at
        return age < 300.0  # 5 minutes
    
    def cleanup_old_hubs(self, max_age: float = 300.0):
        """
        Remove old hub entries.
        
        Args:
            max_age: Maximum age in seconds
        """
        current_time = time.time()
        old_hubs = []
        
        for hub_id, hub in self.discovered_hubs.items():
            if current_time - hub.discovered_at > max_age:
                old_hubs.append(hub_id)
        
        for hub_id in old_hubs:
            hub = self.discovered_hubs.pop(hub_id)
            self.logger.debug(f"Removed old hub: {hub}")


class ContinuousDiscovery:
    """
    Continuous Hub Discovery Service
    
    Provides ongoing hub discovery and monitoring for sensors
    that need to maintain awareness of available hubs.
    """
    
    def __init__(self, discovery: HubDiscovery):
        """
        Initialize continuous discovery.
        
        Args:
            discovery: Hub discovery instance to use
        """
        self.discovery = discovery
        self.running = False
        self.discovery_interval = 60.0  # seconds
        self.cleanup_interval = 300.0   # seconds
        self.logger = logging.getLogger("shdc.discovery.continuous")
        
        # Discovery parameters
        self.device_private_key = None
        self.device_public_key = None
        self.device_info = "SHDC Sensor"
        
    async def start(self, device_private_key, device_public_key, 
                   device_info: str = "SHDC Sensor"):
        """
        Start continuous discovery.
        
        Args:
            device_private_key: Sensor's private key
            device_public_key: Sensor's public key
            device_info: Device identification string
        """
        if self.running:
            return
        
        self.device_private_key = device_private_key
        self.device_public_key = device_public_key
        self.device_info = device_info
        
        self.running = True
        self.logger.info("Starting continuous hub discovery")
        
        # Start discovery and cleanup tasks
        asyncio.create_task(self._discovery_loop())
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop continuous discovery"""
        self.running = False
        self.logger.info("Stopping continuous hub discovery")
    
    async def _discovery_loop(self):
        """Continuous discovery loop"""
        while self.running:
            try:
                await self.discovery.discover_hubs(
                    self.device_private_key,
                    self.device_public_key,
                    self.device_info,
                    timeout=2.0  # Shorter timeout for continuous discovery
                )
                
                await asyncio.sleep(self.discovery_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(10.0)  # Wait before retrying
    
    async def _cleanup_loop(self):
        """Cleanup loop for removing old hubs"""
        while self.running:
            try:
                self.discovery.cleanup_old_hubs()
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(30.0)
