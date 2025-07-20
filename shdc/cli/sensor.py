#!/usr/bin/env python3
"""
SHDC Sensor CLI Tool

Command-line interface for running an SHDC sensor device.
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
from typing import Any, Dict, Optional

from shdc.core.protocol import DeviceRole, SHDCProtocol
from shdc.crypto.keys import KeyManager
from shdc.network.discovery import HubDiscovery
from shdc.network.transport import UDPTransport


class SHDCSensorCLI:
    """SHDC Sensor command-line interface"""

    def __init__(self):
        self.protocol: Optional[SHDCProtocol] = None
        self.hub_discovery: Optional[HubDiscovery] = None
        self.running = False

    async def run_sensor(
        self,
        device_id: int,
        device_type: str,
        auto_join: bool = True,
        hub_address: Optional[str] = None,
        data_file: Optional[str] = None,
        interval: int = 30,
        debug: bool = False,
    ):
        """
        Run SHDC sensor.

        Args:
            device_id: Sensor device ID
            device_type: Type of sensor (e.g., 'temperature', 'humidity')
            auto_join: Automatically discover and join hub
            hub_address: Specific hub address to connect to
            data_file: JSON file with sensor data to send
            interval: Data transmission interval in seconds
            debug: Enable debug logging
        """
        # Set up logging
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        logger = logging.getLogger("shdc.sensor")

        try:
            # Initialize key manager
            logger.info(f"Initializing sensor {device_id:08X} ({device_type})")
            key_manager = KeyManager(device_id)

            # Generate or load device keys
            private_key, public_key = key_manager.generate_device_keys()
            logger.info("Device keys ready")

            # Initialize transport
            transport = UDPTransport(
                0, "0.0.0.0"
            )  # Bind to all interfaces for discovery  # nosec B104
            await transport.start()
            logger.info("UDP transport started")

            # Initialize protocol
            self.protocol = SHDCProtocol(
                role=DeviceRole.SENSOR,
                device_id=device_id,
                port=0,  # Use any available port
            )

            # Note: device_type and start() not implemented in current SHDCProtocol
            # Store device type separately for now
            self.device_type = device_type

            logger.info(f"SHDC sensor started - ID: {device_id:08X}")

            # Load sensor data if provided
            sensor_data = None
            if data_file:
                try:
                    with open(data_file, "r") as f:
                        sensor_data = json.load(f)
                    logger.info(f"Loaded sensor data from {data_file}")
                except Exception as e:
                    logger.warning(f"Failed to load sensor data: {e}")

            # Discover and join hub
            if auto_join or hub_address:
                if hub_address:
                    # Connect to specific hub
                    host, port = (
                        hub_address.split(":")
                        if ":" in hub_address
                        else (hub_address, 56700)
                    )
                    port = int(port)

                    logger.info(f"Connecting to hub at {host}:{port}")
                    # Note: join_hub() not implemented in current SHDCProtocol
                    logger.warning("Direct hub connection not yet implemented")
                    success = False
                    if not success:
                        logger.error("Failed to join hub")
                        return 1
                else:
                    # Discover hubs
                    logger.info("Discovering hubs...")
                    self.hub_discovery = HubDiscovery()

                    # Note: start_discovery() not implemented
                    logger.warning("Hub discovery not yet implemented")

                    # Wait for discovery
                    await asyncio.sleep(5)

                    # Note: get_discovered_hubs() not implemented
                    logger.warning("Hub discovery methods not yet implemented")
                    hubs = []

                    if not hubs:
                        logger.error("No hubs discovered")
                        return 1

                    # Join first available hub
                    hub = hubs[0]
                    logger.info(
                        f"Joining hub {hub.device_id:08X} at {hub.address}:{hub.port}"
                    )
                    # Note: join_hub() not implemented
                    success = False
                    if not success:
                        logger.error("Failed to join hub")
                        return 1

                logger.info("Successfully joined hub")

            # Set up signal handlers
            def signal_handler(signum, frame):
                logger.info("Received shutdown signal")
                self.running = False

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Main loop
            self.running = True
            last_data_time = 0

            while self.running:
                try:
                    current_time = asyncio.get_event_loop().time()

                    # Send sensor data periodically
                    if (current_time - last_data_time) >= interval:
                        # Note: hub_address not implemented, assume connected
                        hub_connected = True
                        if hub_connected:
                            # Generate or use provided sensor data
                            if sensor_data:
                                data_to_send = sensor_data.copy()
                                # Add timestamp
                                data_to_send["timestamp"] = int(current_time)
                            else:
                                # Generate dummy data based on device type
                                data_to_send = self._generate_dummy_data(
                                    device_type, current_time
                                )

                            # Send data
                            try:
                                # Note: send_sensor_data() not implemented
                                logger.info(f"Would send sensor data: {data_to_send}")
                                logger.warning("send_sensor_data() not yet implemented")
                            except Exception as e:
                                logger.error(f"Failed to send sensor data: {e}")

                        last_data_time = current_time

                    await asyncio.sleep(1)

                    # Periodic maintenance
                    key_manager.cleanup_expired_keys()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    if debug:
                        import traceback

                        traceback.print_exc()

        except Exception as e:
            logger.error(f"Failed to start sensor: {e}")
            if debug:
                import traceback

                traceback.print_exc()
            return 1

        finally:
            # Cleanup
            if self.hub_discovery:
                # Note: stop_discovery() not implemented
                logger.info("Would stop hub discovery")

            if self.protocol:
                logger.info("Shutting down sensor")
                # Note: stop() not implemented

            logger.info("Sensor stopped")

        return 0

    def _generate_dummy_data(
        self, device_type: str, timestamp: float
    ) -> Dict[str, Any]:
        """Generate dummy sensor data based on device type"""
        import random

        data = {"timestamp": int(timestamp), "device_type": device_type}

        # Note: Using standard random for demo/test data generation, not security
        if device_type == "temperature":
            data["temperature"] = round(
                20 + random.uniform(-5, 15), 1  # nosec B311
            )  # 15-35°C
            data["unit"] = "celsius"
        elif device_type == "humidity":
            data["humidity"] = round(random.uniform(30, 80), 1)  # nosec B311 # 30-80%
            data["unit"] = "percent"
        elif device_type == "pressure":
            data["pressure"] = round(
                1013.25 + random.uniform(-50, 50), 2  # nosec B311
            )  # ±50 hPa
            data["unit"] = "hPa"
        elif device_type == "light":
            data["illuminance"] = random.randint(0, 1000)  # nosec B311 # 0-1000 lux
            data["unit"] = "lux"
        elif device_type == "motion":
            data["motion_detected"] = random.choice([True, False])  # nosec B311
        elif device_type == "door":
            data["door_open"] = random.choice([True, False])  # nosec B311
        else:
            # Generic sensor
            data["value"] = round(random.uniform(0, 100), 2)  # nosec B311

        return data

    def show_status(self, device_id: int):
        """Show sensor status"""
        print(f"SHDC Sensor Status - Device ID: {device_id:08X}")

        # Check if keys exist
        key_manager = KeyManager(device_id)
        keys = key_manager.list_keys()

        print(f"Stored keys: {len(keys)}")
        for key_info in keys:
            status = "EXPIRED" if key_info.is_expired() else "VALID"
            print(f"  {key_info.key_id}: {key_info.key_type} ({status})")

        # Show storage path
        print(f"Key storage: {key_manager.storage_path}")

    def discover_hubs(self, timeout: int = 10):
        """Discover available hubs"""

        async def _discover():
            # Initialize minimal transport
            transport = UDPTransport(
                0, "0.0.0.0"
            )  # Bind to all interfaces for discovery  # nosec B104
            await transport.start()

            try:
                # Note: Discovery would be initialized here
                print(f"Discovering hubs for {timeout} seconds...")
                # Note: start_discovery() not implemented
                print("Warning: Hub discovery not yet implemented")
                await asyncio.sleep(timeout)

                # Note: get_discovered_hubs() not implemented
                hubs = []

                if hubs:
                    print(f"\nFound {len(hubs)} hub(s):")
                    for hub in hubs:
                        print(f"  Hub {hub.device_id:08X}")
                        print(f"    Address: {hub.address}:{hub.port}")
                        print(f"    Capabilities: {', '.join(hub.capabilities)}")
                        print(f"    Last seen: {hub.last_seen:.1f}s ago")
                        print()
                else:
                    print("No hubs discovered")

                # Note: stop_discovery() not implemented
                # discovery.stop_discovery() would be called here
            finally:
                await transport.stop()

        try:
            asyncio.run(_discover())
        except KeyboardInterrupt:
            print("\nDiscovery cancelled")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SHDC Sensor - Smart Home Device Communications Sensor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shdc-sensor run 0x87654321 temperature           # Run temperature sensor
  shdc-sensor run 0x87654321 humidity --debug      # Run with debug logging
  shdc-sensor run 0x87654321 motion --interval 10  # Send data every 10 seconds
  shdc-sensor run 0x87654321 light --hub 192.168.1.100:56700  # Connect to specific hub
  shdc-sensor run 0x87654321 temperature --data sensor_data.json  # Use custom data
  shdc-sensor discover                              # Discover available hubs
  shdc-sensor status 0x87654321                    # Show sensor status
        """,
    )

    parser.add_argument("--version", action="version", version="SHDC Sensor 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run SHDC sensor")
    run_parser.add_argument(
        "device_id", help="Sensor device ID (hex format, e.g., 0x87654321)"
    )
    run_parser.add_argument(
        "device_type", help="Sensor type (temperature, humidity, motion, etc.)"
    )
    run_parser.add_argument(
        "--hub", help="Hub address (host:port, e.g., 192.168.1.100:56700)"
    )
    run_parser.add_argument(
        "--no-auto-join",
        action="store_true",
        help="Disable automatic hub discovery and joining",
    )
    run_parser.add_argument("--data", help="JSON file with sensor data to send")
    run_parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Data transmission interval in seconds (default: 30)",
    )
    run_parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )

    # Discover command
    discover_parser = subparsers.add_parser("discover", help="Discover available hubs")
    discover_parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=10,
        help="Discovery timeout in seconds (default: 10)",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show sensor status")
    status_parser.add_argument("device_id", help="Sensor device ID (hex format)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create CLI instance
    cli = SHDCSensorCLI()

    # Execute command
    if args.command == "run":
        # Parse device ID
        try:
            if args.device_id.startswith("0x") or args.device_id.startswith("0X"):
                device_id = int(args.device_id, 16)
            else:
                device_id = int(args.device_id)

            if not (0 <= device_id <= 0xFFFFFFFF):
                print("Error: Device ID must be a 32-bit unsigned integer")
                return 1
        except ValueError:
            print("Error: Invalid device ID format")
            return 1

        try:
            return asyncio.run(
                cli.run_sensor(
                    device_id=device_id,
                    device_type=args.device_type,
                    auto_join=not args.no_auto_join,
                    hub_address=args.hub,
                    data_file=args.data,
                    interval=args.interval,
                    debug=args.debug,
                )
            )
        except KeyboardInterrupt:
            print("\nShutdown requested")
            return 0

    elif args.command == "discover":
        cli.discover_hubs(timeout=args.timeout)
        return 0

    elif args.command == "status":
        # Parse device ID
        try:
            if args.device_id.startswith("0x") or args.device_id.startswith("0X"):
                device_id = int(args.device_id, 16)
            else:
                device_id = int(args.device_id)
        except ValueError:
            print("Error: Invalid device ID format")
            return 1

        cli.show_status(device_id)
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
