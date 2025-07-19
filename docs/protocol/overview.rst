Protocol Overview
=================

The Smart Home Device Communications (SHDC) protocol v1.0 defines secure
communication between smart home devices using a hub-and-sensor architecture.

Network Architecture
--------------------

Hub-Sensor Topology
~~~~~~~~~~~~~~~~~~~

SHDC uses a star topology where sensors communicate with a central hub.
The hub serves as the control center that coordinates all sensor devices:

* **Hub**: Central control and coordination point
* **Sensors**: Various device types (temperature, motion, door, humidity, light controllers)
* **Communication**: All sensors connect directly to the hub
* **Scalability**: Single hub can manage multiple sensor types

Transport Layer
~~~~~~~~~~~~~~~

* **Primary Transport**: UDP on port 56700
* **Discovery**: UDP multicast to 239.255.0.1:56700
* **Data Communication**: UDP unicast between devices
* **Fallback**: TCP on port 56700 for reliability-critical operations

Packet Format
-------------

All SHDC messages follow a consistent packet structure:

.. code-block:: text

   +------------------+--------------------+---------------------+
   | Header (12 B)    | Encrypted Payload  | Signature (64 B)    |
   +------------------+--------------------+---------------------+

Header Structure
~~~~~~~~~~~~~~~~

The 12-byte header contains essential message metadata:

.. list-table:: Header Fields
   :header-rows: 1
   :widths: 20 10 70

   * - Field
     - Size
     - Description
   * - Type
     - 1 B
     - Message type code (0x00-0x06)
   * - Device ID
     - 4 B
     - Unique device identifier
   * - Timestamp
     - 4 B
     - UNIX timestamp for replay protection
   * - Nonce
     - 3 B
     - Random nonce for additional security

Encrypted Payload
~~~~~~~~~~~~~~~~~

The payload is encrypted using AES-256-GCM:

* **Algorithm**: AES-256-GCM
* **Key**: Session key established during device joining
* **IV**: Derived from timestamp and nonce
* **Authentication**: Built-in with GCM mode

Digital Signature
~~~~~~~~~~~~~~~~~

All messages are signed using Ed25519:

* **Algorithm**: Ed25519
* **Key Size**: 32 bytes (private), 32 bytes (public)
* **Signature Size**: 64 bytes
* **Coverage**: Header + Encrypted Payload

Message Types
-------------

The protocol defines seven core message types:

Discovery Messages
~~~~~~~~~~~~~~~~~~

.. list-table:: Discovery Message Types
   :header-rows: 1
   :widths: 10 20 20 50

   * - Code
     - Name
     - Direction
     - Purpose
   * - 0x00
     - HUB_DISCOVERY_REQ
     - Sensor → Hub
     - Broadcast to discover available hubs
   * - 0x06
     - HUB_DISCOVERY_RESP
     - Hub → Sensor
     - Unicast response with hub identity

Device Management
~~~~~~~~~~~~~~~~~

.. list-table:: Device Management Message Types
   :header-rows: 1
   :widths: 10 20 20 50

   * - Code
     - Name
     - Direction
     - Purpose
   * - 0x02
     - JOIN_REQUEST
     - Sensor → Hub
     - Request to join hub network
   * - 0x03
     - JOIN_RESPONSE
     - Hub → Sensor
     - Response with session keys and config

Data Exchange
~~~~~~~~~~~~~

.. list-table:: Data Exchange Message Types
   :header-rows: 1
   :widths: 10 20 20 50

   * - Code
     - Name
     - Direction
     - Purpose
   * - 0x01
     - EVENT_REPORT
     - Sensor → Hub
     - Sensor data and event transmission
   * - 0x04
     - BROADCAST_COMMAND
     - Hub → Sensors
     - Commands broadcast to sensors

Security Management
~~~~~~~~~~~~~~~~~~~

.. list-table:: Security Message Types
   :header-rows: 1
   :widths: 10 20 20 50

   * - Code
     - Name
     - Direction
     - Purpose
   * - 0x05
     - KEY_ROTATION
     - Hub ↔ Sensor
     - Update session or group keys

Security Model
--------------

Defense in Depth
~~~~~~~~~~~~~~~~

SHDC implements multiple security layers:

1. **Device Identity**: Ed25519 keypairs for each device
2. **Message Authentication**: Digital signatures on all messages
3. **Data Encryption**: AES-256-GCM for payload protection
4. **Replay Protection**: Timestamp validation and nonce tracking
5. **Key Rotation**: Regular updates of session keys

Cryptographic Primitives
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Cryptographic Algorithms
   :header-rows: 1
   :widths: 30 30 40

   * - Purpose
     - Algorithm
     - Key/Parameter Size
   * - Digital Signatures
     - Ed25519
     - 32-byte keys, 64-byte signatures
   * - Symmetric Encryption
     - AES-256-GCM
     - 32-byte keys, 12-byte nonces
   * - Key Derivation
     - HKDF-SHA256
     - Variable length output
   * - Random Generation
     - OS cryptographic RNG
     - N/A

Authentication Flow
~~~~~~~~~~~~~~~~~~~

Device authentication follows a secure handshake:

**1. Discovery Phase**
   - Sensor sends HUB_DISCOVERY_REQ (signed)
   - Hub responds with HUB_DISCOVERY_RESP (signed, includes hub public key)

**2. Joining Phase**
   - Sensor sends JOIN_REQUEST (sensor public key, capabilities)
   - Hub validates sensor identity
   - Hub sends JOIN_RESPONSE (encrypted session key, configuration)

**3. Secure Communication**
   - Sensor sends EVENT_REPORT (encrypted with session key)
   - Hub sends BROADCAST_COMMAND (encrypted with broadcast key)

Protocol States
---------------

Hub States
~~~~~~~~~~

Hub devices follow these state transitions:

* **Stopped** → **Starting**: Initialize hub components
* **Starting** → **Listening**: Successfully bind to network port
* **Listening** → **Processing**: Receive message from sensor
* **Processing** → **Listening**: Complete message handling
* **Listening** → **Stopped**: Graceful shutdown
* **Processing** → **Stopped**: Fatal error encountered

Sensor States
~~~~~~~~~~~~~

Sensor devices follow these state transitions:

* **Disconnected** → **Discovering**: Start hub discovery process
* **Discovering** → **Joining**: Find available hub
* **Joining** → **Connected**: Successfully join hub network
* **Connected** → **Transmitting**: Send sensor data
* **Transmitting** → **Connected**: Complete data transmission
* **Connected** → **Disconnected**: Lose connection to hub

Error Handling
--------------

The protocol includes comprehensive error handling:

Network Errors
~~~~~~~~~~~~~~

* **Timeout**: Exponential backoff for retransmissions
* **Unreachable**: Automatic hub rediscovery
* **Congestion**: Rate limiting and backpressure

Security Errors
~~~~~~~~~~~~~~~

* **Invalid Signature**: Message rejection and logging
* **Replay Attack**: Timestamp validation and nonce tracking
* **Authentication Failure**: Connection termination and blacklisting

Protocol Errors
~~~~~~~~~~~~~~~

* **Malformed Messages**: Parsing error handling
* **Unknown Message Types**: Graceful degradation
* **State Violations**: State machine error recovery

Performance Considerations
--------------------------

Packet Size Limits
~~~~~~~~~~~~~~~~~~

* **Maximum Packet Size**: 512 bytes
* **Header Overhead**: 12 bytes
* **Signature Overhead**: 64 bytes
* **Available Payload**: 436 bytes (encrypted)

Timing Requirements
~~~~~~~~~~~~~~~~~~~

* **Discovery Timeout**: 1-5 seconds
* **Join Timeout**: 5-10 seconds
* **Heartbeat Interval**: 30-300 seconds
* **Key Rotation**: 24 hours (configurable)

Scalability
~~~~~~~~~~~

* **Sensors per Hub**: Recommended < 100
* **Message Rate**: < 10 messages/second per sensor
* **Network Bandwidth**: Minimal (~1KB/sensor/minute)

Compatibility
-------------

Protocol Versioning
~~~~~~~~~~~~~~~~~~~

* **Current Version**: SHDC v1.0
* **Version Field**: Reserved in header for future use
* **Backward Compatibility**: Planned for future versions

Platform Support
~~~~~~~~~~~~~~~~

* **Python**: 3.8+ (this implementation)
* **Operating Systems**: Linux, macOS, Windows
* **Embedded**: Compatible with MicroPython
* **Network**: IPv4 and IPv6 support

Standards Compliance
~~~~~~~~~~~~~~~~~~~~

* **Cryptography**: FIPS 140-2 approved algorithms
* **Networking**: RFC-compliant UDP implementation
* **Security**: Industry best practices
