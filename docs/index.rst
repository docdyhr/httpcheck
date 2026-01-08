httpcheck Documentation
=======================

**httpcheck** is a Python CLI tool for HTTP status code checking with advanced features including threading, redirect handling, TLD validation, and macOS integration.

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: black

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install httpcheck

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

   # Check single site
   httpcheck google.com

   # Check multiple sites from file
   httpcheck @domains.txt

   # Fast mode with threading
   httpcheck -f @domains.txt

   # JSON output
   httpcheck --output json google.com

   # Debug logging
   httpcheck --debug google.com

Features
--------

* **HTTP Status Checking**: Get HTTP status codes for one or more websites
* **Multiple Output Formats**: table (default), JSON, CSV
* **Threading Support**: Fast parallel checking with configurable workers
* **Redirect Handling**: Four modes (always, never, http-only, https-only)
* **TLD Validation**: Validates against global TLD list from publicsuffix.org
* **Custom Headers**: Add custom HTTP headers to requests
* **SSL Control**: Option to disable SSL certificate verification
* **Structured Logging**: Debug, file, and JSON logging support
* **File Input**: Read URLs from files with comment support
* **macOS Integration**: Menu bar app and notifications

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   usage
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/modules
   api/cli
   api/core
   api/utilities

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
