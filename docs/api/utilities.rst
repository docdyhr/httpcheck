Utility Modules
===============

file_handler
------------

.. automodule:: httpcheck.file_handler
   :members:
   :undoc-members:
   :show-inheritance:

FileInputHandler
~~~~~~~~~~~~~~~~

.. autoclass:: httpcheck.file_handler.FileInputHandler
   :members:
   :special-members: __init__

Validation Functions
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: httpcheck.file_handler.url_validation

output_formatter
----------------

.. automodule:: httpcheck.output_formatter
   :members:
   :undoc-members:
   :show-inheritance:

Formatting Functions
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: httpcheck.output_formatter.print_format

.. autofunction:: httpcheck.output_formatter.format_json_list

.. autofunction:: httpcheck.output_formatter.format_csv_list

tld_manager
-----------

.. automodule:: httpcheck.tld_manager
   :members:
   :undoc-members:
   :show-inheritance:

TLDManager
~~~~~~~~~~

.. autoclass:: httpcheck.tld_manager.TLDManager
   :members:
   :special-members: __init__

validation
----------

.. automodule:: httpcheck.validation
   :members:
   :undoc-members:
   :show-inheritance:

Security Validation
~~~~~~~~~~~~~~~~~~~

.. autofunction:: httpcheck.validation.validate_url_security

.. autofunction:: httpcheck.validation.validate_file_path_security

.. autofunction:: httpcheck.validation.validate_header_security

Input Validation
~~~~~~~~~~~~~~~~

.. autofunction:: httpcheck.validation.validate_domain

.. autofunction:: httpcheck.validation.validate_url_format

.. autofunction:: httpcheck.validation.sanitize_url

notification
------------

.. automodule:: httpcheck.notification
   :members:
   :undoc-members:
   :show-inheritance:

Notification Functions
~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: httpcheck.notification.notify
