# SHDC Python Library

A comprehensive Python implementation of the Smart Home Device Communications (SHDC) protocol v1.0. This library provides secure, efficient communication between smart home devices using Ed25519 digital signatures and AES-256-GCM encryption over UDP.

## Features

- **Secure Communication**: Ed25519 digital signatures and AES-256-GCM encryption
- **Hub-Sensor Architecture**: Star topology with automatic device discovery
- **Key Management**: Automatic key generation, rotation, and secure storage
- **Network Transport**: UDP multicast/broadcast/unicast with asyncio support
- **CLI Tools**: Ready-to-use command-line tools for hubs and sensors
- **Example Applications**: Complete demonstrations of home monitoring systems

## Installation

```bash
pip install shdc
```

Or install from source:

```bash
git clone <repository-url>
cd py-shdc
pip install -e .
```

## Quick Start

### Running a Hub

```bash
# Start a hub with device ID 0x12345678
shdc-hub run 0x12345678

# Start with debug logging on specific interface
shdc-hub run 0x12345678 --interface eth0 --debug
```

### Running a Sensor

```bash
# Start a temperature sensor that auto-discovers hubs
shdc-sensor run 0x87654321 temperature

# Connect to a specific hub
shdc-sensor run 0x87654321 humidity --hub 192.168.1.100:56700

# Send custom sensor data every 10 seconds
shdc-sensor run 0x87654321 motion --data sensor_data.json --interval 10
```

### Discovering Hubs

```bash
# Discover available hubs on the network
shdc-sensor discover
```

## Programming Interface

### Basic Hub Example

```python
import asyncio
from shdc.core.protocol import SHDCProtocol, DeviceRole
from shdc.crypto.keys import KeyManager
from shdc.network.transport import UDPTransport

async def run_hub():
    # Initialize components
    device_id = 0x12345678
    key_manager = KeyManager(device_id)
    private_key, public_key = key_manager.generate_device_keys()
    
    transport = UDPTransport("0.0.0.0", 56700)
    await transport.start()
    
    # Create hub protocol
    protocol = SHDCProtocol(
        device_id=device_id,
        device_role=DeviceRole.HUB,
        private_key=private_key,
        key_manager=key_manager,
        transport=transport
    )
    
    # Set up event handlers
    async def on_device_joined(device_info):
        print(f"Device joined: {device_info.device_id:08X} ({device_info.device_type})")
    
    async def on_sensor_data(device_id, data):
        print(f"Sensor data from {device_id:08X}: {data}")
    
    protocol.on_device_joined = on_device_joined
    protocol.on_sensor_data = on_sensor_data
    
    # Start the hub
    await protocol.start()
    print("Hub running...")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await protocol.stop()

# Run the hub
asyncio.run(run_hub())
```

### Basic Sensor Example

```python
import asyncio
import time
from shdc.core.protocol import SHDCProtocol, DeviceRole
from shdc.crypto.keys import KeyManager
from shdc.network.transport import UDPTransport
from shdc.network.discovery import HubDiscovery

async def run_sensor():
    # Initialize components
    device_id = 0x87654321
    key_manager = KeyManager(device_id)
    private_key, public_key = key_manager.generate_device_keys()
    
    transport = UDPTransport("0.0.0.0", 0)  # Any available port
    await transport.start()
    
    # Create sensor protocol
    protocol = SHDCProtocol(
        device_id=device_id,
        device_role=DeviceRole.SENSOR,
        private_key=private_key,
        key_manager=key_manager,
        transport=transport
    )
    
    protocol.device_type = "temperature"
    await protocol.start()
    
    # Discover and join hub
    discovery = HubDiscovery(transport, key_manager)
    await discovery.start_discovery()
    await asyncio.sleep(5)  # Wait for discovery
    
    hubs = discovery.get_discovered_hubs()
    if hubs:
        hub = hubs[0]
        success = await protocol.join_hub(hub.address, hub.port)
        if success:
            print("Joined hub successfully")
        
    await discovery.stop_discovery()
    
    # Send sensor data
    try:
        while True:
            sensor_data = {
                'device_type': 'temperature',
                'temperature': 25.5,
                'unit': 'celsius',
                'timestamp': int(time.time())
            }
            
            await protocol.send_sensor_data(sensor_data)
            print("Sent temperature data")
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        await protocol.stop()

# Run the sensor
asyncio.run(run_sensor())
```

## Architecture

The SHDC library consists of several key components:

### Core Components

- **`shdc.core.protocol`**: Main SHDC protocol implementation
- **`shdc.core.messages`**: Message types and data structures
- **`shdc.crypto.encryption`**: Cryptographic operations (Ed25519, AES-256-GCM)
- **`shdc.crypto.keys`**: Key management and storage
- **`shdc.network.transport`**: UDP transport layer
- **`shdc.network.discovery`**: Hub discovery mechanism

### Network Protocol

- **Port**: UDP 56700 (configurable)
- **Discovery**: Multicast to 224.0.1.187:56700
- **Transport**: Unicast for device communication
- **Security**: Ed25519 signatures + AES-256-GCM encryption

### Message Types

- `DISCOVERY_REQUEST` (0x00): Hub discovery
- `DISCOVERY_RESPONSE` (0x01): Hub advertisement
- `JOIN_REQUEST` (0x02): Device join request
- `JOIN_RESPONSE` (0x03): Join response with status
- `SENSOR_DATA` (0x04): Sensor data transmission
- `CONTROL_MESSAGE` (0x05): Control/command messages
- `STATUS_REQUEST` (0x06): Status information request

## Examples

The `examples/` directory contains complete demonstration applications:

### Home Monitoring System

A comprehensive example showing multi-sensor data collection with alerts:

```bash
cd examples
python home_monitoring.py
```

Features:
- Multi-sensor support (temperature, humidity, motion, door sensors)
- Real-time data collection and logging
- Automated alerts for threshold violations
- Data export functionality
- Device status monitoring

### Temperature Sensor Simulator

A realistic temperature sensor with daily cycles:

```bash
cd examples
python temperature_sensor.py
```

Features:
- Realistic temperature simulation with daily variations
- Automatic hub discovery and joining
- Configurable data transmission intervals
- Location-based sensor identification

## Configuration

### Key Storage

Keys are automatically stored in `~/.shdc/keys/{device_id}/` with restrictive permissions (600). Key files include:

- Device identity keys (Ed25519)
- Session keys (AES-256)
- Broadcast keys (AES-256)

### Environment Variables

- `SHDC_KEY_PATH`: Override default key storage location
- `SHDC_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `SHDC_DEFAULT_PORT`: Override default UDP port (56700)

## Security

The SHDC protocol implements defense-in-depth security:

1. **Device Authentication**: Ed25519 digital signatures
2. **Message Encryption**: AES-256-GCM with random nonces
3. **Key Rotation**: Automatic session and broadcast key rotation
4. **Replay Protection**: Timestamp validation and nonce tracking
5. **Secure Storage**: Keys stored with restrictive filesystem permissions

## Testing

Run the integration test to verify complete system functionality:

```bash
python test_integration.py
```

This test validates:
- Hub and sensor startup
- Device discovery and joining
- Secure data transmission
- Control message exchange
- Key management operations
- Error handling scenarios

## CLI Reference

### Hub Commands

```bash
shdc-hub run <device_id> [options]     # Run SHDC hub
shdc-hub status <device_id>            # Show hub status
shdc-hub reset-keys <device_id>        # Reset device keys
```

### Sensor Commands

```bash
shdc-sensor run <device_id> <type> [options]  # Run sensor
shdc-sensor discover [options]                # Discover hubs
shdc-sensor status <device_id>                # Show sensor status
```

### Common Options

- `--debug` / `-d`: Enable debug logging
- `--interface` / `-i`: Network interface to bind
- `--port` / `-p`: UDP port to use
- `--hub`: Specific hub address to connect to
- `--interval`: Data transmission interval
- `--data`: JSON file with custom sensor data

## Protocol Specification

This implementation follows the SHDC v1.0 protocol specification. Key features:

- **Packet Format**: 4-byte header + encrypted payload
- **Device IDs**: 32-bit unique identifiers
- **Encryption**: AES-256-GCM with 96-bit nonces
- **Signatures**: Ed25519 with 32-byte public keys
- **Discovery**: Multicast-based with capability negotiation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Commit your changes (`git commit -am 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions:

- Create an issue on GitHub
- Review the protocol specification in `../design.md`
- Check the examples directory for usage patterns
- Run the integration test to verify functionality

```bash
pip install py-shdc
```

## Quick Start

### Creating a Hub

```python
from shdc import SHDCProtocol, KeyManager

# Create and start a hub
hub = SHDCProtocol(role="hub")
hub.start()
print("Hub started and listening for devices...")
```

### Creating a Sensor

```python
from shdc import SHDCProtocol

# Create a sensor
sensor = SHDCProtocol(role="sensor")

# Discover and join network
sensor.discover_hub()
sensor.join_network()

# Send an event
sensor.send_event(event_type=0x01, data=b"Motion detected")
```

## Features

- **Full SHDC v1.0 protocol implementation**
- **Ed25519 cryptographic security** for device identity and signing
- **AES-256-GCM encryption** for session encryption
- **Automatic hub discovery** via UDP broadcast
- **Secure device joining** with cryptographic handshake
- **Message replay protection** with timestamps and nonces
- **Key rotation** support for enhanced security
- **UDP transport** with TCP fallback option
- **Multicast broadcasting** for hub-to-device commands

## Protocol Overview

The SHDC protocol defines secure communication between:
- **Sensors**: Embedded nodes sending event/status data
- **Hub**: Local control node handling routing and authentication

### Message Types

| Code | Direction     | Name                | Description                  |
|------|---------------|---------------------|------------------------------|
| 0x00 | Sensor → Hub  | HUB_DISCOVERY_REQ   | Broadcast to discover hub    |
| 0x01 | Sensor → Hub  | EVENT_REPORT        | Event or status message      |
| 0x02 | Sensor → Hub  | JOIN_REQUEST        | Join handshake initiation    |
| 0x03 | Hub → Sensor  | JOIN_RESPONSE       | Response with keys/config    |
| 0x04 | Hub → Sensor  | BROADCAST_COMMAND   | Broadcasted command          |
| 0x05 | Any           | KEY_ROTATION        | Key update                   |
| 0x06 | Hub → Sensor  | HUB_DISCOVERY_RESP  | Unicast response with identity |

## Security Features

- **Ed25519 digital signatures** for message authentication
- **AES-256-GCM encryption** for confidentiality
- **Replay protection** using timestamps and nonces
- **Secure key management** with automatic rotation
- **Certificate-based device validation**
- **Network isolation** and quarantine capabilities

## Example Usage

### Hub Implementation

```python
import asyncio
from shdc import SHDCProtocol, MessageType

async def main():
    # Initialize hub
    hub = SHDCProtocol(role="hub", port=56700)
    
    # Set up event handlers
    @hub.on_event(MessageType.EVENT_REPORT)
    async def handle_sensor_event(device_id, event_type, data):
        print(f"Sensor {device_id}: Event {event_type} - {data}")
    
    # Start hub
    await hub.start()
    print("Hub running...")
    
    # Keep running
    await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
```

### Sensor Implementation

```python
import asyncio
from shdc import SHDCProtocol

async def main():
    # Initialize sensor
    sensor = SHDCProtocol(role="sensor")
    
    # Connect to hub
    await sensor.discover_hub()
    await sensor.join_network()
    
    # Send periodic events
    while True:
        await sensor.send_event(0x01, b"Heartbeat")
        await asyncio.sleep(300)  # Every 5 minutes

if __name__ == "__main__":
    asyncio.run(main())
```

## Requirements

- Python 3.8+
- cryptography >= 41.0.0
- pynacl >= 1.5.0

## Development

### Installation for Development

```bash
git clone https://github.com/envopentech/py-shdc.git
cd py-shdc
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black shdc/
isort shdc/
```

## License

GNU LGPL - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests to our GitHub repository.

## Support

- GitHub Issues: https://github.com/envopentech/py-shdc/issues
- Email: argo@envopen.org
