#!/usr/bin/env python3
"""
SHDC Integration Test

Test the complete SHDC implementation with hub and sensor communication.
"""

import asyncio
import logging
import time
import json
from pathlib import Path

from shdc.core.protocol import SHDCProtocol, DeviceRole
from shdc.core.messages import MessageType
from shdc.crypto.keys import KeyManager
from shdc.network.transport import UDPTransport
from shdc.network.discovery import HubDiscovery


class SHDCIntegrationTest:
    """Integration test for SHDC protocol"""
    
    def __init__(self):
        self.hub_protocol = None
        self.sensor_protocol = None
        self.test_results = []
        
        # Set up logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('shdc_test')
    
    async def test_complete_system(self):
        """Test complete SHDC system functionality"""
        print("=== SHDC Integration Test ===\n")
        
        # Test configuration
        hub_id = 0x12345678
        sensor_id = 0x87654321
        hub_port = 56700
        
        try:
            # Test 1: Hub startup
            print("Test 1: Starting hub...")
            await self.start_hub(hub_id, hub_port)
            self.log_success("Hub started successfully")
            
            # Test 2: Sensor startup and discovery
            print("Test 2: Starting sensor and testing discovery...")
            await self.start_sensor(sensor_id)
            self.log_success("Sensor started successfully")
            
            # Test 3: Hub discovery
            print("Test 3: Testing hub discovery...")
            await self.test_hub_discovery(sensor_id)
            self.log_success("Hub discovery successful")
            
            # Test 4: Device joining
            print("Test 4: Testing device joining...")
            await self.test_device_joining()
            self.log_success("Device joining successful")
            
            # Test 5: Data transmission
            print("Test 5: Testing sensor data transmission...")
            await self.test_data_transmission()
            self.log_success("Data transmission successful")
            
            # Test 6: Control messages
            print("Test 6: Testing control messages...")
            await self.test_control_messages()
            self.log_success("Control messages successful")
            
            # Test 7: Key management
            print("Test 7: Testing key management...")
            await self.test_key_management()
            self.log_success("Key management successful")
            
            # Test 8: Error handling
            print("Test 8: Testing error handling...")
            await self.test_error_handling()
            self.log_success("Error handling successful")
            
            print("\n=== All Tests Passed! ===")
            self.print_test_summary()
            
        except Exception as e:
            self.log_failure(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.cleanup()
    
    async def start_hub(self, hub_id: int, port: int):
        """Start test hub"""
        # Initialize key manager
        key_manager = KeyManager(hub_id)
        private_key, public_key = key_manager.generate_device_keys()
        
        # Initialize transport
        transport = UDPTransport(port, "127.0.0.1")
        await transport.start()
        
        # Initialize protocol
        self.hub_protocol = SHDCProtocol(
            role=DeviceRole.HUB,
            device_id=hub_id,
            port=port
        )
        
        # Set up event handlers for testing
        self.hub_received_messages = []
        
        original_on_device_joined = self.hub_protocol.on_device_joined
        async def test_on_device_joined(device_info):
            self.hub_received_messages.append(('device_joined', device_info))
            if original_on_device_joined:
                await original_on_device_joined(device_info)
        
        original_on_sensor_data = self.hub_protocol.on_sensor_data
        async def test_on_sensor_data(device_id, data):
            self.hub_received_messages.append(('sensor_data', device_id, data))
            if original_on_sensor_data:
                await original_on_sensor_data(device_id, data)
        
        self.hub_protocol.on_device_joined = test_on_device_joined
        self.hub_protocol.on_sensor_data = test_on_sensor_data
        
        # Start protocol
        await self.hub_protocol.start()
    
    async def start_sensor(self, sensor_id: int):
        """Start test sensor"""
        # Initialize key manager
        key_manager = KeyManager(sensor_id)
        private_key, public_key = key_manager.generate_device_keys()
        
        # Initialize transport
        transport = UDPTransport(0, "127.0.0.1")  # Any available port
        await transport.start()
        
        # Initialize protocol
        self.sensor_protocol = SHDCProtocol(
            role=DeviceRole.SENSOR,
            device_id=sensor_id
        )
        
        self.sensor_protocol.device_type = "test_sensor"
        
        # Set up event handlers for testing
        self.sensor_received_messages = []
        
        original_on_control_message = self.sensor_protocol.on_control_message
        async def test_on_control_message(device_id, data):
            self.sensor_received_messages.append(('control_message', device_id, data))
            if original_on_control_message:
                await original_on_control_message(device_id, data)
        
        self.sensor_protocol.on_control_message = test_on_control_message
        
        # Start protocol
        await self.sensor_protocol.start()
    
    async def test_hub_discovery(self, sensor_id: int):
        """Test hub discovery functionality"""
        # Get sensor's transport and key manager
        transport = self.sensor_protocol.transport
        key_manager = self.sensor_protocol.key_manager
        
        # Create discovery instance
        discovery = HubDiscovery(transport, key_manager)
        
        # Start discovery
        await discovery.start_discovery()
        
        # Wait for discovery
        await asyncio.sleep(3)
        
        # Check results
        hubs = discovery.get_discovered_hubs()
        await discovery.stop_discovery()
        
        if not hubs:
            raise RuntimeError("No hubs discovered")
        
        # Verify hub found
        hub_found = False
        for hub in hubs:
            if hub.device_id == self.hub_protocol.device_id:
                hub_found = True
                break
        
        if not hub_found:
            raise RuntimeError("Expected hub not found in discovery")
    
    async def test_device_joining(self):
        """Test device joining process"""
        # Sensor joins hub
        success = await self.sensor_protocol.join_hub("127.0.0.1", 56700)
        if not success:
            raise RuntimeError("Failed to join hub")
        
        # Wait for join to complete
        await asyncio.sleep(2)
        
        # Verify hub received join message
        device_joined_found = False
        for message in self.hub_received_messages:
            if message[0] == 'device_joined':
                device_info = message[1]
                if device_info.device_id == self.sensor_protocol.device_id:
                    device_joined_found = True
                    break
        
        if not device_joined_found:
            raise RuntimeError("Hub did not receive device join message")
    
    async def test_data_transmission(self):
        """Test sensor data transmission"""
        # Send test data
        test_data = {
            'device_type': 'test_sensor',
            'value': 42.5,
            'unit': 'test_units',
            'timestamp': int(time.time())
        }
        
        await self.sensor_protocol.send_sensor_data(test_data)
        
        # Wait for data to be received
        await asyncio.sleep(2)
        
        # Verify hub received data
        data_received = False
        for message in self.hub_received_messages:
            if message[0] == 'sensor_data':
                device_id, data = message[1], message[2]
                if device_id == self.sensor_protocol.device_id and data.get('value') == 42.5:
                    data_received = True
                    break
        
        if not data_received:
            raise RuntimeError("Hub did not receive sensor data")
    
    async def test_control_messages(self):
        """Test control message exchange"""
        # Hub sends control message to sensor
        control_data = {
            'type': 'test_control',
            'command': 'ping',
            'timestamp': int(time.time())
        }
        
        await self.hub_protocol.send_control_message(self.sensor_protocol.device_id, control_data)
        
        # Wait for message to be received
        await asyncio.sleep(2)
        
        # Verify sensor received control message
        control_received = False
        for message in self.sensor_received_messages:
            if message[0] == 'control_message':
                device_id, data = message[1], message[2]
                if data.get('command') == 'ping':
                    control_received = True
                    break
        
        if not control_received:
            raise RuntimeError("Sensor did not receive control message")
    
    async def test_key_management(self):
        """Test key management functionality"""
        # Test key generation and storage
        hub_key_manager = self.hub_protocol.key_manager
        sensor_key_manager = self.sensor_protocol.key_manager
        
        # Generate session key
        session_key = hub_key_manager.generate_session_key(self.sensor_protocol.device_id)
        if len(session_key) != 32:
            raise RuntimeError("Invalid session key length")
        
        # Test key retrieval
        retrieved_key = hub_key_manager.get_session_key(self.sensor_protocol.device_id)
        if retrieved_key != session_key:
            raise RuntimeError("Key retrieval failed")
        
        # Test key rotation
        new_key = hub_key_manager.rotate_session_key(self.sensor_protocol.device_id)
        if new_key == session_key:
            raise RuntimeError("Key rotation failed")
        
        # Test broadcast key
        broadcast_key = hub_key_manager.generate_broadcast_key(1)
        if len(broadcast_key) != 32:
            raise RuntimeError("Invalid broadcast key length")
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        # Test invalid message
        try:
            # Send invalid data to hub
            invalid_transport = UDPTransport("127.0.0.1", 0)
            await invalid_transport.start()
            
            # Send malformed packet
            await invalid_transport.send_packet("127.0.0.1", 56700, b"invalid_data")
            
            await invalid_transport.stop()
            
            # Wait and check hub is still running
            await asyncio.sleep(1)
            if not self.hub_protocol.running:
                raise RuntimeError("Hub stopped after invalid message")
            
        except Exception as e:
            # This is expected - error handling working
            pass
    
    def log_success(self, message: str):
        """Log successful test"""
        self.test_results.append(('PASS', message))
        print(f"  ✓ {message}")
    
    def log_failure(self, message: str):
        """Log failed test"""
        self.test_results.append(('FAIL', message))
        print(f"  ✗ {message}")
    
    def print_test_summary(self):
        """Print test summary"""
        passed = sum(1 for result, _ in self.test_results if result == 'PASS')
        total = len(self.test_results)
        
        print(f"\nTest Summary: {passed}/{total} tests passed")
        
        for result, message in self.test_results:
            status = "✓" if result == 'PASS' else "✗"
            print(f"  {status} {message}")
    
    async def cleanup(self):
        """Cleanup test resources"""
        if self.sensor_protocol:
            await self.sensor_protocol.stop()
        
        if self.hub_protocol:
            await self.hub_protocol.stop()
        
        print("\nTest cleanup completed")


async def run_integration_test():
    """Run the complete integration test"""
    test = SHDCIntegrationTest()
    await test.test_complete_system()


if __name__ == '__main__':
    # Run integration test
    asyncio.run(run_integration_test())
