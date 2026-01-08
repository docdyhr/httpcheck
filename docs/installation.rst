Installation
============

Requirements
------------

* Python 3.9 or higher
* pip package manager

Basic Installation
------------------

Install httpcheck from PyPI:

.. code-block:: bash

   pip install httpcheck

Development Installation
------------------------

For development, clone the repository and install in editable mode:

.. code-block:: bash

   git clone https://github.com/docdyhr/httpcheck.git
   cd httpcheck
   pip install -e ".[dev]"

Optional Dependencies
---------------------

macOS Menu Bar App
~~~~~~~~~~~~~~~~~~

For macOS menu bar integration:

.. code-block:: bash

   pip install httpcheck[macos]

Development Tools
~~~~~~~~~~~~~~~~~

For running tests and development:

.. code-block:: bash

   pip install httpcheck[dev]

This includes:

* pytest - Testing framework
* pytest-cov - Coverage reporting
* pytest-mock - Mocking support
* pylint - Code quality checking
* mypy - Type checking

Verification
------------

Verify the installation:

.. code-block:: bash

   httpcheck --version

You should see output like:

.. code-block:: text

   httpcheck 1.4.1
