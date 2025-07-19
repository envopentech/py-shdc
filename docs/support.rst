Support
=======

Getting Help
------------

If you need help with the SHDC Python library, there are several resources available:

Documentation
~~~~~~~~~~~~~

* **API Documentation**: Complete reference for all classes and functions
* **Tutorial**: Step-by-step guides for common use cases
* **Examples**: Real-world implementations and code samples
* **Protocol Reference**: Detailed SHDC protocol specification

Community Support
~~~~~~~~~~~~~~~~~

GitHub Issues
^^^^^^^^^^^^^

For bug reports, feature requests, and questions:

* **Bug Reports**: https://github.com/envopentech/py-shdc/issues/new?template=bug_report.md
* **Feature Requests**: https://github.com/envopentech/py-shdc/issues/new?template=feature_request.md
* **Questions**: https://github.com/envopentech/py-shdc/discussions

When reporting issues, please include:

* Python version and operating system
* SHDC library version
* Minimal code example that reproduces the issue
* Error messages and stack traces
* Network configuration details (if relevant)

Email Support
^^^^^^^^^^^^^

For direct support inquiries:

* **General Questions**: argo@envopen.org
* **Security Issues**: security@envopen.org (GPG key available)
* **Commercial Support**: sales@envopen.org

Response Times
~~~~~~~~~~~~~~

* **GitHub Issues**: Usually within 24-48 hours
* **Security Issues**: Within 24 hours
* **Email Support**: Within 2-3 business days

Commercial Support
------------------

Professional Services
~~~~~~~~~~~~~~~~~~~~~

For organizations requiring professional support:

* **Implementation Consulting**: Help integrating SHDC into your products
* **Custom Development**: Extensions and modifications for specific needs
* **Training**: On-site or remote training for development teams
* **Priority Support**: Guaranteed response times and dedicated support

Support Packages
~~~~~~~~~~~~~~~~

**Basic Support**

* Email support during business hours
* Bug fix priority
* Access to private documentation

**Premium Support**

* 24/7 email and phone support
* Dedicated support engineer
* Custom feature development
* On-site consulting available

**Enterprise Support**

* Service level agreements (SLA)
* Multiple support channels
* Architectural review and optimization
* Custom training programs

Contact sales@envopen.org for commercial support pricing.

Frequently Asked Questions
--------------------------

Installation Issues
~~~~~~~~~~~~~~~~~~~

**Q: I get a "No module named 'nacl'" error**

A: This indicates PyNaCl failed to install. Try:

.. code-block:: bash

   pip install --upgrade pip
   pip install pynacl

**Q: Installation fails with cryptography errors**

A: Install system dependencies:

.. code-block:: bash

   # Linux
   sudo apt-get install libsodium-dev libffi-dev
   
   # macOS
   brew install libsodium

Network Configuration
~~~~~~~~~~~~~~~~~~~~~

**Q: Hub discovery doesn't work**

A: Check that:

* UDP port 56700 is not blocked by firewall
* Multicast is enabled on your network interface
* Devices are on the same network segment

**Q: Sensors can't connect to hub**

A: Verify:

* Hub is running and listening
* Network connectivity between devices
* Device IDs are unique
* No NAT/firewall blocking connections

Security Questions
~~~~~~~~~~~~~~~~~~

**Q: How secure is the SHDC protocol?**

A: SHDC uses industry-standard cryptography:

* Ed25519 signatures for authentication
* AES-256-GCM for encryption
* Secure key derivation and rotation
* Protection against replay attacks

**Q: Can I use SHDC over the internet?**

A: SHDC is designed for local networks. For internet use:

* Use VPN for network layer security
* Consider additional authentication mechanisms
* Implement proper firewall rules

Performance
~~~~~~~~~~~

**Q: How many sensors can one hub support?**

A: Recommended limits:

* < 100 sensors per hub
* < 10 messages/second per sensor
* Monitor network bandwidth and hub CPU usage

**Q: What's the typical latency?**

A: On local networks:

* Discovery: < 1 second
* Joining: < 5 seconds
* Data transmission: < 100ms

Development
~~~~~~~~~~~

**Q: How do I contribute to the project?**

A: See the :doc:`development/contributing` guide for details.

**Q: Can I use SHDC in commercial products?**

A: Yes, SHDC is licensed under LGPL v3.0, which allows commercial use.

Troubleshooting
---------------

Debug Mode
~~~~~~~~~~

Enable debug logging to diagnose issues:

.. code-block:: python

   import logging
   
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger('shdc')
   logger.setLevel(logging.DEBUG)

Common Error Messages
~~~~~~~~~~~~~~~~~~~~~

**"Transport error: Connection refused"**

* Hub is not running or not accessible
* Check network connectivity and firewall rules

**"Authentication failed"**

* Device keys may be corrupted or mismatched
* Try regenerating device keys

**"Message timeout"**

* Network congestion or high latency
* Increase timeout values in configuration

**"Invalid signature"**

* Clock synchronization issues between devices
* Corrupted message data or keys

Network Diagnostics
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test UDP connectivity
   nc -u hub_ip 56700
   
   # Monitor network traffic
   sudo tcpdump -i any port 56700
   
   # Check multicast membership
   netstat -g

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   import psutil
   
   # Monitor memory usage
   process = psutil.Process()
   memory_mb = process.memory_info().rss / 1024 / 1024
   print(f"Memory usage: {memory_mb:.1f} MB")
   
   # Monitor message latency
   start_time = time.time()
   await protocol.send_data(data)
   latency = time.time() - start_time
   print(f"Latency: {latency:.3f}s")

Security Best Practices
-----------------------

Device Security
~~~~~~~~~~~~~~~

* Use unique device IDs for each physical device
* Protect key storage with appropriate file permissions
* Implement secure boot and tamper detection for embedded devices
* Regular security updates and key rotation

Network Security
~~~~~~~~~~~~~~~~

* Isolate IoT devices on separate network segments
* Use firewall rules to restrict unnecessary traffic
* Monitor for unusual network activity
* Implement intrusion detection systems

Application Security
~~~~~~~~~~~~~~~~~~~~

* Validate all input data from sensors
* Implement rate limiting and anomaly detection
* Log security events for audit trails
* Regular security assessments and penetration testing

Reporting Security Issues
-------------------------

If you discover a security vulnerability in the SHDC library:

1. **Do not** create a public GitHub issue
2. Email security@envopen.org with details
3. Include proof of concept if available
4. Allow reasonable time for response and fixing

We follow responsible disclosure practices and will:

* Acknowledge receipt within 24 hours
* Provide initial assessment within 72 hours
* Work with you to understand and fix the issue
* Credit you in the security advisory (if desired)

Security Contact
~~~~~~~~~~~~~~~~

* **Email**: security@envopen.org
* **GPG Key**: Available at https://github.com/envopentech/py-shdc/security
* **Response Time**: Within 24 hours for security issues
