"""
SHDC Network Transport

This module implements UDP-based network transport for the SHDC protocol,
including unicast, broadcast, and multicast communication.
"""

import asyncio
import socket
import logging
from typing import Optional, Callable, Tuple, List

# SHDC Protocol constants
SHDC_PORT = 56700
SHDC_MULTICAST_IP = "224.0.1.187"
SHDC_BROADCAST_IP = "255.255.255.255"
DEFAULT_BUFFER_SIZE = 65536
MAX_PACKET_SIZE = 1500


class TransportError(Exception):
    """Exception raised for transport-related errors"""
    pass


class UDPTransport:
    """
    UDP Transport for SHDC Protocol
    
    Handles all network communication including unicast, broadcast,
    and multicast messaging as specified in SHDC v1.0.
    """
    
    def __init__(self, port: int = SHDC_PORT, bind_ip: str = "0.0.0.0"):
        """
        Initialize UDP transport.
        
        Args:
            port: Port number to bind to
            bind_ip: IP address to bind to (0.0.0.0 for all interfaces)
        """
        self.port = port
        self.bind_ip = bind_ip
        self.socket: Optional[socket.socket] = None
        self.multicast_socket: Optional[socket.socket] = None
        self.running = False
        
        # Message handlers
        self.message_handlers: List[Callable[[bytes, Tuple[str, int]], None]] = []
        
        # Logger
        self.logger = logging.getLogger(f"shdc.transport.{self.bind_ip}")
        
    async def start(self):
        """Start the transport layer"""
        if self.running:
            return
        
        try:
            # Create main UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.bind_ip, self.port))
            self.socket.setblocking(False)
            
            # Create multicast socket for receiving broadcasts
            self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Join multicast group
            try:
                mreq = socket.inet_aton(SHDC_MULTICAST_IP) + socket.inet_aton("0.0.0.0")
                self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                self.multicast_socket.bind(("", self.port))
                self.multicast_socket.setblocking(False)
            except Exception as e:
                self.logger.warning(f"Failed to setup multicast: {e}")
                self.multicast_socket.close()
                self.multicast_socket = None
            
            self.running = True
            
            # Start receiving tasks
            asyncio.create_task(self._receive_loop())
            if self.multicast_socket:
                asyncio.create_task(self._multicast_receive_loop())
            
            self.logger.info(f"UDP transport started on {self.bind_ip}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start transport: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the transport layer"""
        self.running = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
            
        if self.multicast_socket:
            self.multicast_socket.close()
            self.multicast_socket = None
            
        self.logger.info("UDP transport stopped")
    
    def on_message(self, handler: Callable[[bytes, Tuple[str, int]], None]):
        """Register a message handler"""
        self.message_handlers.append(handler)
    
    async def _receive_loop(self):
        """Main receive loop for unicast messages"""
        while self.running and self.socket:
            try:
                # Use asyncio to avoid blocking
                loop = asyncio.get_event_loop()
                data, addr = await loop.sock_recvfrom(self.socket, 1024)
                
                self.logger.debug(f"Received {len(data)} bytes from {addr}")
                
                # Call all message handlers
                for handler in self.message_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            asyncio.create_task(handler(data, addr))
                        else:
                            handler(data, addr)
                    except Exception as e:
                        self.logger.error(f"Error in message handler: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error in receive loop: {e}")
                    await asyncio.sleep(0.1)
    
    async def _multicast_receive_loop(self):
        """Receive loop for multicast messages"""
        while self.running and self.multicast_socket:
            try:
                loop = asyncio.get_event_loop()
                data, addr = await loop.sock_recvfrom(self.multicast_socket, 1024)
                
                self.logger.debug(f"Received multicast {len(data)} bytes from {addr}")
                
                # Call all message handlers
                for handler in self.message_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            asyncio.create_task(handler(data, addr))
                        else:
                            handler(data, addr)
                    except Exception as e:
                        self.logger.error(f"Error in multicast handler: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error in multicast receive loop: {e}")
                    await asyncio.sleep(0.1)
    
    async def send_to(self, data: bytes, addr: Tuple[str, int]):
        """Send data to specific address"""
        if not self.socket:
            raise RuntimeError("Transport not started")
        
        try:
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self.socket, data, addr)
            self.logger.debug(f"Sent {len(data)} bytes to {addr}")
        except Exception as e:
            self.logger.error(f"Error sending to {addr}: {e}")
            raise
    
    async def send_broadcast(self, data: bytes):
        """Send broadcast message"""
        if not self.socket:
            raise RuntimeError("Transport not started")
        
        try:
            # Enable broadcast
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send to broadcast address
            addr = (SHDC_BROADCAST_IP, self.port)
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self.socket, data, addr)
            
            self.logger.debug(f"Sent broadcast {len(data)} bytes")
            
        except Exception as e:
            self.logger.error(f"Error sending broadcast: {e}")
            raise
        finally:
            # Disable broadcast
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
            except:
                pass
    
    async def send_multicast(self, data: bytes):
        """Send multicast message"""
        if not self.socket:
            raise RuntimeError("Transport not started")
        
        try:
            # Set multicast TTL
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            # Send to multicast address
            addr = (SHDC_MULTICAST_IP, self.port)
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self.socket, data, addr)
            
            self.logger.debug(f"Sent multicast {len(data)} bytes")
            
        except Exception as e:
            self.logger.error(f"Error sending multicast: {e}")
            raise
    
    def get_local_addresses(self) -> List[str]:
        """Get list of local IP addresses"""
        addresses = []
        
        try:
            # Get all network interfaces
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        addr = addr_info.get('addr')
                        if addr and addr != '127.0.0.1':
                            addresses.append(addr)
        except ImportError:
            # Fallback method if netifaces not available
            try:
                # Connect to a remote address to determine local IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                addresses.append(s.getsockname()[0])
                s.close()
            except:
                addresses.append("127.0.0.1")
        
        return addresses


class TCPTransport:
    """
    TCP Transport for SHDC Protocol (Fallback)
    
    Provides reliable TCP transport as fallback for critical operations.
    Not fully implemented in this version.
    """
    
    def __init__(self, port: int = SHDC_PORT):
        """Initialize TCP transport"""
        self.port = port
        self.logger = logging.getLogger(f"shdc.tcp.{port}")
        
    async def start(self):
        """Start TCP transport (placeholder)"""
        self.logger.info("TCP transport not implemented in this version")
        
    async def stop(self):
        """Stop TCP transport (placeholder)"""
        pass
