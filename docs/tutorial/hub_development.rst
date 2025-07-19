Hub Development
===============

This tutorial covers developing hub applications using the SHDC library.

Understanding Hub Responsibilities
----------------------------------

A hub in the SHDC protocol serves as the central coordinator for a network of sensors. The hub:

* Listens for device discovery requests
* Manages device authentication and joining
* Receives and processes sensor data
* Sends commands to connected devices
* Handles key rotation and security management

Basic Hub Implementation
-----------------------

Minimal Hub Example
~~~~~~~~~~~~~~~~~~~

Here's a simple hub that accepts sensor connections and logs their data:

.. code-block:: python

   import asyncio
   import logging
   from shdc.core.protocol import SHDCProtocol, DeviceRole
   from shdc.crypto.keys import KeyManager
   from shdc.network.transport import UDPTransport

   class SimpleHub:
       def __init__(self, device_id, port=56700):
           self.device_id = device_id
           self.port = port
           self.protocol = None
           
       async def start(self):
           # Initialize key management
           key_manager = KeyManager(self.device_id)
           private_key, public_key = key_manager.generate_device_keys()
           
           # Initialize network transport
           transport = UDPTransport("0.0.0.0", self.port)
           await transport.start()
           
           # Create protocol instance
           self.protocol = SHDCProtocol(
               device_id=self.device_id,
               device_role=DeviceRole.HUB,
               private_key=private_key,
               key_manager=key_manager,
               transport=transport
           )
           
           # Set up event handlers
           self.protocol.on_device_joined = self.on_device_joined
           self.protocol.on_sensor_data = self.on_sensor_data
           self.protocol.on_device_left = self.on_device_left
           
           # Start the protocol
           await self.protocol.start()
           logging.info(f"Hub {self.device_id:08X} started on port {self.port}")
           
       async def on_device_joined(self, device_info):
           """Called when a sensor joins the network"""
           logging.info(
               f"Device {device_info.device_id:08X} joined "
               f"(type: {device_info.device_type})"
           )
           
       async def on_sensor_data(self, device_id, data):
           """Called when sensor data is received"""
           logging.info(f"Data from {device_id:08X}: {data}")
           
       async def on_device_left(self, device_id):
           """Called when a sensor disconnects"""
           logging.info(f"Device {device_id:08X} left the network")
           
       async def stop(self):
           if self.protocol:
               await self.protocol.stop()

   # Usage
   async def main():
       hub = SimpleHub(0x12345678)
       await hub.start()
       
       try:
           # Keep running
           while True:
               await asyncio.sleep(1)
       except KeyboardInterrupt:
           await hub.stop()

   if __name__ == "__main__":
       logging.basicConfig(level=logging.INFO)
       asyncio.run(main())

Advanced Hub Features
--------------------

Data Processing and Storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A more sophisticated hub can process and store sensor data:

.. code-block:: python

   import json
   import sqlite3
   from datetime import datetime
   from typing import Dict, Any

   class DataProcessingHub(SimpleHub):
       def __init__(self, device_id, port=56700, db_path="hub_data.db"):
           super().__init__(device_id, port)
           self.db_path = db_path
           self.init_database()
           
       def init_database(self):
           """Initialize SQLite database for sensor data"""
           conn = sqlite3.connect(self.db_path)
           conn.execute("""
               CREATE TABLE IF NOT EXISTS sensor_data (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   device_id TEXT NOT NULL,
                   device_type TEXT,
                   timestamp DATETIME,
                   data TEXT,
                   processed BOOLEAN DEFAULT FALSE
               )
           """)
           conn.execute("""
               CREATE TABLE IF NOT EXISTS devices (
                   device_id TEXT PRIMARY KEY,
                   device_type TEXT,
                   first_seen DATETIME,
                   last_seen DATETIME,
                   status TEXT DEFAULT 'active'
               )
           """)
           conn.commit()
           conn.close()
           
       async def on_device_joined(self, device_info):
           """Store device information in database"""
           await super().on_device_joined(device_info)
           
           conn = sqlite3.connect(self.db_path)
           now = datetime.now()
           conn.execute("""
               INSERT OR REPLACE INTO devices 
               (device_id, device_type, first_seen, last_seen, status)
               VALUES (?, ?, COALESCE((SELECT first_seen FROM devices WHERE device_id = ?), ?), ?, 'active')
           """, (
               f"{device_info.device_id:08X}",
               device_info.device_type,
               f"{device_info.device_id:08X}",
               now,
               now
           ))
           conn.commit()
           conn.close()
           
       async def on_sensor_data(self, device_id, data):
           """Process and store sensor data"""
           await super().on_sensor_data(device_id, data)
           
           # Store raw data
           conn = sqlite3.connect(self.db_path)
           conn.execute("""
               INSERT INTO sensor_data (device_id, device_type, timestamp, data)
               VALUES (?, ?, ?, ?)
           """, (
               f"{device_id:08X}",
               data.get('device_type', 'unknown'),
               datetime.now(),
               json.dumps(data)
           ))
           conn.commit()
           conn.close()
           
           # Process specific data types
           await self.process_sensor_data(device_id, data)
           
       async def process_sensor_data(self, device_id: int, data: Dict[str, Any]):
           """Process sensor data based on type"""
           device_type = data.get('device_type')
           
           if device_type == 'temperature':
               await self.process_temperature_data(device_id, data)
           elif device_type == 'motion':
               await self.process_motion_data(device_id, data)
           elif device_type == 'humidity':
               await self.process_humidity_data(device_id, data)
               
       async def process_temperature_data(self, device_id: int, data: Dict[str, Any]):
           """Process temperature sensor data"""
           temp = data.get('temperature')
           if temp is not None:
               # Check for alerts
               if temp > 30.0:
                   await self.send_alert(device_id, "HIGH_TEMPERATURE", f"Temperature {temp}°C exceeds threshold")
               elif temp < 10.0:
                   await self.send_alert(device_id, "LOW_TEMPERATURE", f"Temperature {temp}°C below threshold")
                   
       async def process_motion_data(self, device_id: int, data: Dict[str, Any]):
           """Process motion sensor data"""
           motion_detected = data.get('motion_detected', False)
           if motion_detected:
               await self.send_alert(device_id, "MOTION_DETECTED", "Motion detected")
               
       async def send_alert(self, device_id: int, alert_type: str, message: str):
           """Send alert to external systems"""
           logging.warning(f"ALERT from {device_id:08X}: {alert_type} - {message}")
           # Here you could send to external alerting systems

Device Management
~~~~~~~~~~~~~~~~

Implement advanced device management features:

.. code-block:: python

   from typing import Set
   import time

   class ManagedHub(DataProcessingHub):
       def __init__(self, device_id, port=56700, db_path="hub_data.db"):
           super().__init__(device_id, port, db_path)
           self.connected_devices: Dict[int, Dict[str, Any]] = {}
           self.device_heartbeats: Dict[int, float] = {}
           self.heartbeat_interval = 60  # seconds
           
       async def start(self):
           await super().start()
           # Start heartbeat monitoring
           asyncio.create_task(self.monitor_heartbeats())
           
       async def on_device_joined(self, device_info):
           """Track connected devices"""
           await super().on_device_joined(device_info)
           
           self.connected_devices[device_info.device_id] = {
               'device_type': device_info.device_type,
               'joined_at': time.time(),
               'status': 'active'
           }
           self.device_heartbeats[device_info.device_id] = time.time()
           
       async def on_sensor_data(self, device_id, data):
           """Update heartbeat on data reception"""
           await super().on_sensor_data(device_id, data)
           self.device_heartbeats[device_id] = time.time()
           
       async def on_device_left(self, device_id):
           """Clean up when device leaves"""
           await super().on_device_left(device_id)
           if device_id in self.connected_devices:
               del self.connected_devices[device_id]
           if device_id in self.device_heartbeats:
               del self.device_heartbeats[device_id]
               
       async def monitor_heartbeats(self):
           """Monitor device heartbeats and detect offline devices"""
           while True:
               current_time = time.time()
               offline_devices = []
               
               for device_id, last_heartbeat in self.device_heartbeats.items():
                   if current_time - last_heartbeat > self.heartbeat_interval * 2:
                       offline_devices.append(device_id)
                       
               for device_id in offline_devices:
                   logging.warning(f"Device {device_id:08X} appears offline")
                   if device_id in self.connected_devices:
                       self.connected_devices[device_id]['status'] = 'offline'
                       
               await asyncio.sleep(self.heartbeat_interval)
               
       async def send_command_to_device(self, device_id: int, command: str, data: Dict[str, Any] = None):
           """Send command to a specific device"""
           if self.protocol and device_id in self.connected_devices:
               command_data = {
                   'command': command,
                   'data': data or {},
                   'timestamp': int(time.time())
               }
               await self.protocol.send_command(device_id, command_data)
               
       async def broadcast_command(self, command: str, data: Dict[str, Any] = None):
           """Broadcast command to all connected devices"""
           if self.protocol:
               command_data = {
                   'command': command,
                   'data': data or {},
                   'timestamp': int(time.time())
               }
               await self.protocol.broadcast_command(command_data)
               
       def get_device_status(self) -> Dict[int, Dict[str, Any]]:
           """Get status of all connected devices"""
           return self.connected_devices.copy()

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~

Handle hub configuration and settings:

.. code-block:: python

   import yaml
   from pathlib import Path

   class ConfigurableHub(ManagedHub):
       def __init__(self, config_path="hub_config.yaml"):
           self.config = self.load_config(config_path)
           super().__init__(
               device_id=self.config['device_id'],
               port=self.config.get('port', 56700),
               db_path=self.config.get('database', 'hub_data.db')
           )
           
       def load_config(self, config_path: str) -> Dict[str, Any]:
           """Load hub configuration from YAML file"""
           config_file = Path(config_path)
           if config_file.exists():
               with open(config_file, 'r') as f:
                   return yaml.safe_load(f)
           else:
               # Create default configuration
               default_config = {
                   'device_id': 0x12345678,
                   'port': 56700,
                   'database': 'hub_data.db',
                   'log_level': 'INFO',
                   'heartbeat_interval': 60,
                   'alerts': {
                       'temperature_high': 30.0,
                       'temperature_low': 10.0,
                       'enable_motion_alerts': True
                   },
                   'allowed_device_types': ['temperature', 'humidity', 'motion', 'door']
               }
               with open(config_file, 'w') as f:
                   yaml.dump(default_config, f, default_flow_style=False)
               return default_config
               
       async def process_temperature_data(self, device_id: int, data: Dict[str, Any]):
           """Process temperature with configurable thresholds"""
           temp = data.get('temperature')
           if temp is not None:
               high_threshold = self.config['alerts']['temperature_high']
               low_threshold = self.config['alerts']['temperature_low']
               
               if temp > high_threshold:
                   await self.send_alert(device_id, "HIGH_TEMPERATURE", 
                                       f"Temperature {temp}°C exceeds {high_threshold}°C")
               elif temp < low_threshold:
                   await self.send_alert(device_id, "LOW_TEMPERATURE", 
                                       f"Temperature {temp}°C below {low_threshold}°C")

Testing Your Hub
---------------

Unit Testing
~~~~~~~~~~~~

Create unit tests for your hub implementation:

.. code-block:: python

   import pytest
   import asyncio
   from unittest.mock import AsyncMock, MagicMock

   @pytest.mark.asyncio
   async def test_simple_hub_startup():
       hub = SimpleHub(0x12345678, port=0)  # Use port 0 for testing
       
       # Mock the transport to avoid actual network operations
       hub.protocol = MagicMock()
       hub.protocol.start = AsyncMock()
       
       await hub.start()
       hub.protocol.start.assert_called_once()
       
   @pytest.mark.asyncio
   async def test_device_joined_handler():
       hub = SimpleHub(0x12345678)
       
       device_info = MagicMock()
       device_info.device_id = 0x87654321
       device_info.device_type = "temperature"
       
       # Should not raise any exceptions
       await hub.on_device_joined(device_info)

Integration Testing
~~~~~~~~~~~~~~~~~~

Test your hub with real sensor connections:

.. code-block:: python

   import subprocess
   import time

   async def test_hub_sensor_integration():
       # Start the hub
       hub = SimpleHub(0x12345678, port=56701)  # Use non-standard port
       await hub.start()
       
       try:
           # Start a test sensor
           sensor_process = subprocess.Popen([
               'python', '-m', 'shdc.cli.sensor',
               'run', '0x87654321', 'temperature',
               '--port', '56701',
               '--interval', '5'
           ])
           
           # Wait for connection
           await asyncio.sleep(10)
           
           # Check that device connected
           assert 0x87654321 in hub.connected_devices
           
       finally:
           sensor_process.terminate()
           await hub.stop()

Deployment Considerations
------------------------

Production Deployment
~~~~~~~~~~~~~~~~~~~~

For production deployments:

.. code-block:: python

   import signal
   import sys

   class ProductionHub(ConfigurableHub):
       def __init__(self, config_path="hub_config.yaml"):
           super().__init__(config_path)
           self.setup_signal_handlers()
           
       def setup_signal_handlers(self):
           """Handle graceful shutdown"""
           signal.signal(signal.SIGINT, self.signal_handler)
           signal.signal(signal.SIGTERM, self.signal_handler)
           
       def signal_handler(self, signum, frame):
           """Handle shutdown signals"""
           logging.info(f"Received signal {signum}, shutting down...")
           asyncio.create_task(self.graceful_shutdown())
           
       async def graceful_shutdown(self):
           """Perform graceful shutdown"""
           # Notify connected devices
           await self.broadcast_command("HUB_SHUTDOWN", {"reason": "maintenance"})
           
           # Wait for devices to disconnect
           await asyncio.sleep(5)
           
           # Stop the hub
           await self.stop()
           sys.exit(0)

Monitoring and Logging
~~~~~~~~~~~~~~~~~~~~~

Implement comprehensive monitoring:

.. code-block:: python

   import logging
   import json
   from logging.handlers import RotatingFileHandler

   def setup_production_logging():
       """Setup production logging configuration"""
       # Create formatters
       json_formatter = logging.Formatter(
           '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
           '"logger": "%(name)s", "message": "%(message)s"}'
       )
       
       # File handler with rotation
       file_handler = RotatingFileHandler(
           'hub.log', maxBytes=10*1024*1024, backupCount=5
       )
       file_handler.setFormatter(json_formatter)
       
       # Console handler
       console_handler = logging.StreamHandler()
       console_handler.setFormatter(logging.Formatter(
           '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       ))
       
       # Configure root logger
       logging.basicConfig(
           level=logging.INFO,
           handlers=[file_handler, console_handler]
       )

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~

For high-throughput scenarios:

.. code-block:: python

   import asyncio
   from collections import deque
   import threading

   class HighPerformanceHub(ProductionHub):
       def __init__(self, config_path="hub_config.yaml"):
           super().__init__(config_path)
           self.data_queue = deque()
           self.processing_thread = None
           
       async def start(self):
           await super().start()
           # Start background data processing
           self.processing_thread = threading.Thread(
               target=self.process_data_background,
               daemon=True
           )
           self.processing_thread.start()
           
       async def on_sensor_data(self, device_id, data):
           """Queue data for background processing"""
           self.data_queue.append((device_id, data, time.time()))
           
       def process_data_background(self):
           """Process sensor data in background thread"""
           while True:
               if self.data_queue:
                   device_id, data, timestamp = self.data_queue.popleft()
                   # Process data without blocking the main event loop
                   self.process_data_sync(device_id, data, timestamp)
               else:
                   time.sleep(0.01)  # Small sleep to prevent busy waiting

This tutorial provides a comprehensive foundation for developing sophisticated hub applications using the SHDC library. The examples progress from simple logging hubs to production-ready systems with data processing, device management, and monitoring capabilities.
