###Check Websites HTTP Status Codes with httpcheck

##Name: httpcheck 
##Version: 1.0
##Programming language: Python 3
##Author: Thomas Juul Dyhr - [thomas@dyhr.com](mailto:thomas@dyhr.com)
##Purpose: CLI tool to Check Website HTTP Status
##Release date: 17. Jan 2020


##usage: httpcheck [-h] [--version] [-q | -v | -c] [site [site ...]]
httpcheck.py: error: [-] Please specify a website or a file with sites to check, use --help for more info.
(.venv) ➜  monitor_sites python httpcheck.py --hel    
usage: httpcheck.py [-h] [--version] [-q | -v | -c] [site [site ...]]

##positional arguments:
  site           return http status codes for one or more websites

##optional arguments:
  -h, --help     show this help message and exit
  --version      show program's version number and exit
  -q, --quiet    only print errors
  -v, --verbose  increase output verbosity
  -c, --code     only print status code

##additional information:
  enter sites in url or 'no' url form: 'httpcheck duckduckgo.com'
  read sites from a file: 'httpcheck @domains.txt'

  [List of HTTP status codes](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)

##Installation



