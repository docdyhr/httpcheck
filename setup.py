#!/usr/bin/env python3
"""
Setup script for creating macOS app bundle using py2app
"""

from setuptools import setup

# Read version from httpcheck.py
version = "1.3.0"
try:
    with open("httpcheck.py") as f:
        for line in f:
            if line.startswith("VERSION = "):
                version = line.split("=")[1].strip().strip("\"'")
                break
except Exception:
    pass

APP = ["httpcheck_menubar.py"]
DATA_FILES = [
    ("", ["httpcheck.py"]),  # Include main httpcheck module
    ("", ["requirements.txt"]),
    ("", ["domains.txt"]),
    ("", ["README.md"]),
]

# Resources for the app bundle
RESOURCES = []

OPTIONS = {
    "argv_emulation": False,
    "iconfile": None,  # Add path to .icns file if you have one
    "plist": {
        "CFBundleName": "onSite",
        "CFBundleDisplayName": "onSite",
        "CFBundleIdentifier": "com.onsite.menubar",
        "CFBundleVersion": version,
        "CFBundleShortVersionString": version,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleExecutable": "onSite",
        "NSHumanReadableCopyright": (
            "Copyright © June 2025 Thomas Juul " "Dyhr. All rights reserved."
        ),
        "LSUIElement": True,  # Hide from dock (menu bar only app)
        "NSAppTransportSecurity": {
            "NSAllowsArbitraryLoads": True,  # Allow HTTP requests
        },
        # Show notifications as alerts
        "NSUserNotificationAlertStyle": "alert",
        "LSMinimumSystemVersion": "10.13",  # Minimum macOS version
    },
    "packages": [
        "rumps",
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        "Foundation",
        "AppKit",
        "CoreFoundation",
        "objc",
    ],
    "includes": [
        "httpcheck",
        "macos_notifications",
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "PIL",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
    ],
    "resources": RESOURCES,
    "optimize": 2,
    "compressed": True,
    "strip": True,
}

setup(
    name="onSite",
    version=version,
    description="Monitor HTTP endpoints from your macOS menu bar",
    author="Thomas Juul Dyhr",
    author_email="thomas@dyhr.com",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    install_requires=[
        "rumps>=0.4.0",
        "requests>=2.32.0",
        "pyobjc-framework-Cocoa>=10.0",
        "pyobjc-framework-Foundation>=10.0",
        "pyobjc-framework-AppKit>=10.0",
        "pyobjc-core>=10.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: MacOS X :: Cocoa",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
    ],
)

# Build instructions for users
if __name__ == "__main__":
    print(
        """
onSite - HTTP Site Monitor Setup
================================

To build the macOS app bundle:

1. Install dependencies:
   pip install py2app rumps pyobjc-framework-Cocoa

2. Build the app:
   python setup.py py2app

3. The app will be created in dist/onSite.app

4. To run in development mode:
   python setup.py py2app -A

5. To create a clean build:
   rm -rf build dist
   python setup.py py2app

Optional: Code signing (for distribution)
========================================

1. Sign the app:
   codesign --deep --force --verify --verbose --sign\
   "Developer ID Application: Your Name" "dist/onSite.app"

2. Create a disk image:
   hdiutil create -volname "onSite" -srcfolder "dist/onSite.app"\
   -ov -format UDZO "onSite.dmg"

3. Sign the disk image:
   codesign --sign "Developer ID Application: Your Name" "onSite.dmg"

4. Notarize with Apple (requires Apple Developer account):
   xcrun altool --notarize-app --primary-bundle-id "com.onsite.menubar"\
   --username "your@email.com" --password "@keychain:AC_PASSWORD"\
   --file "onSite.dmg"

Usage:
======
After building, you can:
- Copy the app to /Applications
- Double-click to run
- Configure sites through the menu bar icon
- The app will automatically start checking your sites

Dependencies included in bundle:
- rumps (menu bar framework)
- requests (HTTP client)
- PyObjC (macOS native APIs)
- All required Python standard library modules
    """
    )
