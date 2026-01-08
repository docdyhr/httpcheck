CLI Module
==========

.. automodule:: httpcheck.cli
   :members:
   :undoc-members:
   :show-inheritance:

Main Entry Point
----------------

.. autofunction:: httpcheck.cli.main

Argument Parsing
----------------

.. autofunction:: httpcheck.cli.get_arguments

.. autofunction:: httpcheck.cli._create_argument_parser

Site Processing
---------------

.. autofunction:: httpcheck.cli.check_sites_serial

.. autofunction:: httpcheck.cli.check_sites_parallel

.. autofunction:: httpcheck.cli.process_site_status

Input Processing
----------------

.. autofunction:: httpcheck.cli._process_file_input

.. autofunction:: httpcheck.cli._process_stdin_input

.. autofunction:: httpcheck.cli._validate_sites

TLD Validation
--------------

.. autofunction:: httpcheck.cli.check_tlds

Helper Functions
----------------

.. autofunction:: httpcheck.cli._print_verbose_header

.. autofunction:: httpcheck.cli._handle_stdin_input

.. autofunction:: httpcheck.cli._process_sites

.. autofunction:: httpcheck.cli._send_completion_notification
