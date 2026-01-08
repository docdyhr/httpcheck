Core Modules
============

site_checker
------------

.. automodule:: httpcheck.site_checker
   :members:
   :undoc-members:
   :show-inheritance:

common
------

.. automodule:: httpcheck.common
   :members:
   :undoc-members:
   :show-inheritance:

SiteStatus
~~~~~~~~~~

.. autoclass:: httpcheck.common.SiteStatus
   :members:

Constants
~~~~~~~~~

.. autodata:: httpcheck.common.VERSION

.. autodata:: httpcheck.common.DEFAULT_USER_AGENT

Exceptions
~~~~~~~~~~

.. autoexception:: httpcheck.common.InvalidTLDException
   :members:
   :show-inheritance:

logger
------

.. automodule:: httpcheck.logger
   :members:
   :undoc-members:
   :show-inheritance:

Logger Setup
~~~~~~~~~~~~

.. autofunction:: httpcheck.logger.setup_logger

.. autofunction:: httpcheck.logger.get_logger

.. autofunction:: httpcheck.logger.reset_logger

Convenience Functions
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: httpcheck.logger.debug

.. autofunction:: httpcheck.logger.info

.. autofunction:: httpcheck.logger.warning

.. autofunction:: httpcheck.logger.error

.. autofunction:: httpcheck.logger.critical
