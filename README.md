![PyPI - Python Version](https://img.shields.io/pypi/pyversions/requests) [![GitHub issues](https://img.shields.io/github/issues/docdyhr/httpcheck)](https://github.com/docdyhr/httpcheck/issues)  ![GitHub repo size](https://img.shields.io/github/repo-size/docdyhr/httpcheck) ![GitHub](https://img.shields.io/github/license/docdyhr/httpcheck)

# Check Websites HTTP Status Codes with httpcheck

* Name: httpcheck
* Version: 1.3.0
* Programming language: Python 3
* Author: Thomas J. Dyhr
* Purpose: CLI tool to Check Website HTTP Status
* Release date: 27 April 2025

## usage: httpcheck [-h] [-t] [-q | -v | -c | -f] [--timeout TIMEOUT] [--retries RETRIES] [--workers WORKERS] [--version] [site ...]

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
* Redirect tracking and reporting
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

## history

checking one or more websites by constantly opening a browser seems a waste of time. Providing a cli tool that can be used in a bash shell, pipe or for scheduling tasks in cron, notifying the user, seems the way to go. The python requests library seems perfect for the job.

## todo

[TODO.md](https://github.com/docdyhr/httpcheck/blob/master/TODO.md)

## license

[MIT](https://github.com/docdyhr/httpcheck/blob/master/LICENSE)
