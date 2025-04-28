![PyPI - Python Version](https://img.shields.io/pypi/pyversions/requests) [![GitHub issues](https://img.shields.io/github/issues/docdyhr/httpcheck)](https://github.com/docdyhr/httpcheck/issues)  ![GitHub repo size](https://img.shields.io/github/repo-size/docdyhr/httpcheck) ![GitHub](https://img.shields.io/github/license/docdyhr/httpcheck)

# Check Websites HTTP Status Codes with httpcheck

* Name: httpcheck
* Version: 1.3.0
* Programming language: Python 3
* Author: Thomas J. Dyhr
* Purpose: CLI tool to Check Website HTTP Status
* Release date: 29 April 2025

## usage: httpcheck [-h] [-t] [-q | -v | -c | -f] [--timeout TIMEOUT] [--retries RETRIES] [--workers WORKERS] [--file-summary] [--comment-style {hash,slash,both}] [--follow-redirects {always,never,http-only,https-only}] [--max-redirects MAX_REDIRECTS] [--show-redirect-timing] [--version] [site ...]

### positional arguments

  site           return http status codes for one or more websites

### optional arguments

  -h, --help     show this help message and exit
  -t, --tld      check if domain is in global list of TLDs
  -q, --quiet    only print errors
  -v, --verbose  increase output verbosity
  -c, --code     only print status code
  -f, --fast     fast check wtih threading
  --timeout TIMEOUT
                 set the timeout for each request
  --retries RETRIES
                 set the number of retries for each request
  --workers WORKERS
                 set the number of worker threads
  --file-summary
                 show summary of file parsing results (valid URLs, comments, etc.)
  --comment-style {hash,slash,both}
                 comment style to recognize: hash (#), slash (//), or both (default: both)
  --follow-redirects {always,never,http-only,https-only}
                 control redirect following behavior (default: always)
  --max-redirects MAX_REDIRECTS
                 maximum number of redirects to follow (default: 30)
  --show-redirect-timing
                 show detailed timing for each redirect in the chain
  --version      show program's version number and exit

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
* Advanced redirect tracking and control
  * Follow all redirects, none, or limit by protocol (HTTP/HTTPS)
  * Configure maximum number of redirects to follow
  * View detailed per-hop timing information in redirect chains
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

### file input examples

Create a domains file with comments and use it with httpcheck:

```
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

## history

checking one or more websites by constantly opening a browser seems a waste of time. Providing a cli tool that can be used in a bash shell, pipe or for scheduling tasks in cron, notifying the user, seems the way to go. The python requests library seems perfect for the job.

## todo

[TODO.md](https://github.com/docdyhr/httpcheck/blob/master/TODO.md)

## license

[MIT](https://github.com/docdyhr/httpcheck/blob/master/LICENSE)
