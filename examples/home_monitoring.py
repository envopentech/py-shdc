#!/usr/bin/env python3
"""
SHDC Home Monitoring System Example

A complete example showing how to use the SHDC library to create
a smart home monitoring system with multiple sensors.
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any

from shdc.core.protocol import SHDCProtocol, DeviceRole
from shdc.core.messages import MessageType, EventReportPayload
from shdc.crypto.keys import KeyManager
from shdc.network.transport import UDPTransport


class HomeMonitoringHub:
    """A smart home monitoring hub that collects data from multiple sensors"""
    
    def __init__(self, hub_id: int):
        self.hub_id = hub_id
        self.protocol: SHDCProtocol = None
        self.sensor_data: Dict[int, List[Dict]] = {}  # device_id -> data history
        self.running = False
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('home_monitor')
    
    async def start(self, interface: str = "0.0.0.0", port: int = 56700):
        """Start the monitoring hub"""
        try:
            # Initialize key manager and generate keys
            key_manager = KeyManager(self.hub_id)
            private_key, public_key = key_manager.generate_device_keys()
            
            # Initialize transport and protocol
            transport = UDPTransport(port, interface)
            await transport.start()
            
            self.protocol = SHDCProtocol(
                device_id=self.hub_id,
                device_role=DeviceRole.HUB,
                private_key=private_key,
                key_manager=key_manager,
                transport=transport
            )
            
            # Set up event handlers
            self.protocol.on_device_joined = self.on_device_joined
            self.protocol.on_device_left = self.on_device_left
            self.protocol.on_sensor_data = self.on_sensor_data
            self.protocol.on_status_request = self.on_status_request
            
            # Start protocol
            await self.protocol.start()
            
            self.logger.info(f"Home monitoring hub started - ID: {self.hub_id:08X}")
            self.logger.info(f"Listening on {interface}:{port}")
            
            self.running = True
            
        except Exception as e:
            self.logger.error(f"Failed to start hub: {e}")
            raise
    
    async def stop(self):
        """Stop the monitoring hub"""
        self.running = False
        if self.protocol:
            await self.protocol.stop()
        self.logger.info("Home monitoring hub stopped")
    
    async def on_device_joined(self, device_info):
        """Handle device joining the network"""
        device_id = device_info.device_id
        device_type = device_info.device_type
        
        self.logger.info(f"Device joined: {device_id:08X} ({device_type})")
        
        # Initialize data storage for this device
        if device_id not in self.sensor_data:
            self.sensor_data[device_id] = []
        
        # Send welcome message
        try:
            welcome_data = {
                'type': 'welcome',
                'hub_id': self.hub_id,
                'timestamp': int(time.time()),
                'message': f'Welcome to the home monitoring system!'
            }
            await self.protocol.send_control_message(device_id, welcome_data)
        except Exception as e:
            self.logger.warning(f"Failed to send welcome message: {e}")
    
    async def on_device_left(self, device_id: int):
        """Handle device leaving the network"""
        self.logger.info(f"Device left: {device_id:08X}")
    
    async def on_sensor_data(self, device_id: int, data: Dict[str, Any]):
        """Handle incoming sensor data"""
        timestamp = data.get('timestamp', int(time.time()))
        device_type = data.get('device_type', 'unknown')
        
        # Store data
        if device_id not in self.sensor_data:
            self.sensor_data[device_id] = []
        
        self.sensor_data[device_id].append({
            'timestamp': timestamp,
            'data': data
        })
        
        # Keep only last 100 readings per device
        if len(self.sensor_data[device_id]) > 100:
            self.sensor_data[device_id] = self.sensor_data[device_id][-100:]
        
        # Log the data
        dt = datetime.fromtimestamp(timestamp)
        self.logger.info(f"Sensor data from {device_id:08X} ({device_type}) at {dt}: {data}")
        
        # Analyze data and send alerts if needed
        await self.analyze_sensor_data(device_id, data)
    
    async def on_status_request(self, device_id: int) -> Dict[str, Any]:
        """Handle status requests from devices"""
        connected_devices = self.protocol.get_connected_devices()
        
        status = {
            'hub_id': self.hub_id,
            'timestamp': int(time.time()),
            'connected_devices': len(connected_devices),
            'total_data_points': sum(len(history) for history in self.sensor_data.values())
        }
        
        return status
    
    async def analyze_sensor_data(self, device_id: int, data: Dict[str, Any]):
        """Analyze sensor data and send alerts if needed"""
        device_type = data.get('device_type', '')
        
        # Temperature alerts
        if device_type == 'temperature':
            temp = data.get('temperature', 0)
            if temp > 35:
                await self.send_alert(device_id, 'HIGH_TEMPERATURE', 
                                    f'High temperature detected: {temp}°C')
            elif temp < 5:
                await self.send_alert(device_id, 'LOW_TEMPERATURE', 
                                    f'Low temperature detected: {temp}°C')
        
        # Humidity alerts
        elif device_type == 'humidity':
            humidity = data.get('humidity', 0)
            if humidity > 80:
                await self.send_alert(device_id, 'HIGH_HUMIDITY', 
                                    f'High humidity detected: {humidity}%')
            elif humidity < 20:
                await self.send_alert(device_id, 'LOW_HUMIDITY', 
                                    f'Low humidity detected: {humidity}%')
        
        # Motion detection
        elif device_type == 'motion':
            if data.get('motion_detected', False):
                await self.send_alert(device_id, 'MOTION_DETECTED', 
                                    'Motion detected')
        
        # Door sensor
        elif device_type == 'door':
            if data.get('door_open', False):
                # Check if door has been open for too long
                recent_data = self.sensor_data.get(device_id, [])[-10:]  # Last 10 readings
                if len(recent_data) >= 5:  # At least 5 readings
                    all_open = all(reading['data'].get('door_open', False) for reading in recent_data)
                    if all_open:
                        await self.send_alert(device_id, 'DOOR_OPEN_LONG', 
                                            'Door has been open for extended period')
    
    async def send_alert(self, device_id: int, alert_type: str, message: str):
        """Send alert to monitoring system or device"""
        alert_data = {
            'type': 'alert',
            'alert_type': alert_type,
            'device_id': device_id,
            'message': message,
            'timestamp': int(time.time())
        }
        
        self.logger.warning(f"ALERT - {alert_type}: {message} (Device: {device_id:08X})")
        
        # In a real system, you might send this to a notification service,
        # log to a database, or send to the device itself
    
    def get_device_summary(self) -> Dict[str, Any]:
        """Get summary of all connected devices and their data"""
        connected_devices = self.protocol.get_connected_devices() if self.protocol else []
        
        summary = {
            'hub_id': self.hub_id,
            'timestamp': int(time.time()),
            'connected_devices': [],
            'total_devices': len(connected_devices),
            'total_data_points': sum(len(history) for history in self.sensor_data.values())
        }
        
        for device_info in connected_devices:
            device_id = device_info.device_id
            device_data = self.sensor_data.get(device_id, [])
            
            latest_data = device_data[-1] if device_data else None
            
            device_summary = {
                'device_id': f"{device_id:08X}",
                'device_type': device_info.device_type,
                'data_points': len(device_data),
                'latest_data': latest_data['data'] if latest_data else None,
                'last_seen': latest_data['timestamp'] if latest_data else None
            }
            
            summary['connected_devices'].append(device_summary)
        
        return summary
    
    def export_data(self, filename: str = None):
        """Export all sensor data to JSON file"""
        if filename is None:
            filename = f"home_monitoring_data_{int(time.time())}.json"
        
        export_data = {
            'hub_id': self.hub_id,
            'export_timestamp': int(time.time()),
            'devices': {}
        }
        
        for device_id, data_history in self.sensor_data.items():
            export_data['devices'][f"{device_id:08X}"] = data_history
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Data exported to {filename}")
        return filename


async def run_monitoring_demo():
    """Run a complete home monitoring demonstration"""
    # Create monitoring hub
    hub_id = 0x12345678
    hub = HomeMonitoringHub(hub_id)
    
    print("=== SHDC Home Monitoring System Demo ===\n")
    
    try:
        # Start hub
        print("Starting monitoring hub...")
        await hub.start()
        
        print(f"Hub {hub_id:08X} is running and waiting for sensors...")
        print("You can now connect sensors using:")
        print("  shdc-sensor run 0x87654321 temperature")
        print("  shdc-sensor run 0x87654322 humidity")
        print("  shdc-sensor run 0x87654323 motion")
        print("\nPress Ctrl+C to stop the demo\n")
        
        # Main monitoring loop
        start_time = time.time()
        while hub.running:
            await asyncio.sleep(10)  # Update every 10 seconds
            
            # Show status every minute
            if (time.time() - start_time) % 60 < 10:
                summary = hub.get_device_summary()
                print(f"\n--- Status Update ({datetime.now().strftime('%H:%M:%S')}) ---")
                print(f"Connected devices: {summary['total_devices']}")
                print(f"Total data points: {summary['total_data_points']}")
                
                for device in summary['connected_devices']:
                    device_id = device['device_id']
                    device_type = device['device_type']
                    data_points = device['data_points']
                    latest = device['latest_data']
                    
                    print(f"  {device_id} ({device_type}): {data_points} readings")
                    if latest:
                        # Show relevant latest data
                        if device_type == 'temperature' and 'temperature' in latest:
                            print(f"    Current: {latest['temperature']}°C")
                        elif device_type == 'humidity' and 'humidity' in latest:
                            print(f"    Current: {latest['humidity']}%")
                        elif device_type == 'motion':
                            status = "Detected" if latest.get('motion_detected') else "Clear"
                            print(f"    Status: {status}")
                        elif device_type == 'door':
                            status = "Open" if latest.get('door_open') else "Closed"
                            print(f"    Status: {status}")
                print()
    
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    
    except Exception as e:
        print(f"Error in demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await hub.stop()
        
        # Export data
        if hub.sensor_data:
            filename = hub.export_data()
            print(f"Sensor data exported to: {filename}")
        
        print("Demo completed.")


if __name__ == '__main__':
    # Run the monitoring demo
    asyncio.run(run_monitoring_demo())
