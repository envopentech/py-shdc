Temperature Sensor Example
===========================

This example demonstrates building a realistic temperature sensor using the SHDC library.
The sensor simulates daily temperature variations and automatically connects to available hubs.

Complete Temperature Sensor
---------------------------

.. code-block:: python

   import asyncio
   import logging
   import math
   import random
   import time
   from datetime import datetime
   from typing import Optional

   from shdc.core.protocol import SHDCProtocol, DeviceRole
   from shdc.crypto.keys import KeyManager
   from shdc.network.transport import UDPTransport
   from shdc.network.discovery import HubDiscovery

   class TemperatureSensor:
       """
       Realistic temperature sensor with daily cycles and noise.
       
       Features:
       - Simulates realistic temperature variations
       - Automatic hub discovery and connection
       - Configurable transmission intervals
       - Error handling and reconnection
       - Location-based identification
       """
       
       def __init__(self, device_id: int, location: str = "Living Room", 
                    base_temp: float = 20.0, temp_range: float = 5.0):
           self.device_id = device_id
           self.location = location
           self.base_temp = base_temp
           self.temp_range = temp_range
           
           # State tracking
           self.protocol: Optional[SHDCProtocol] = None
           self.transport: Optional[UDPTransport] = None
           self.discovery: Optional[HubDiscovery] = None
           self.connected = False
           self.running = False
           
           # Configuration
           self.transmission_interval = 30  # seconds
           self.discovery_timeout = 10  # seconds
           self.max_retries = 3
           
           # Sensor simulation
           self.start_time = time.time()
           self.noise_amplitude = 0.5  # degrees
           
           # Setup logging
           self.logger = logging.getLogger(f"sensor.{device_id:08X}")
           
       async def start(self):
           """Start the temperature sensor"""
           self.logger.info(f"Starting temperature sensor at {self.location}")
           
           try:
               # Initialize components
               await self.initialize_components()
               
               # Discover and connect to hub
               await self.connect_to_hub()
               
               # Start temperature monitoring
               self.running = True
               await self.run_sensor_loop()
               
           except Exception as e:
               self.logger.error(f"Failed to start sensor: {e}")
               await self.stop()
               
       async def initialize_components(self):
           """Initialize SHDC protocol components"""
           # Key management
           key_manager = KeyManager(self.device_id)
           private_key, public_key = key_manager.generate_device_keys()
           
           # Network transport
           self.transport = UDPTransport("0.0.0.0", 0)  # Any available port
           await self.transport.start()
           self.logger.debug("Transport initialized")
           
           # Protocol instance
           self.protocol = SHDCProtocol(
               device_id=self.device_id,
               device_role=DeviceRole.SENSOR,
               private_key=private_key,
               key_manager=key_manager,
               transport=self.transport
           )
           
           # Set device type and location
           self.protocol.device_type = "temperature"
           self.protocol.device_location = self.location
           
           await self.protocol.start()
           self.logger.debug("Protocol initialized")
           
       async def connect_to_hub(self):
           """Discover and connect to a hub"""
           for attempt in range(self.max_retries):
               try:
                   self.logger.info(f"Discovering hubs (attempt {attempt + 1}/{self.max_retries})")
                   
                   # Initialize hub discovery
                   self.discovery = HubDiscovery(self.transport, self.protocol.key_manager)
                   await self.discovery.start_discovery()
                   
                   # Wait for discovery
                   await asyncio.sleep(self.discovery_timeout)
                   
                   # Get discovered hubs
                   hubs = self.discovery.get_discovered_hubs()
                   await self.discovery.stop_discovery()
                   
                   if not hubs:
                       self.logger.warning("No hubs discovered")
                       if attempt < self.max_retries - 1:
                           await asyncio.sleep(5)  # Wait before retry
                       continue
                       
                   # Connect to the first available hub
                   hub = hubs[0]
                   self.logger.info(f"Connecting to hub {hub.device_id:08X} at {hub.address}:{hub.port}")
                   
                   success = await self.protocol.join_hub(hub.address, hub.port)
                   if success:
                       self.connected = True
                       self.logger.info("Successfully connected to hub")
                       return
                   else:
                       self.logger.warning("Failed to join hub")
                       
               except Exception as e:
                   self.logger.error(f"Discovery attempt {attempt + 1} failed: {e}")
                   
               if attempt < self.max_retries - 1:
                   await asyncio.sleep(5)  # Wait before retry
                   
           raise Exception("Failed to connect to any hub after all attempts")
           
       async def run_sensor_loop(self):
           """Main sensor operation loop"""
           self.logger.info("Starting temperature monitoring")
           
           while self.running:
               try:
                   if not self.connected:
                       # Try to reconnect
                       self.logger.info("Connection lost, attempting to reconnect")
                       await self.connect_to_hub()
                       
                   # Read temperature
                   temperature = self.read_temperature()
                   humidity = self.read_humidity()  # Bonus: simulate humidity too
                   
                   # Prepare sensor data
                   sensor_data = {
                       'device_type': 'temperature',
                       'device_id': f"{self.device_id:08X}",
                       'location': self.location,
                       'timestamp': int(time.time()),
                       'temperature': round(temperature, 2),
                       'humidity': round(humidity, 1),
                       'unit': 'celsius'
                   }
                   
                   # Send data to hub
                   await self.protocol.send_sensor_data(sensor_data)
                   self.logger.info(
                       f"Sent data: {temperature:.1f}°C, {humidity:.1f}% humidity"
                   )
                   
                   # Wait for next transmission
                   await asyncio.sleep(self.transmission_interval)
                   
               except Exception as e:
                   self.logger.error(f"Error in sensor loop: {e}")
                   self.connected = False
                   await asyncio.sleep(5)  # Wait before retry
                   
       def read_temperature(self) -> float:
           """
           Simulate realistic temperature reading with daily cycles.
           
           The temperature follows a sinusoidal pattern with:
           - Daily high/low cycle
           - Random noise
           - Gradual trends
           """
           current_time = time.time()
           elapsed_hours = (current_time - self.start_time) / 3600
           
           # Daily temperature cycle (peak at 2 PM, low at 2 AM)
           daily_cycle = math.sin((elapsed_hours - 14) * 2 * math.pi / 24)
           daily_variation = daily_cycle * self.temp_range
           
           # Add some random noise
           noise = random.gauss(0, self.noise_amplitude)
           
           # Simulate slow trends (temperature drift over days)
           trend = math.sin(elapsed_hours * 2 * math.pi / (24 * 7)) * 2  # Weekly cycle
           
           temperature = self.base_temp + daily_variation + noise + trend
           
           # Ensure reasonable bounds
           return max(0, min(50, temperature))
           
       def read_humidity(self) -> float:
           """Simulate humidity reading (inverse correlation with temperature)"""
           temp = self.read_temperature()
           base_humidity = 50.0
           temp_effect = (temp - self.base_temp) * -1.5  # Inverse correlation
           noise = random.gauss(0, 2.0)
           
           humidity = base_humidity + temp_effect + noise
           return max(10, min(90, humidity))  # Reasonable bounds
           
       async def stop(self):
           """Stop the sensor"""
           self.logger.info("Stopping temperature sensor")
           self.running = False
           
           if self.discovery:
               await self.discovery.stop_discovery()
               
           if self.protocol:
               await self.protocol.stop()
               
           if self.transport:
               await self.transport.stop()

   # Example usage functions
   async def run_single_sensor():
       """Run a single temperature sensor"""
       sensor = TemperatureSensor(
           device_id=0x87654321,
           location="Living Room",
           base_temp=21.0,
           temp_range=3.0
       )
       
       try:
           await sensor.start()
       except KeyboardInterrupt:
           await sensor.stop()

   async def run_multiple_sensors():
       """Run multiple temperature sensors in different locations"""
       sensors = [
           TemperatureSensor(0x87654321, "Living Room", 21.0, 3.0),
           TemperatureSensor(0x87654322, "Bedroom", 19.0, 2.0),
           TemperatureSensor(0x87654323, "Kitchen", 23.0, 4.0),
           TemperatureSensor(0x87654324, "Basement", 16.0, 1.0),
       ]
       
       # Start all sensors concurrently
       tasks = [asyncio.create_task(sensor.start()) for sensor in sensors]
       
       try:
           await asyncio.gather(*tasks)
       except KeyboardInterrupt:
           print("Shutting down all sensors...")
           for sensor in sensors:
               await sensor.stop()

   if __name__ == "__main__":
       # Configure logging
       logging.basicConfig(
           level=logging.INFO,
           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       )
       
       # Run example
       print("Temperature Sensor Example")
       print("1. Single sensor")
       print("2. Multiple sensors")
       choice = input("Enter choice (1 or 2): ")
       
       if choice == "1":
           asyncio.run(run_single_sensor())
       elif choice == "2":
           asyncio.run(run_multiple_sensors())
       else:
           print("Invalid choice")

Advanced Features
-----------------

Configuration File Support
~~~~~~~~~~~~~~~~~~~~~~~~~~

Add configuration file support for deployment:

.. code-block:: python

   import yaml
   from pathlib import Path

   class ConfigurableTemperatureSensor(TemperatureSensor):
       def __init__(self, config_path: str):
           self.config = self.load_config(config_path)
           super().__init__(
               device_id=self.config['device_id'],
               location=self.config['location'],
               base_temp=self.config.get('base_temperature', 20.0),
               temp_range=self.config.get('temperature_range', 5.0)
           )
           
           # Apply configuration
           self.transmission_interval = self.config.get('transmission_interval', 30)
           self.discovery_timeout = self.config.get('discovery_timeout', 10)
           
       def load_config(self, config_path: str) -> dict:
           """Load sensor configuration from YAML file"""
           config_file = Path(config_path)
           if config_file.exists():
               with open(config_file, 'r') as f:
                   return yaml.safe_load(f)
           else:
               # Create default configuration
               default_config = {
                   'device_id': 0x87654321,
                   'location': 'Living Room',
                   'base_temperature': 20.0,
                   'temperature_range': 5.0,
                   'transmission_interval': 30,
                   'discovery_timeout': 10,
                   'log_level': 'INFO'
               }
               with open(config_file, 'w') as f:
                   yaml.dump(default_config, f, default_flow_style=False)
               return default_config

Data Logging
~~~~~~~~~~~~

Add local data logging capabilities:

.. code-block:: python

   import csv
   from datetime import datetime

   class LoggingTemperatureSensor(ConfigurableTemperatureSensor):
       def __init__(self, config_path: str):
           super().__init__(config_path)
           self.log_file = self.config.get('log_file', 'sensor_data.csv')
           self.init_logging()
           
       def init_logging(self):
           """Initialize CSV logging"""
           log_path = Path(self.log_file)
           if not log_path.exists():
               with open(log_path, 'w', newline='') as f:
                   writer = csv.writer(f)
                   writer.writerow([
                       'timestamp', 'device_id', 'location', 
                       'temperature', 'humidity', 'transmitted'
                   ])
                   
       async def run_sensor_loop(self):
           """Enhanced sensor loop with logging"""
           self.logger.info("Starting temperature monitoring with data logging")
           
           while self.running:
               try:
                   temperature = self.read_temperature()
                   humidity = self.read_humidity()
                   timestamp = datetime.now()
                   transmitted = False
                   
                   # Log data locally first
                   self.log_data(timestamp, temperature, humidity, transmitted)
                   
                   if not self.connected:
                       await self.connect_to_hub()
                       
                   # Prepare and send sensor data
                   sensor_data = {
                       'device_type': 'temperature',
                       'device_id': f"{self.device_id:08X}",
                       'location': self.location,
                       'timestamp': int(timestamp.timestamp()),
                       'temperature': round(temperature, 2),
                       'humidity': round(humidity, 1),
                       'unit': 'celsius'
                   }
                   
                   await self.protocol.send_sensor_data(sensor_data)
                   transmitted = True
                   
                   # Update log with transmission status
                   self.update_log_transmission(timestamp, transmitted)
                   
                   self.logger.info(
                       f"Sent data: {temperature:.1f}°C, {humidity:.1f}% humidity"
                   )
                   
                   await asyncio.sleep(self.transmission_interval)
                   
               except Exception as e:
                   self.logger.error(f"Error in sensor loop: {e}")
                   self.connected = False
                   await asyncio.sleep(5)
                   
       def log_data(self, timestamp: datetime, temperature: float, 
                   humidity: float, transmitted: bool):
           """Log sensor data to CSV file"""
           with open(self.log_file, 'a', newline='') as f:
               writer = csv.writer(f)
               writer.writerow([
                   timestamp.isoformat(),
                   f"{self.device_id:08X}",
                   self.location,
                   temperature,
                   humidity,
                   transmitted
               ])

Testing the Temperature Sensor
------------------------------

Unit Tests
~~~~~~~~~~

.. code-block:: python

   import pytest
   import asyncio
   from unittest.mock import AsyncMock, MagicMock, patch

   @pytest.mark.asyncio
   async def test_temperature_reading():
       """Test temperature reading simulation"""
       sensor = TemperatureSensor(0x12345678, "Test Room", 20.0, 5.0)
       
       # Read multiple samples
       temperatures = [sensor.read_temperature() for _ in range(100)]
       
       # Check reasonable range
       assert all(0 <= temp <= 50 for temp in temperatures)
       
       # Check that readings vary (not constant)
       assert len(set(temperatures)) > 10
       
   @pytest.mark.asyncio
   async def test_sensor_initialization():
       """Test sensor component initialization"""
       sensor = TemperatureSensor(0x12345678, "Test Room")
       
       with patch('shdc.network.transport.UDPTransport') as mock_transport:
           mock_transport.return_value.start = AsyncMock()
           
           with patch('shdc.core.protocol.SHDCProtocol') as mock_protocol:
               mock_protocol.return_value.start = AsyncMock()
               
               await sensor.initialize_components()
               
               assert sensor.transport is not None
               assert sensor.protocol is not None

Integration Test
~~~~~~~~~~~~~~~

.. code-block:: python

   async def test_sensor_hub_integration():
       """Test complete sensor-hub integration"""
       import subprocess
       import tempfile
       import os
       
       # Create temporary config
       config = {
           'device_id': 0x87654321,
           'location': 'Test Room',
           'transmission_interval': 5,
           'discovery_timeout': 5
       }
       
       with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
           yaml.dump(config, f)
           config_path = f.name
           
       try:
           # Start test hub
           hub_process = subprocess.Popen([
               'python', '-m', 'shdc.cli.hub',
               'run', '0x12345678',
               '--port', '56701'
           ])
           
           # Wait for hub to start
           await asyncio.sleep(2)
           
           # Start sensor
           sensor = ConfigurableTemperatureSensor(config_path)
           
           # Run sensor for a short time
           sensor_task = asyncio.create_task(sensor.start())
           await asyncio.sleep(15)  # Run for 15 seconds
           
           # Stop sensor
           await sensor.stop()
           sensor_task.cancel()
           
           # Check that data was transmitted
           assert sensor.connected
           
       finally:
           # Cleanup
           hub_process.terminate()
           hub_process.wait()
           os.unlink(config_path)

Deployment Example
-----------------

Create a deployment script:

.. code-block:: python

   #!/usr/bin/env python3
   """
   Temperature Sensor Deployment Script
   
   This script demonstrates how to deploy temperature sensors in production.
   """
   
   import argparse
   import asyncio
   import logging
   import signal
   import sys
   from pathlib import Path

   def setup_logging(log_level: str, log_file: str = None):
       """Setup logging configuration"""
       level = getattr(logging, log_level.upper(), logging.INFO)
       
       handlers = [logging.StreamHandler()]
       if log_file:
           handlers.append(logging.FileHandler(log_file))
           
       logging.basicConfig(
           level=level,
           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
           handlers=handlers
       )

   async def main():
       parser = argparse.ArgumentParser(description='SHDC Temperature Sensor')
       parser.add_argument('config', help='Configuration file path')
       parser.add_argument('--log-level', default='INFO', 
                          choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
       parser.add_argument('--log-file', help='Log file path')
       parser.add_argument('--pid-file', help='PID file path')
       
       args = parser.parse_args()
       
       # Setup logging
       setup_logging(args.log_level, args.log_file)
       
       # Write PID file for process management
       if args.pid_file:
           with open(args.pid_file, 'w') as f:
               f.write(str(os.getpid()))
               
       # Create and start sensor
       sensor = LoggingTemperatureSensor(args.config)
       
       # Handle graceful shutdown
       def signal_handler(signum, frame):
           logging.info(f"Received signal {signum}, shutting down...")
           asyncio.create_task(shutdown(sensor))
           
       signal.signal(signal.SIGINT, signal_handler)
       signal.signal(signal.SIGTERM, signal_handler)
       
       try:
           await sensor.start()
       except Exception as e:
           logging.error(f"Sensor failed: {e}")
           sys.exit(1)
           
   async def shutdown(sensor):
       """Graceful shutdown"""
       await sensor.stop()
       sys.exit(0)

   if __name__ == "__main__":
       asyncio.run(main())

This comprehensive temperature sensor example demonstrates realistic sensor simulation,
robust error handling, configuration management, and production deployment practices.
