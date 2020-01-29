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
Clone repo and install requirements.
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
Set up a virtual environment with venv.
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
or 

```shell
mv httpcheck.py ~/bin/httpcheck # or another bin dir
chmod + ~/bin/httpcheck
```

### license
[MIT](https://github.com/docdyhr/httpcheck/blob/master/LICENSE)
