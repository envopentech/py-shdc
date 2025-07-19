Development Setup
=================

This guide covers setting up a development environment for the SHDC library.

Prerequisites
-------------

System Requirements
~~~~~~~~~~~~~~~~~~~

* Python 3.8 or higher
* Git
* A text editor or IDE (VS Code, PyCharm, etc.)

Operating System Specific
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Linux (Ubuntu/Debian)**

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install python3-dev python3-venv libsodium-dev libffi-dev

**macOS**

.. code-block:: bash

   brew install python libsodium

**Windows**

* Install Python from python.org
* Install Git from git-scm.com
* Install Visual Studio Build Tools for C++ compilation

Getting the Source Code
-----------------------

Clone the Repository
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/envopentech/py-shdc.git
   cd py-shdc

Development Installation
------------------------

Virtual Environment
~~~~~~~~~~~~~~~~~~~

Create and activate a virtual environment:

.. code-block:: bash

   python -m venv venv
   
   # On Linux/macOS
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate

Install Dependencies
~~~~~~~~~~~~~~~~~~~

Install the package in development mode with all dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

This installs:

* The SHDC library in editable mode
* All runtime dependencies
* Development tools (pytest, black, isort, mypy, etc.)
* Documentation tools (sphinx, sphinx-rtd-theme, etc.)

Project Structure
-----------------

Understanding the codebase organization:

.. code-block:: text

   py-shdc/
   ├── shdc/                    # Main package
   │   ├── core/               # Core protocol implementation
   │   │   ├── protocol.py     # Main protocol class
   │   │   └── messages.py     # Message types and structures
   │   ├── crypto/             # Cryptographic operations
   │   │   ├── encryption.py   # Ed25519 and AES-256-GCM
   │   │   └── keys.py         # Key management
   │   ├── network/            # Network transport
   │   │   ├── transport.py    # UDP transport layer
   │   │   └── discovery.py    # Hub discovery
   │   ├── cli/                # Command-line tools
   │   │   ├── hub.py          # Hub CLI
   │   │   └── sensor.py       # Sensor CLI
   │   └── utils/              # Utility functions
   ├── examples/               # Example applications
   ├── tests/                  # Test suite
   ├── docs/                   # Documentation source
   └── setup.py               # Package configuration

Development Workflow
--------------------

Code Style
~~~~~~~~~~

The project uses several tools to maintain code quality:

.. code-block:: bash

   # Format code
   black shdc/ tests/ examples/
   
   # Sort imports
   isort shdc/ tests/ examples/
   
   # Type checking
   mypy shdc/
   
   # Linting
   flake8 shdc/ tests/ examples/

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=shdc --cov-report=html
   
   # Run specific test file
   pytest tests/test_protocol.py
   
   # Run with verbose output
   pytest -v

Building Documentation
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docs/
   make html
   
   # Open the built documentation
   # On Linux/macOS
   open _build/html/index.html
   
   # On Windows
   start _build/html/index.html

Integration Testing
~~~~~~~~~~~~~~~~~~~

Test the complete system:

.. code-block:: bash

   # Run integration tests
   python test_integration.py
   
   # Test CLI tools
   python -m shdc.cli.hub run 0x12345678 &
   python -m shdc.cli.sensor discover

IDE Configuration
-----------------

VS Code
~~~~~~~

Recommended VS Code extensions:

* Python
* Pylance
* Python Docstring Generator
* GitLens
* REST Client (for API testing)

Add to your ``.vscode/settings.json``:

.. code-block:: json

   {
       "python.formatting.provider": "black",
       "python.linting.enabled": true,
       "python.linting.flake8Enabled": true,
       "python.linting.mypyEnabled": true,
       "python.testing.pytestEnabled": true,
       "editor.formatOnSave": true,
       "python.sortImports.args": ["--profile", "black"]
   }

PyCharm
~~~~~~~

Configure PyCharm for the project:

1. Open the project directory
2. Set the Python interpreter to your virtual environment
3. Enable pytest as the test runner
4. Configure Black as the code formatter
5. Enable mypy for type checking

Debugging
---------

Debug Configuration
~~~~~~~~~~~~~~~~~~~

For debugging SHDC applications:

.. code-block:: python

   import logging
   
   # Enable debug logging
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   # Get SHDC loggers
   shdc_logger = logging.getLogger('shdc')
   shdc_logger.setLevel(logging.DEBUG)

Network Debugging
~~~~~~~~~~~~~~~~~

Use network tools to debug communication:

.. code-block:: bash

   # Monitor UDP traffic
   sudo tcpdump -i any port 56700
   
   # Test network connectivity
   nc -u 192.168.1.100 56700

Common Issues
~~~~~~~~~~~~~

**Import Errors**

Make sure the package is installed in development mode:

.. code-block:: bash

   pip install -e .

**Cryptography Issues**

Install system dependencies for cryptographic libraries:

.. code-block:: bash

   # Linux
   sudo apt-get install libsodium-dev libffi-dev
   
   # macOS
   brew install libsodium

**Network Permission Issues**

On some systems, binding to low ports requires privileges:

.. code-block:: bash

   # Run with sudo (not recommended for development)
   sudo python your_script.py
   
   # Or use a high port for testing
   shdc-hub run 0x12345678 --port 56700

Performance Profiling
---------------------

Profile CPU Usage
~~~~~~~~~~~~~~~~

.. code-block:: python

   import cProfile
   import pstats
   
   # Profile your code
   profiler = cProfile.Profile()
   profiler.enable()
   
   # Your code here
   await protocol.start()
   
   profiler.disable()
   stats = pstats.Stats(profiler)
   stats.sort_stats('cumulative')
   stats.print_stats(20)

Memory Profiling
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install memory profiler
   pip install memory-profiler
   
   # Profile memory usage
   python -m memory_profiler your_script.py

Network Performance
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   import asyncio
   
   # Measure message latency
   start_time = time.time()
   await protocol.send_sensor_data(data)
   latency = time.time() - start_time
   print(f"Message latency: {latency:.3f}s")

Contributing Guidelines
----------------------

Before Contributing
~~~~~~~~~~~~~~~~~~~

1. Read the contributing guidelines
2. Check existing issues and pull requests
3. Set up your development environment
4. Run the test suite to ensure everything works

Development Process
~~~~~~~~~~~~~~~~~~

1. Create a feature branch from main
2. Make your changes
3. Add or update tests
4. Update documentation if needed
5. Run the full test suite
6. Submit a pull request

Code Review
~~~~~~~~~~~

All code changes go through review:

* Follow the existing code style
* Include comprehensive tests
* Update documentation
* Respond to reviewer feedback
* Ensure CI passes

Release Process
---------------

Version Numbering
~~~~~~~~~~~~~~~~~

The project follows semantic versioning:

* **Major** (X.0.0): Breaking changes
* **Minor** (0.X.0): New features, backward compatible
* **Patch** (0.0.X): Bug fixes, backward compatible

Creating a Release
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Update version in setup.py and __init__.py
   # Update CHANGELOG.md
   # Commit changes
   git commit -am "Release v1.1.0"
   git tag v1.1.0
   git push origin main --tags
   
   # Build and upload to PyPI
   python setup.py sdist bdist_wheel
   twine upload dist/*
