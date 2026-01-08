Quick Start
===========

This guide will get you started with httpcheck in minutes.

Basic Usage
-----------

Check a Single Site
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   httpcheck google.com

Output:

.. code-block:: text

   ----------  ---
   google.com  200
   ----------  ---

   Checked 1 sites in 0s
   1 successful, 0 failed

Check Multiple Sites
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   httpcheck google.com github.com reddit.com

Multiple Sites from File
~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file ``domains.txt``:

.. code-block:: text

   # My important sites
   google.com
   github.com
   reddit.com

Then check all sites:

.. code-block:: bash

   httpcheck @domains.txt

Fast Mode (Threading)
~~~~~~~~~~~~~~~~~~~~~

For checking many sites quickly:

.. code-block:: bash

   httpcheck -f @domains.txt

This uses threading to check sites in parallel.

Output Formats
--------------

JSON Output
~~~~~~~~~~~

.. code-block:: bash

   httpcheck --output json google.com

.. code-block:: json

   [
     {
       "domain": "google.com",
       "status": "200",
       "message": "OK",
       "response_time": 0.234,
       "final_url": "https://www.google.com/"
     }
   ]

CSV Output
~~~~~~~~~~

.. code-block:: bash

   httpcheck --output csv google.com github.com

.. code-block:: text

   domain,status,message,response_time,final_url
   google.com,200,OK,0.234,https://www.google.com/
   github.com,200,OK,0.456,https://github.com/

Logging
-------

Debug Mode
~~~~~~~~~~

Enable detailed debug logging:

.. code-block:: bash

   httpcheck --debug google.com

Log to File
~~~~~~~~~~~

Write logs to a file:

.. code-block:: bash

   httpcheck --log-file /var/log/httpcheck.log @domains.txt

JSON Logging
~~~~~~~~~~~~

For log aggregation systems (ELK, Splunk):

.. code-block:: bash

   httpcheck --log-json --debug google.com

Advanced Options
----------------

Custom Headers
~~~~~~~~~~~~~~

.. code-block:: bash

   httpcheck -H "User-Agent: MyBot/1.0" -H "Accept: application/json" google.com

Disable SSL Verification
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   httpcheck --no-verify-ssl https://self-signed-cert.example.com

Timeout and Retries
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   httpcheck --timeout 10 --retries 3 slow-site.com

Custom Workers
~~~~~~~~~~~~~~

.. code-block:: bash

   httpcheck -f --workers 20 @large-list.txt

Next Steps
----------

* See :doc:`usage` for complete documentation
* Check :doc:`examples` for more real-world scenarios
* Browse :doc:`api/modules` for programmatic usage
