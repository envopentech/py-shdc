SHDC Python Library Documentation
===================================

.. image:: https://img.shields.io/badge/version-1.0.0-blue.svg
   :alt: Version
   :target: https://github.com/envopentech/py-shdc

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :alt: Python Version
   :target: https://python.org

.. image:: https://img.shields.io/badge/license-LGPL--3.0-green.svg
   :alt: License
   :target: https://github.com/envopentech/py-shdc/blob/main/LICENSE

A comprehensive Python implementation of the Smart Home Device Communications (SHDC) protocol v1.0.
This library provides secure, efficient communication between smart home devices using Ed25519 digital
signatures and AES-256-GCM encryption over UDP.

Features
--------

* **Secure Communication**: Ed25519 digital signatures and AES-256-GCM encryption
* **Hub-Sensor Architecture**: Star topology with automatic device discovery
* **Key Management**: Automatic key generation, rotation, and secure storage
* **Network Transport**: UDP multicast/broadcast/unicast with asyncio support
* **CLI Tools**: Ready-to-use command-line tools for hubs and sensors
* **Example Applications**: Complete demonstrations of home monitoring systems

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install shdc

Running a Hub
~~~~~~~~~~~~~

.. code-block:: bash

   # Start a hub with device ID 0x12345678
   shdc-hub run 0x12345678

   # Start with debug logging on specific interface
   shdc-hub run 0x12345678 --interface eth0 --debug

Running a Sensor
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start a temperature sensor that auto-discovers hubs
   shdc-sensor run 0x87654321 temperature

   # Connect to a specific hub
   shdc-sensor run 0x87654321 humidity --hub 192.168.1.100:56700

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   tutorial/index
   examples/index
   cli/index

.. toctree::
   :maxdepth: 2
   :caption: Protocol Reference

   protocol/overview

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/shdc/index

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/setup

.. toctree::
   :maxdepth: 1
   :caption: Additional Information

   changelog
   license
   support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

