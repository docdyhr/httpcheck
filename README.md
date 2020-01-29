![PyPI - Python Version](https://img.shields.io/pypi/pyversions/requests) ![GitHub repo size](https://img.shields.io/github/repo-size/docdyhr/httpcheck) ![GitHub](https://img.shields.io/github/license/docdyhr/httpcheck)

# Check Websites HTTP Status Codes with httpcheck
* Name: httpcheck
* Version: 1.0
* Programming language: Python 3
* Author: Thomas J. Dyhr
* Purpose: CLI tool to Check Website HTTP Status
* Release date: 28. Jan 2020
### usage: httpcheck [-h] [--version] [-q | -v | -c] [site [site ...]]
### positional arguments:
  site           return http status codes for one or more websites
### optional arguments:
  -h, --help     show this help message and exit.  
  --version      show program's version number and exit.  
  -q, --quiet    only print errors.   
  -v, --verbose  increase output verbosity.  
  -c, --code     only print status code.  
### additional information:
  enter sites in url or 'no' url form: 'httpcheck duckduckgo.com'  
  read sites from a file: 'httpcheck @domains.txt'. 

  [List of HTTP status codes](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)

### installation
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

### usage examples
```shell
python3 httpcheck.py https://duckduckgo.com
```
returns ex. 'duckduckgo.com 200'

#### python from venv
```shell
python httpcheck.py -v https://api.github.com/invalid
```
returns verbose output ex. '[-] api.github.com --> Client errors: 404 Not Found'

#### installed as binary 
```shell
httpcheck -q @domains.txt
```
only returs http status code errors ex. 'api.github.com 404'

```shell
httpcheck -c 1.1.1.1
```
returs status code only ex. '200'

### history
checking one or more websites by constantly opening a browser seems a waste of time. Providing a cli tool that can be used in a bash shell, pipe or for scheduling tasks in cron, notifying the user, seems the way to go.

### todo
[TODO.md](https://github.com/docdyhr/httpcheck/blob/master/TODO.md)
### license
[MIT](https://github.com/docdyhr/httpcheck/blob/master/LICENSE)
