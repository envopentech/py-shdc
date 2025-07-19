Quick Start Guide
=================

This guide will help you get up and running with the SHDC Python library quickly.

Overview
--------

The Smart Home Device Communications (SHDC) protocol defines secure communication
between sensors and hubs in a smart home network. The library provides both
programmatic APIs and command-line tools.

Basic Concepts
--------------

Hub
~~~
A hub is the central coordinator that manages sensors and handles communication
routing. Each network has one active hub.

Sensor
~~~~~~
Sensors are devices that collect and transmit data to the hub. They can be
temperature sensors, motion detectors, door sensors, etc.

Device ID
~~~~~~~~~
Each device has a unique 32-bit identifier used for addressing and authentication.

Using the CLI Tools
-------------------

The easiest way to get started is using the command-line tools.

Starting a Hub
~~~~~~~~~~~~~~

.. code-block:: bash

   # Start a hub with device ID 0x12345678
   shdc-hub run 0x12345678

   # Start with debug logging
   shdc-hub run 0x12345678 --debug

   # Bind to a specific network interface
   shdc-hub run 0x12345678 --interface eth0

Starting a Sensor
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start a temperature sensor that auto-discovers hubs
   shdc-sensor run 0x87654321 temperature

   # Connect to a specific hub
   shdc-sensor run 0x87654321 humidity --hub 192.168.1.100:56700

   # Send custom data from a JSON file
   shdc-sensor run 0x87654321 motion --data sensor_data.json --interval 10

Discovering Hubs
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Discover available hubs on the network
   shdc-sensor discover

Programmatic Usage
------------------

For more control, you can use the Python API directly.

Basic Hub Example
~~~~~~~~~~~~~~~~~

.. code-block:: python

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
           print(f"Device joined: {device_info.device_id:08X}")
       
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

Basic Sensor Example
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

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

Configuration
-------------

Key Storage
~~~~~~~~~~~

Keys are automatically stored in ``~/.shdc/keys/{device_id}/`` with restrictive
permissions (600). Key files include:

* Device identity keys (Ed25519)
* Session keys (AES-256)
* Broadcast keys (AES-256)

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

* ``SHDC_KEY_PATH``: Override default key storage location
* ``SHDC_LOG_LEVEL``: Set logging level (DEBUG, INFO, WARNING, ERROR)
* ``SHDC_DEFAULT_PORT``: Override default UDP port (56700)

Testing Your Setup
------------------

Run the integration test to verify complete system functionality:

.. code-block:: bash

   python test_integration.py

This test validates:

* Hub and sensor startup
* Device discovery and joining
* Secure data transmission
* Control message exchange
* Key management operations
* Error handling scenarios

Next Steps
----------

* Read the :doc:`tutorial/index` for detailed examples
* Explore the :doc:`examples/index` for real-world applications
* Check the :doc:`api/shdc` for complete API reference
* Review the :doc:`protocol/overview` for protocol details
