#!/usr/bin/env python3
"""
Test script for the menu bar app functionality
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# pylint: disable=wrong-import-position
from macos_notifications import MacOSNotificationManager


def test_notifications():
    """Test the notification system"""
    print("Testing notification manager...")
    manager = MacOSNotificationManager()

    if manager.available:
        print("✅ PyObjC is available, testing native notifications...")

        # Test basic notification
        result = manager.send_notification(
            title="HTTP Check Test",
            message="Testing native macOS notifications",
            subtitle="This is a test",
        )
        print(f"Basic notification sent: {result}")

        # Test site down alert
        result = manager.send_site_down_alert(site="example.com", status_code=500)
        print(f"Site down alert sent: {result}")

    else:
        print("⚠️  PyObjC not available, testing fallback...")
        result = manager.send_notification(
            title="HTTP Check Test", message="Testing fallback notifications"
        )
        print(f"Fallback notification sent: {result}")


def test_httpcheck_import():
    """Test importing httpcheck functionality"""
    print("\nTesting httpcheck import...")
    try:
        import httpcheck

        print("✅ httpcheck module imported successfully")

        # Test creating a simple args object
        args = type(
            "Args",
            (),
            {
                "timeout": 10,
                "redirect": "always",
                "max_redirects": 10,
                "tld": False,
                "retry": 1,
                "verbose": False,
            },
        )()

        print("✅ Args object created successfully")

    except Exception as e:
        print(f"❌ Error importing httpcheck: {e}")


if __name__ == "__main__":
    print("🧪 Testing HTTP Check Menu Bar App Components\n")

    test_notifications()
    test_httpcheck_import()

    print("\n✅ All tests completed!")
    print("\nTo run the menu bar app:")
    print("python3 httpcheck_menubar.py")
    print("\nTo add test sites, you can:")
    print("1. Run the app and use 'Add Site...' menu")
    print("2. Or edit ~/.httpcheck/sites.json manually")
