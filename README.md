[![CI/CD Pipeline](https://github.com/docdyhr/httpcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/docdyhr/httpcheck/actions/workflows/ci.yml)
[![Quick Pylint Check](https://github.com/docdyhr/httpcheck/actions/workflows/pylint.yml/badge.svg)](https://github.com/docdyhr/httpcheck/actions/workflows/pylint.yml)
[![CodeQL](https://github.com/docdyhr/httpcheck/actions/workflows/ci.yml/badge.svg?event=schedule)](https://github.com/docdyhr/httpcheck/security/code-scanning)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)
[![GitHub issues](https://img.shields.io/github/issues/docdyhr/httpcheck)](https://github.com/docdyhr/httpcheck/issues)
![GitHub repo size](https://img.shields.io/github/repo-size/docdyhr/httpcheck)
![GitHub](https://img.shields.io/github/license/docdyhr/httpcheck)

# Check Websites HTTP Status Codes with httpcheck

<img src="images/onSiteLogo.png" alt="onSite Logo" width="50%">

* Name: httpcheck (CLI) / onSite (Menu Bar App)
* Version: 1.3.0
* Programming language: Python 3
* Author: Thomas Juul Dyhr
* Purpose: CLI tool to Check Website HTTP Status + macOS Menu Bar App
* Release date: 29 April 2025

## usage:
httpcheck [-h] [-t] [--disable-tld-checks] [--tld-warning-only] [--update-tld-list] [--tld-cache-days TLD_CACHE_DAYS] [-q | -v | -c | -f] [--timeout TIMEOUT] [--retries RETRIES] [--workers WORKERS] [--file-summary] [--comment-style {hash,slash,both}] [--follow-redirects {always,never,http-only,https-only}] [--max-redirects MAX_REDIRECTS] [--show-redirect-timing] [--version] [site ...]

### positional arguments

  site                   return http status codes for one or more websites

### optional arguments

  -h, --help             show this help message and exit
  -t, --tld              check if domain is in global list of TLDs
  --disable-tld-checks   disable TLD validation checks
  --tld-warning-only     show warnings for invalid TLDs without failing
  --update-tld-list      force update of the TLD list from publicsuffix.org
  --tld-cache-days TLD_CACHE_DAYS
                         number of days to keep the TLD cache valid (default: 30)
  -q, --quiet            only print errors
  -v, --verbose          increase output verbosity
  -c, --code             only print status code
  -f, --fast             fast check wtih threading
  --timeout TIMEOUT      set the timeout for each request
  --retries RETRIES      set the number of retries for each request
  --workers WORKERS      set the number of worker threads
  --file-summary         show summary of file parsing results (valid URLs, comments, etc.)
  --comment-style {hash,slash,both}
                         comment style to recognize: hash (#), slash (//), or both (default: both)
  --follow-redirects {always,never,http-only,https-only}
                         control redirect following behavior (default: always)
  --max-redirects MAX_REDIRECTS
                         maximum number of redirects to follow (default: 30)
  --show-redirect-timing show detailed timing for each redirect in the chain
  --version              show program's version number and exit

### additional information

  enter sites in url or 'no' url form: 'httpcheck duckduckgo.com'
  read sites from a file: 'httpcheck @domains.txt'.

  [List of HTTP status codes](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)

## installation

clone repo and install requirements.

### clone the repository

```shell
git clone https://github.com/docdyhr/httpcheck
cd httpcheck/
```

### install requirements

```shell
python3 -m pip install -r requirements.txt --user
```

On macOS, install terminal-notifier for notifications:

```shell
brew install terminal-notifier
```

### alternative install

set up a virtual environment with venv.

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

or

```shell
mv httpcheck.py ~/bin/httpcheck # any other bin folder
chmod + ~/bin/httpcheck
```

## features

* Check HTTP status codes for one or more websites
* Support for macOS notifications on failures
* **NEW: Menu bar app for continuous monitoring**
  * Live status indicator in menu bar (🟢/🔴)
  * Background checking with configurable intervals
  * Rich native macOS notifications with actions
  * Click notifications to open failing sites
  * Easy site management through menu interface
* Advanced redirect tracking and control
  * Follow all redirects, none, or limit by protocol (HTTP/HTTPS)
  * Configure maximum number of redirects to follow
  * View detailed per-hop timing information in redirect chains
* Enhanced TLD validation
  * Caches TLD list for better performance
  * Auto-updates from Public Suffix List
  * Configurable cache duration
  * Optional warning-only mode
* Enhanced file input handling
  * Support for comments using # or // style
  * Handles inline comments
  * Automatically strips whitespace
  * Detailed file parsing statistics
* Threading support for faster checks
* Progress bar for multiple site checks
* Configurable timeouts and retries
* Pipe and file input support

## usage examples

```shell
python3 httpcheck.py https://duckduckgo.com
```

returns ex. 'duckduckgo.com 200'

### python from venv

```shell
python httpcheck.py -v https://api.github.com/invalid
```

returns verbose output ex. '[-] api.github.com --> Client errors: 404 Not Found'

### installed as binary

```shell
httpcheck -q @domains.txt
```

only returns http status code errors ex. 'api.github.com 404'

```shell
httpcheck -c 1.1.1.1
```

status code only ex. '200'

### notifications

On macOS, the tool will show notifications when sites fail checks. For sites with failures:

* Shows failure count
* Lists failed sites (when less than 10)
* Groups notifications to avoid duplicates

### advanced usage examples

Control redirect behavior:

```shell
# Don't follow any redirects
httpcheck --follow-redirects never example.com

# Only follow redirects to HTTP URLs (not HTTPS)
httpcheck --follow-redirects http-only example.com

# Only follow redirects to HTTPS URLs (not HTTP)
httpcheck --follow-redirects https-only example.com

# Limit redirect chain length
httpcheck --max-redirects 5 example.com

# Show timing for each redirect hop
httpcheck -v --show-redirect-timing example.com
```

### tld validation examples

Control TLD validation behavior:

```shell
# Enable TLD validation
httpcheck -t example.com

# Force update of the TLD list from Public Suffix List
httpcheck -t --update-tld-list example.com

# Warn about invalid TLDs but don't fail
httpcheck -t --tld-warning-only example.com

# Disable TLD checks completely
httpcheck --disable-tld-checks example.com

# Set cache expiration to 60 days
httpcheck -t --tld-cache-days 60 example.com
```

### file input examples

Create a domains file with comments and use it with httpcheck:

```txt
# domains.txt - Example domains file
google.com  # Search engine
facebook.com // Social media
twitter.com
// Commented out: example.com
```

```shell
# Basic file usage
httpcheck @domains.txt

# Show file parsing statistics
httpcheck --file-summary @domains.txt

# Only recognize # style comments
httpcheck --comment-style hash @domains.txt

# Only recognize // style comments
httpcheck --comment-style slash @domains.txt
```

## onSite - menu bar app (macOS)

For continuous monitoring with a native macOS experience, use onSite - the menu bar app:

### installation

```shell
# Install additional dependencies for menu bar app
pip install rumps pyobjc-framework-Cocoa py2app

# Run the menu bar app directly
python3 httpcheck_menubar.py
```

### building a standalone app

Create a native macOS app bundle:

```shell
# Build the app (creates dist/onSite.app)
python setup.py py2app

# Copy to Applications folder
cp -r "dist/onSite.app" /Applications/

# Run from Applications or Spotlight
open "/Applications/onSite.app"
```

### menu bar app features

* **Live Status Indicator**: Menu bar shows ⚡ (white lightning - all good/checking), 🔴⚡ (red + lightning - failures)
* **Badge Count**: Shows number of failed sites next to the icon
* **Rich Notifications**: Native macOS notifications with:
  * Site down alerts with status codes
  * Recovery notifications when sites come back online
  * Click actions to open failing sites in browser
  * Custom sounds for different alert types
* **Background Monitoring**: Configurable check intervals (default 15 minutes, minimum 60 seconds)
* **Site Management**: Add, remove, and edit monitored sites through menu
* **Settings**: Configure check intervals, clear failed sites, view logs
* **Configuration Storage**: Sites and settings saved to `~/.httpcheck/`

### menu bar app usage

1. **Add Sites**: Click menu bar icon → "Add Site..." → Enter URL (automatically checks status)
2. **Manual Check**: Click "Check Now" for immediate status check
3. **Auto-Check**: Toggle automatic background checking on/off (default: 15 minutes)
4. **View Status**: Click on menu to see all sites with status indicators
5. **Settings**: Adjust check interval, clear failed sites, view logs

### keyboard shortcuts and tips

* Menu bar shows white lightning ⚡ for normal status, red lightning 🔴⚡ for failures
* Failed site count appears as badge number
* Notifications include action buttons (Check Now, View, Dismiss)
* Clicking notifications opens the failing site in your default browser
* Logs are stored in `~/Library/Logs/onSite/onsite.log` following macOS best practices
* Log rotation: 5MB max size, 5 backup files maintained automatically
* Logs viewable through Console.app or "View logs" menu item
* Configuration files stored in `~/.httpcheck/` for easy backup

## history

checking one or more websites by constantly opening a browser seems a waste of time. Providing a cli tool that can be used in a bash shell, pipe or for scheduling tasks in cron, notifying the user, seems the way to go. The python requests library seems perfect for the job.

## todo

[TODO.md](https://github.com/docdyhr/httpcheck/blob/master/TODO.md)

## license

[MIT](https://github.com/docdyhr/httpcheck/blob/master/LICENSE)
