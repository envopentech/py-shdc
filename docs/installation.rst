Installation
============

Requirements
------------

* Python 3.8 or higher
* cryptography >= 41.0.0
* pynacl >= 1.5.0

Install from PyPI
-----------------

The recommended way to install the SHDC Python library is using pip:

.. code-block:: bash

   pip install shdc

Install from Source
-------------------

For development or to get the latest features, you can install from source:

.. code-block:: bash

   git clone https://github.com/envopentech/py-shdc.git
   cd py-shdc
   pip install -e .

Development Installation
------------------------

To install for development with all testing and documentation dependencies:

.. code-block:: bash

   git clone https://github.com/envopentech/py-shdc.git
   cd py-shdc
   pip install -e ".[dev]"

Virtual Environment
-------------------

It's recommended to use a virtual environment to avoid conflicts:

.. code-block:: bash

   python -m venv shdc-env
   source shdc-env/bin/activate  # On Windows: shdc-env\Scripts\activate
   pip install shdc

Verify Installation
-------------------

To verify the installation, you can check the version:

.. code-block:: bash

   python -c "import shdc; print(shdc.__version__)"

Or run the basic functionality test:

.. code-block:: bash

   python -c "from shdc import SHDCProtocol; print('SHDC library installed successfully')"

System Dependencies
-------------------

The library requires the following system-level cryptographic libraries:

Linux (Ubuntu/Debian)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install libsodium-dev libffi-dev

Linux (CentOS/RHEL/Fedora)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   sudo yum install libsodium-devel libffi-devel

macOS
~~~~~

.. code-block:: bash

   brew install libsodium

Windows
~~~~~~~

No additional system dependencies are required on Windows. The necessary
libraries are included with the Python package wheels.

Troubleshooting
---------------

ImportError: No module named 'nacl'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This usually indicates that PyNaCl failed to install. Try:

.. code-block:: bash

   pip install --upgrade pip
   pip install pynacl

Permission Errors
~~~~~~~~~~~~~~~~~

If you encounter permission errors during installation:

.. code-block:: bash

   pip install --user shdc

Or use a virtual environment as described above.

Network Issues
~~~~~~~~~~~~~~

If you have network connectivity issues, you can try using a different index:

.. code-block:: bash

   pip install -i https://pypi.org/simple/ shdc
