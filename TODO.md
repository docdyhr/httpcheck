# Todo list for httpcheck

* implement advanced redirects check as an option
* validate @files for empty lines within argparse scope / strip domain files for blanklines and spaces before read
* Check domains against [tlds](https://github.com/barseghyanartur/tld/blob/master/src/tld/res/effective_tld_names.dat.txt)
* implement a progress bar for larger number of site checks - ex.: [tqdm](https://github.com/tqdm/tqdm)
* refactor to use 'from requests.exceptions import HTTPError' in requests err instead of custom check
* implement advanced option for setting timeout length
* option for set number of times to try if timeout errror
* figure out the correct use of pipe with | ie. 'httpcheck -' for piping into httpcheck, see FileType and Nargs within [argparse](https://docs.python.org/3.8/library/argparse.html#nargs)
* notification of user integration with email, message, popup, notification, phone, see terminal-notifier or just use osascript "display notification" for osx
* implement threading propperly to show info

## tld check refactoring

 `tld_check` should be modified to use the function `validators.domain()` from the python package `validators` that has built in support for domain name validation, including checking TLDs against a list of public suffixes maintained by Mozilla. 

```python
import validators
from urllib.parse import urlparse

def tld_check(url):
    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):  # if the URL does not have a scheme or netloc
        raise ValueError('Invalid URL')  
    domain = parsed.hostname
    try:
        validators.domain(domain)
        return True
    except validators.ValidationFailure:
        raise InvalidTLDException(f"[-] Domain not in global list of TLDs: '{url}'")
```
Use the function as follows:

```python
tld_check('https://www.example.com')  # returns True if URL is valid, otherwise raises an exception
```
This will check both for a valid domain and that its TLD exists in the Mozilla list of public suffixes. If either condition fails, it raises an exception.

Make sure to install `validators` python package with:
```sh
pip install validators
```
Might need to replace own implementation for the function `tld_check` if there's no specific reason why you have written this code, as it will be more efficient and accurate. This library does exactly what you asked for, including checking against public suffixes which is not possible with a simple regex or similar methods.