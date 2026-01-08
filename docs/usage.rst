Usage Guide
===========

This comprehensive guide covers all httpcheck features and options.

Command Line Interface
----------------------

Basic Syntax
~~~~~~~~~~~~

.. code-block:: bash

   httpcheck [OPTIONS] [SITE ...]

Site Arguments
~~~~~~~~~~~~~~

You can specify sites in multiple ways:

1. **Direct URLs**:

   .. code-block:: bash

      httpcheck google.com github.com

2. **From file** (using @ prefix):

   .. code-block:: bash

      httpcheck @domains.txt

3. **From stdin**:

   .. code-block:: bash

      cat domains.txt | httpcheck

Options Reference
-----------------

TLD Validation
~~~~~~~~~~~~~~

``-t, --tld``
  Check if domain is in global list of TLDs

``--disable-tld-checks``
  Disable TLD validation checks

``--tld-warning-only``
  Show warnings for invalid TLDs without failing

``--update-tld-list``
  Force update of the TLD list from publicsuffix.org

``--tld-cache-days N``
  Number of days to keep the TLD cache valid (default: 30)

Request Options
~~~~~~~~~~~~~~~

``--timeout SECONDS``
  Timeout in seconds for each request (default: 5.0)

``--retries N``
  Number of retries for failed requests (default: 2)

``--retry-delay SECONDS``
  Delay in seconds between retry attempts (default: 1.0)

``--workers N``
  Number of concurrent workers for fast mode (default: 10)

File Input
~~~~~~~~~~

``--file-summary``
  Show summary of file parsing results

``--comment-style {hash,slash,both}``
  Comment style to recognize (default: both)

Redirect Handling
~~~~~~~~~~~~~~~~~

``--follow-redirects {always,never,http-only,https-only}``
  Control redirect following behavior (default: always)

``--max-redirects N``
  Maximum number of redirects to follow (default: 30)

``--show-redirect-timing``
  Show timing information for each redirect step

Request Customization
~~~~~~~~~~~~~~~~~~~~~

``-H HEADER, --header HEADER``
  Add custom HTTP header (can be used multiple times)

``--no-verify-ssl``
  Disable SSL certificate verification

Output Options
~~~~~~~~~~~~~~

``-q, --quiet``
  Only print errors

``-v, --verbose``
  Increase output verbosity

``-c, --code``
  Only print status code

``-f, --fast``
  Fast check with threading

``--output {table,json,csv}``
  Output format (default: table)

Logging Options
~~~~~~~~~~~~~~~

``--debug``
  Enable debug logging

``--log-file FILE``
  Write logs to file

``--log-json``
  Output logs in JSON format

Examples
--------

Basic Checks
~~~~~~~~~~~~

Check a single site:

.. code-block:: bash

   httpcheck example.com

Check multiple sites:

.. code-block:: bash

   httpcheck google.com github.com reddit.com

Check sites from a file:

.. code-block:: bash

   httpcheck @domains.txt

Fast Mode
~~~~~~~~~

Use threading for faster checks:

.. code-block:: bash

   httpcheck -f @large-list.txt

Customize worker count:

.. code-block:: bash

   httpcheck -f --workers 20 @sites.txt

Output Formats
~~~~~~~~~~~~~~

JSON output:

.. code-block:: bash

   httpcheck --output json google.com > results.json

CSV output:

.. code-block:: bash

   httpcheck --output csv @sites.txt > results.csv

Quiet mode (errors only):

.. code-block:: bash

   httpcheck -q @sites.txt

Code only:

.. code-block:: bash

   httpcheck -c google.com
   # Output: 200

Custom Headers
~~~~~~~~~~~~~~

Single header:

.. code-block:: bash

   httpcheck -H "User-Agent: MyBot/1.0" example.com

Multiple headers:

.. code-block:: bash

   httpcheck \
     -H "User-Agent: MyBot/1.0" \
     -H "Accept: application/json" \
     -H "Authorization: Bearer token123" \
     api.example.com

Redirect Control
~~~~~~~~~~~~~~~~

Never follow redirects:

.. code-block:: bash

   httpcheck --follow-redirects never example.com

Only follow HTTP redirects:

.. code-block:: bash

   httpcheck --follow-redirects http-only example.com

Show redirect timing:

.. code-block:: bash

   httpcheck --show-redirect-timing google.com

Logging
~~~~~~~

Debug mode:

.. code-block:: bash

   httpcheck --debug example.com

Log to file:

.. code-block:: bash

   httpcheck --log-file /var/log/httpcheck.log @sites.txt

JSON logging for ELK/Splunk:

.. code-block:: bash

   httpcheck --log-json --debug --log-file httpcheck.json @sites.txt

TLD Validation
~~~~~~~~~~~~~~

Validate TLDs:

.. code-block:: bash

   httpcheck -t example.com example.invalidtld

Update TLD list:

.. code-block:: bash

   httpcheck --update-tld-list google.com

File Input Format
-----------------

The file input format supports comments and blank lines:

.. code-block:: text

   # Production sites
   https://example.com
   https://api.example.com

   // Staging environment
   https://staging.example.com

   # Third-party services
   https://cdn.example.com

Advanced Usage
--------------

Monitoring Cron Job
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # /etc/cron.d/httpcheck

   0 * * * * /usr/local/bin/httpcheck \
     --log-file /var/log/httpcheck.log \
     --log-json \
     -f @/etc/httpcheck/sites.txt

CI/CD Integration
~~~~~~~~~~~~~~~~~

GitHub Actions example:

.. code-block:: yaml

   - name: Check site availability
     run: |
       pip install httpcheck
       httpcheck --output json google.com > results.json

   - name: Upload results
     uses: actions/upload-artifact@v2
     with:
       name: http-check-results
       path: results.json

Docker Usage
~~~~~~~~~~~~

.. code-block:: dockerfile

   FROM python:3.12-slim
   RUN pip install httpcheck
   COPY domains.txt /app/
   CMD ["httpcheck", "-f", "@/app/domains.txt"]
