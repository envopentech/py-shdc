SHDC Basics
===========

Understanding the SHDC Protocol
-------------------------------

The Smart Home Device Communications (SHDC) protocol is designed for secure,
efficient communication between smart home devices. It follows a hub-and-spoke
architecture where sensors communicate with a central hub.

Key Features
~~~~~~~~~~~~

* **Security**: Ed25519 digital signatures and AES-256-GCM encryption
* **Discovery**: Automatic hub discovery using UDP multicast
* **Simplicity**: Minimal overhead for embedded devices
* **Reliability**: Built-in retry mechanisms and error handling

Architecture Overview
~~~~~~~~~~~~~~~~~~~~~

.. mermaid::

   graph TB
       A[Hub] --> B[Temperature Sensor]
       A --> C[Motion Detector]
       A --> D[Door Sensor]
       A --> E[Humidity Sensor]
       
       subgraph "Network Communication"
           F[UDP Multicast Discovery]
           G[UDP Unicast Data]
           H[Ed25519 + AES-256-GCM]
       end

Device Roles
------------

Hub
~~~

The hub is the central coordinator in an SHDC network:

* Listens for device discovery requests
* Manages device authentication and joining
* Receives sensor data and events
* Sends commands to devices
* Handles key rotation and security

Example hub responsibilities:

.. code-block:: python

   # Hub handles multiple sensors
   async def on_sensor_data(device_id, data):
       if data['device_type'] == 'temperature':
           await handle_temperature_reading(device_id, data)
       elif data['device_type'] == 'motion':
           await handle_motion_detection(device_id, data)

Sensor
~~~~~~

Sensors are typically embedded devices that:

* Discover and join hub networks
* Collect and transmit data
* Respond to hub commands
* Maintain secure connections

Example sensor data transmission:

.. code-block:: python

   # Sensor sends periodic data
   sensor_data = {
       'device_type': 'temperature',
       'temperature': 23.5,
       'humidity': 45.2,
       'timestamp': int(time.time())
   }
   await protocol.send_sensor_data(sensor_data)

Protocol Flow
-------------

Device Discovery
~~~~~~~~~~~~~~~~

1. **Sensor Broadcast**: New sensor broadcasts discovery request
2. **Hub Response**: Available hubs respond with their capabilities
3. **Hub Selection**: Sensor selects a suitable hub

.. mermaid::

   sequenceDiagram
       participant S as Sensor
       participant H as Hub
       
       S->>H: HUB_DISCOVERY_REQ (broadcast)
       H->>S: HUB_DISCOVERY_RESP (unicast)
       S->>H: Selection decision

Device Joining
~~~~~~~~~~~~~~

1. **Join Request**: Sensor requests to join selected hub
2. **Authentication**: Hub verifies sensor identity
3. **Key Exchange**: Secure session established
4. **Join Confirmation**: Hub confirms successful joining

.. mermaid::

   sequenceDiagram
       participant S as Sensor
       participant H as Hub
       
       S->>H: JOIN_REQUEST (device ID, public key)
       H->>S: JOIN_RESPONSE (session key, configuration)
       S->>H: Acknowledgment
       Note over S,H: Secure session established

Data Communication
~~~~~~~~~~~~~~~~~~

1. **Data Collection**: Sensor gathers environmental data
2. **Encryption**: Data encrypted with session key
3. **Transmission**: Encrypted data sent to hub
4. **Processing**: Hub processes and responds

Message Types
-------------

The SHDC protocol defines several message types:

Discovery Messages
~~~~~~~~~~~~~~~~~~

* ``HUB_DISCOVERY_REQ`` (0x00): Sensor → Hub discovery request
* ``HUB_DISCOVERY_RESP`` (0x06): Hub → Sensor discovery response

Device Management
~~~~~~~~~~~~~~~~~

* ``JOIN_REQUEST`` (0x02): Sensor → Hub join request
* ``JOIN_RESPONSE`` (0x03): Hub → Sensor join response

Data Exchange
~~~~~~~~~~~~~

* ``EVENT_REPORT`` (0x01): Sensor → Hub data/event transmission
* ``BROADCAST_COMMAND`` (0x04): Hub → Sensor commands

Security
~~~~~~~~

* ``KEY_ROTATION`` (0x05): Key update messages

Security Model
--------------

Identity and Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each device has a unique Ed25519 keypair for identity:

.. code-block:: python

   # Generate device identity
   key_manager = KeyManager(device_id)
   private_key, public_key = key_manager.generate_device_keys()

Session Encryption
~~~~~~~~~~~~~~~~~~

Data is encrypted using AES-256-GCM with unique session keys:

.. code-block:: python

   # Session key established during joining
   crypto = SHDCCrypto()
   encrypted_data = crypto.encrypt_aes_gcm(data, session_key, nonce)

Message Authentication
~~~~~~~~~~~~~~~~~~~~~~

All messages are signed to prevent tampering:

.. code-block:: python

   # Sign message with device private key
   signature = crypto.sign_ed25519(message_data, private_key)

Error Handling
--------------

The SHDC library provides comprehensive error handling:

Network Errors
~~~~~~~~~~~~~~

.. code-block:: python

   try:
       await protocol.send_sensor_data(data)
   except TransportError as e:
       logger.error(f"Network error: {e}")
       await handle_network_failure()

Authentication Errors
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   try:
       success = await protocol.join_hub(hub_address, hub_port)
   except AuthenticationError as e:
       logger.error(f"Authentication failed: {e}")
       await regenerate_keys()

Timeout Handling
~~~~~~~~~~~~~~~~

.. code-block:: python

   try:
       await asyncio.wait_for(protocol.discover_hubs(), timeout=10.0)
   except asyncio.TimeoutError:
       logger.warning("Hub discovery timed out")
       await retry_discovery()

Best Practices
--------------

Device IDs
~~~~~~~~~~

* Use unique, random 32-bit device IDs
* Store device IDs persistently
* Never reuse device IDs across different physical devices

Key Management
~~~~~~~~~~~~~~

* Let the library handle key generation and storage
* Implement key rotation for long-running deployments
* Protect key storage directories with appropriate permissions

Network Configuration
~~~~~~~~~~~~~~~~~~~~~

* Use the standard SHDC port (56700) when possible
* Configure firewall rules for UDP traffic
* Consider network segmentation for IoT devices

Logging
~~~~~~~

* Enable debug logging during development
* Use structured logging for production systems
* Monitor for authentication and network errors

.. code-block:: python

   import logging
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   # Get SHDC logger
   logger = logging.getLogger('shdc')
   logger.setLevel(logging.DEBUG)
