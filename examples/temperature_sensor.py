#!/usr/bin/env python3
"""
Simple Temperature Sensor Simulator

A simple example that simulates a temperature sensor sending data to an SHDC hub.
"""

import asyncio
import logging
import math
import random
import time
from datetime import datetime

from shdc.core.protocol import DeviceRole, SHDCProtocol
from shdc.crypto.keys import KeyManager
from shdc.network.discovery import HubDiscovery
from shdc.network.transport import UDPTransport


class TemperatureSensor:
    """Simulated temperature sensor"""

    def __init__(self, device_id: int, location: str = "Living Room"):
        self.device_id = device_id
        self.location = location
        self.protocol: SHDCProtocol = None
        self.running = False

        # Temperature simulation parameters
        self.base_temp = 22.0  # Base temperature in Celsius
        self.daily_variation = 5.0  # Daily temperature variation
        self.noise = 0.5  # Random noise

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(f"temp_sensor_{device_id:08X}")

    async def start(self, hub_address: str = None):
        """Start the temperature sensor"""
        try:
            # Initialize key manager and generate keys
            key_manager = KeyManager(self.device_id)
            private_key, public_key = key_manager.generate_device_keys()

            # Initialize transport
            transport = UDPTransport(0, "0.0.0.0")  # Bind to any available port
            await transport.start()

            # Initialize protocol
            self.protocol = SHDCProtocol(
                device_id=self.device_id,
                device_role=DeviceRole.SENSOR,
                private_key=private_key,
                key_manager=key_manager,
                transport=transport,
            )

            self.protocol.device_type = "temperature"

            # Start protocol
            await self.protocol.start()

            self.logger.info(f"Temperature sensor started - ID: {self.device_id:08X}")
            self.logger.info(f"Location: {self.location}")

            # Discover and join hub
            if hub_address:
                # Connect to specific hub
                host, port = (
                    hub_address.split(":")
                    if ":" in hub_address
                    else (hub_address, 56700)
                )
                port = int(port)

                self.logger.info(f"Connecting to hub at {host}:{port}")
                success = await self.protocol.join_hub(host, port)
                if not success:
                    raise RuntimeError("Failed to join hub")
            else:
                # Discover hubs
                self.logger.info("Discovering hubs...")
                hub_discovery = HubDiscovery(transport, key_manager)
                await hub_discovery.start_discovery()

                # Wait for discovery
                await asyncio.sleep(5)

                # Get discovered hubs
                hubs = hub_discovery.get_discovered_hubs()
                if not hubs:
                    raise RuntimeError("No hubs discovered")

                # Join first available hub
                hub = hubs[0]
                self.logger.info(
                    f"Joining hub {hub.device_id:08X} at {hub.address}:{hub.port}"
                )
                success = await self.protocol.join_hub(hub.address, hub.port)
                if not success:
                    raise RuntimeError("Failed to join hub")

                await hub_discovery.stop_discovery()

            self.logger.info("Successfully joined hub")
            self.running = True

        except Exception as e:
            self.logger.error(f"Failed to start sensor: {e}")
            raise

    async def stop(self):
        """Stop the temperature sensor"""
        self.running = False
        if self.protocol:
            await self.protocol.stop()
        self.logger.info("Temperature sensor stopped")

    def get_temperature(self) -> float:
        """Generate realistic temperature reading"""
        # Get current time for daily variation
        current_hour = datetime.now().hour

        # Daily temperature cycle (cooler at night, warmer during day)
        daily_cycle = math.sin((current_hour - 6) * math.pi / 12) * self.daily_variation

        # Add some random noise
        noise = random.uniform(-self.noise, self.noise)

        # Calculate final temperature
        temperature = self.base_temp + daily_cycle + noise

        return round(temperature, 1)

    async def send_temperature_reading(self):
        """Send temperature reading to hub"""
        if not self.protocol or not self.protocol.hub_address:
            return

        temperature = self.get_temperature()
        timestamp = int(time.time())

        sensor_data = {
            "device_type": "temperature",
            "temperature": temperature,
            "unit": "celsius",
            "location": self.location,
            "timestamp": timestamp,
            "device_id": self.device_id,
        }

        try:
            await self.protocol.send_sensor_data(sensor_data)
            self.logger.info(f"Sent temperature reading: {temperature}°C")
        except Exception as e:
            self.logger.error(f"Failed to send temperature reading: {e}")

    async def run(self, interval: int = 30):
        """Run the sensor main loop"""
        self.logger.info(f"Starting temperature monitoring (interval: {interval}s)")

        last_reading_time = 0

        while self.running:
            try:
                current_time = time.time()

                # Send reading at specified interval
                if (current_time - last_reading_time) >= interval:
                    await self.send_temperature_reading()
                    last_reading_time = current_time

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in sensor loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying


async def run_temperature_sensor_demo():
    """Run temperature sensor demonstration"""
    print("=== SHDC Temperature Sensor Demo ===\n")

    # Create temperature sensor
    sensor_id = 0x87654321
    sensor = TemperatureSensor(sensor_id, "Kitchen")

    try:
        print("Starting temperature sensor...")
        await sensor.start()

        print(f"Temperature sensor {sensor_id:08X} is running")
        print("Sending temperature readings every 30 seconds...")
        print("Press Ctrl+C to stop\n")

        # Run sensor
        await sensor.run(interval=30)

    except KeyboardInterrupt:
        print("\nShutdown requested...")

    except Exception as e:
        print(f"Error in demo: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await sensor.stop()
        print("Temperature sensor demo completed.")


if __name__ == "__main__":
    # Run the temperature sensor demo
    asyncio.run(run_temperature_sensor_demo())
