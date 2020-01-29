## Todo list for httpcheck:
* implement advanced redirects check as a option
* validate @files for empty lines
* refactor to check domains against tlds - ex. https://github.com/barseghyanartur/tld/blob/master/src/tld/res/effective_tld_names.dat.txt
* implement a progress bar for larger number of site checks - ex.: tqdm https://github.com/tqdm/tqdm
* refactor to use 'from requests.exceptions import HTTPError' in requests err
* implement advanced option for setting timeout length
* option for set number of times to try if timeout errror
* figure out the correct use of pipe with | ie. 'httpcheck -' for piping into httpcheck
