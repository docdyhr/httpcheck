Examples
========

This page provides real-world examples of using httpcheck.

Basic Examples
--------------

Example 1: Simple Health Check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check if your main site is up:

.. code-block:: bash

   httpcheck https://mysite.com

Example 2: Multiple Sites
~~~~~~~~~~~~~~~~~~~~~~~~~~

Check multiple related services:

.. code-block:: bash

   httpcheck \
     https://mysite.com \
     https://api.mysite.com \
     https://cdn.mysite.com

Example 3: Large Site List
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``sites.txt``:

.. code-block:: text

   # Main services
   https://example.com
   https://api.example.com
   https://cdn.example.com

   # Third-party dependencies
   https://analytics.google.com
   https://fonts.googleapis.com

Check all sites with threading:

.. code-block:: bash

   httpcheck -f @sites.txt

Monitoring Examples
-------------------

Example 4: Continuous Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitor sites every 5 minutes:

.. code-block:: bash

   #!/bin/bash
   # monitor.sh

   while true; do
     httpcheck \
       --log-file /var/log/httpcheck.log \
       --log-json \
       -f @sites.txt

     sleep 300
   done

Example 5: Cron Job with Alerts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # /etc/cron.hourly/check-sites

   LOG="/var/log/httpcheck-$(date +%Y%m%d).log"

   httpcheck -f @/etc/httpcheck/sites.txt \
     --log-file "$LOG" \
     --log-json \
     --debug

CI/CD Examples
--------------

Example 6: GitHub Actions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: Site Availability Check

   on:
     schedule:
       - cron: '0 */6 * * *'  # Every 6 hours
     workflow_dispatch:

   jobs:
     check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2

         - name: Install httpcheck
           run: pip install httpcheck

         - name: Check sites
           run: |
             httpcheck -f @sites.txt \
               --output json > results.json

         - name: Upload results
           uses: actions/upload-artifact@v2
           with:
             name: check-results
             path: results.json

Example 7: GitLab CI
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   site-check:
     image: python:3.12-slim
     script:
       - pip install httpcheck
       - httpcheck -f @sites.txt --output json
     artifacts:
       paths:
         - results.json
     only:
       - schedules

API Integration Examples
------------------------

Example 8: Python Script
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """Check sites and send alerts."""

   from httpcheck.site_checker import check_site
   from httpcheck.common import SiteStatus
   import smtplib
   from email.message import EmailMessage

   sites = [
       "https://example.com",
       "https://api.example.com",
       "https://cdn.example.com"
   ]

   failed_sites = []

   for site in sites:
       status = check_site(site, timeout=10.0, retries=3)

       if not isinstance(status, SiteStatus):
           failed_sites.append(site)
           continue

       try:
           code = int(status.status)
           if code >= 400:
               failed_sites.append(f"{site} ({code})")
       except ValueError:
           failed_sites.append(f"{site} (ERROR)")

   if failed_sites:
       # Send email alert
       msg = EmailMessage()
       msg['Subject'] = f'Site Check: {len(failed_sites)} sites down'
       msg['From'] = 'monitor@example.com'
       msg['To'] = 'admin@example.com'
       msg.set_content('\n'.join(failed_sites))

       with smtplib.SMTP('localhost') as s:
           s.send_message(msg)

Example 9: Data Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   #!/usr/bin/env python3
   """Collect site metrics to database."""

   import sqlite3
   from datetime import datetime
   from httpcheck.site_checker import check_site

   # Connect to database
   conn = sqlite3.connect('metrics.db')
   cursor = conn.cursor()

   cursor.execute('''
       CREATE TABLE IF NOT EXISTS checks (
           timestamp TEXT,
           site TEXT,
           status INTEGER,
           response_time REAL,
           final_url TEXT
       )
   ''')

   sites = ["google.com", "github.com", "reddit.com"]

   for site in sites:
       status = check_site(site)

       cursor.execute('''
           INSERT INTO checks VALUES (?, ?, ?, ?, ?)
       ''', (
           datetime.now().isoformat(),
           status.domain,
           status.status,
           status.response_time,
           status.final_url
       ))

   conn.commit()
   conn.close()

Docker Examples
---------------

Example 10: Docker Container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``Dockerfile``:

.. code-block:: dockerfile

   FROM python:3.12-slim

   RUN pip install httpcheck

   WORKDIR /app
   COPY sites.txt /app/

   CMD ["httpcheck", "-f", "--output", "json", "@sites.txt"]

Build and run:

.. code-block:: bash

   docker build -t httpcheck-monitor .
   docker run httpcheck-monitor

Example 11: Docker Compose
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``docker-compose.yml``:

.. code-block:: yaml

   version: '3'
   services:
     monitor:
       image: python:3.12-slim
       command: >
         sh -c "pip install httpcheck &&
                while true; do
                  httpcheck -f @/app/sites.txt --log-json;
                  sleep 300;
                done"
       volumes:
         - ./sites.txt:/app/sites.txt
         - ./logs:/var/log
       restart: unless-stopped

Kubernetes Example
------------------

Example 12: CronJob
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: site-checker
   spec:
     schedule: "*/15 * * * *"  # Every 15 minutes
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: httpcheck
               image: python:3.12-slim
               command:
                 - /bin/sh
                 - -c
                 - |
                   pip install httpcheck
                   httpcheck -f @/config/sites.txt \
                     --output json \
                     --log-json
               volumeMounts:
               - name: sites-config
                 mountPath: /config
             volumes:
             - name: sites-config
               configMap:
                 name: sites-list
             restartPolicy: OnFailure

Advanced Examples
-----------------

Example 13: Custom Headers for APIs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   httpcheck \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Accept: application/json" \
     -H "X-API-Version: v2" \
     https://api.example.com/health

Example 14: SSL Certificate Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # Check sites with strict SSL validation

   SITES="
   https://bank.com
   https://secure-portal.com
   https://payment-gateway.com
   "

   for site in $SITES; do
     echo "Checking $site..."
     httpcheck "$site" --timeout 10 --retries 1

     if [ $? -ne 0 ]; then
       echo "ALERT: $site failed SSL check!"
       # Send alert
     fi
   done

Example 15: Rate-Limited Checking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # Check sites with rate limiting

   while IFS= read -r site; do
     httpcheck "$site"
     sleep 1  # Rate limit: 1 request per second
   done < sites.txt
