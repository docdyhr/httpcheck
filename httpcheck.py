#!/usr/bin/env python3
"""Simple command line program to check website status.

This script is maintained for backward compatibility.
The main CLI logic is now in httpcheck.cli module.

Author: Thomas Juul Dyhr thomas@dyhr.com
Purpose: Check one or more websites status
Version: 1.4.1
"""

# This file is now a thin wrapper for backward compatibility
# All CLI logic has been moved to httpcheck.cli module
from httpcheck.cli import main

if __name__ == "__main__":
    main()
