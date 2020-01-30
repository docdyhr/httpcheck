## Todo list for httpcheck:
* implement advanced redirects check as an option
* validate @files for empty lines within argparse scope
* refactor to check domains against tlds - ex. https://github.com/barseghyanartur/tld/blob/master/src/tld/res/effective_tld_names.dat.txt
* implement a progress bar for larger number of site checks - ex.: tqdm https://github.com/tqdm/tqdm
* refactor to use 'from requests.exceptions import HTTPError' in requests err instead of custom check
* implement advanced option for setting timeout length
* option for set number of times to try if timeout errror
* figure out the correct use of pipe with | ie. 'httpcheck -' for piping into httpcheck, see FileType and Nargs within argparse - https://docs.python.org/3.8/library/argparse.html#nargs
* notification of user integration with email, message, popup, notification, phone, see terminal-notifier or just use osascript "display notification" for osx
