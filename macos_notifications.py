#!/usr/bin/env python3
"""
Native macOS Notification Center integration for HTTP Check
Provides richer notifications with actions, sounds, and proper integration
"""

import os
import logging
from enum import Enum
from typing import Callable

try:
    import objc
    from Foundation import (
        NSUserNotification, NSUserNotificationCenter,
        NSObject
    )
    from AppKit import NSImage, NSWorkspace
    PYOBJC_AVAILABLE = True
except ImportError:
    PYOBJC_AVAILABLE = False
    logging.warning("PyObjC not available, falling back to basic "
                    "notifications")


class NotificationSound(Enum):
    """Available notification sounds"""
    DEFAULT = "NSUserNotificationDefaultSoundName"
    BASSO = "Basso"
    BLOW = "Blow"
    BOTTLE = "Bottle"
    FROG = "Frog"
    FUNK = "Funk"
    GLASS = "Glass"
    HERO = "Hero"
    MORSE = "Morse"
    PING = "Ping"
    POP = "Pop"
    PURR = "Purr"
    SOSUMI = "Sosumi"
    SUBMARINE = "Submarine"
    TINK = "Tink"


class NotificationDelegate(NSObject):
    """Delegate to handle notification interactions"""

    def init(self):
        """Initialize the delegate"""
        self = objc.super(NotificationDelegate, self).init()
        if self is None:
            return None
        self.callbacks = {}
        return self

    def userNotificationCenter_didActivateNotification_(
            self, center, notification):
        """Handle notification activation (click)"""
        # pylint: disable=unused-argument,invalid-name
        identifier = notification.identifier()
        if identifier in self.callbacks:
            callback = self.callbacks[identifier]
            if callable(callback):
                callback(notification)

    def userNotificationCenter_shouldPresentNotification_(
            self, center, notification):
        """Always present notifications even when app is focused"""
        # pylint: disable=unused-argument,invalid-name
        return True

    def register_callback(self, identifier: str, callback: Callable):
        """Register a callback for a notification identifier"""
        self.callbacks[identifier] = callback


class MacOSNotificationManager:
    """Enhanced notification manager using native macOS APIs"""

    def __init__(self):
        self.available = PYOBJC_AVAILABLE
        if self.available:
            try:
                self.center = (
                    NSUserNotificationCenter
                    .defaultUserNotificationCenter())
                # Skip delegate for now to simplify
                self.delegate = None
            except Exception as exc:
                logging.error("Failed to initialize notification center: %s",
                              exc)
                self.available = False
                self.center = None
                self.delegate = None
        else:
            self.center = None
            self.delegate = None

    def send_notification(
        self,
        title: str,
        message: str,
        subtitle: str = None,
        sound: NotificationSound = NotificationSound.DEFAULT,
        action_button: str = None,
        other_button: str = None,
        identifier: str = None,
        callback: Callable = None,
        icon_path: str = None,
        url: str = None
    ) -> bool:
        """
        Send a rich notification to macOS Notification Center

        Args:
            title: Notification title
            message: Notification message
            subtitle: Optional subtitle
            sound: Notification sound (NotificationSound enum)
            action_button: Text for action button
            other_button: Text for secondary button
            identifier: Unique identifier for callback handling
            callback: Function to call when notification is clicked
            icon_path: Path to custom icon image
            url: URL to associate with notification

        Returns:
            bool: True if notification was sent successfully
        """
        # pylint: disable=unused-argument,too-many-arguments
        # pylint: disable=too-many-branches
        if not self.available:
            return self._fallback_notification(title, message)

        try:
            notification = NSUserNotification.alloc().init()
            notification.setTitle_(title)
            notification.setInformativeText_(message)

            if subtitle:
                notification.setSubtitle_(subtitle)

            # Set sound
            if sound != NotificationSound.DEFAULT:
                notification.setSoundName_(sound.value)
            else:
                notification.setSoundName_(
                    "NSUserNotificationDefaultSoundName")

            # Set buttons
            if action_button:
                notification.setActionButtonTitle_(action_button)
                notification.setHasActionButton_(True)

            if other_button:
                notification.setOtherButtonTitle_(other_button)

            # Set identifier (callback handling simplified)
            if identifier:
                notification.setIdentifier_(identifier)

            # Set custom icon
            if icon_path and os.path.exists(icon_path):
                image = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if image:
                    notification.setContentImage_(image)

            # Set URL for click handling
            if url:
                notification.setUserInfo_({"url": url})

            # Deliver notification
            if self.center:
                self.center.deliverNotification_(notification)
                return True

            return self._fallback_notification(title, message)

        except Exception as exc:
            logging.error("Error sending native notification: %s", exc)
            return self._fallback_notification(title, message)

    def _fallback_notification(self, title: str, message: str) -> bool:
        """Fallback to osascript if PyObjC is not available"""
        try:
            # Escape quotes in title and message
            title = title.replace('"', '\\"')
            message = message.replace('"', '\\"')

            cmd = (f'osascript -e \'display notification "{message}" '
                   f'with title "{title}\'')
            os.system(cmd)
            return True
        except Exception as exc:
            logging.error("Error sending fallback notification: %s", exc)
            return False

    def send_site_down_alert(self, site: str, status_code: int,
                             callback: Callable = None):
        """Send a notification for a site being down"""
        return self.send_notification(
            title="🔴 Site Down",
            message=f"{site} is unreachable",
            subtitle=f"Status code: {status_code}",
            sound=NotificationSound.BASSO,
            action_button="Check Now",
            other_button="Dismiss",
            identifier=f"down_{site}",
            callback=callback,
            url=site
        )

    def send_site_recovery_alert(self, site: str, status_code: int,
                                 callback: Callable = None):
        """Send a notification for a site recovering"""
        return self.send_notification(
            title="🟢 Site Recovered",
            message=f"{site} is back online",
            subtitle=f"Status code: {status_code}",
            sound=NotificationSound.GLASS,
            action_button="View",
            identifier=f"recovery_{site}",
            callback=callback,
            url=site
        )

    def send_check_complete_summary(self, total: int, failed: int,
                                    callback: Callable = None):
        """Send a summary notification after checking all sites"""
        if failed == 0:
            title = "✅ All Sites OK"
            message = f"Checked {total} sites, all are healthy"
            sound = NotificationSound.PURR
        else:
            title = "⚠️ Sites Have Issues"
            message = f"{failed} of {total} sites are down"
            sound = NotificationSound.SOSUMI

        return self.send_notification(
            title=title,
            message=message,
            sound=sound,
            action_button="View Details" if failed > 0 else None,
            identifier="check_complete",
            callback=callback
        )

    def send_error_notification(self, error_msg: str, site: str = None):
        """Send an error notification"""
        title = "HTTP Check Error"
        message = error_msg
        if site:
            message = f"Error checking {site}: {error_msg}"

        return self.send_notification(
            title=title,
            message=message,
            sound=NotificationSound.FUNK,
            action_button="View Logs",
            identifier="error",
        )

    def clear_all_notifications(self):
        """Clear all delivered notifications"""
        if self.available and self.center:
            self.center.removeAllDeliveredNotifications()

    def clear_notifications_with_identifier(self, identifier: str):
        """Clear notifications with specific identifier"""
        if not self.available or not self.center:
            return

        delivered = self.center.deliveredNotifications()
        for notification in delivered:
            if notification.identifier() == identifier:
                self.center.removeDeliveredNotification_(notification)


def open_url_callback(notification):
    """Default callback to open URLs when notifications are clicked"""
    try:
        user_info = notification.userInfo()
        if user_info and "url" in user_info:
            url = user_info["url"]
            workspace = NSWorkspace.sharedWorkspace()
            workspace.openURL_(url)
    except Exception as exc:
        logging.error("Error opening URL from notification: %s", exc)


# Example usage and testing
if __name__ == "__main__":
    manager = MacOSNotificationManager()

    # Test basic notification
    manager.send_notification(
        title="HTTP Check Test",
        message="Testing native macOS notifications",
        sound=NotificationSound.PING
    )

    # Test site down notification
    manager.send_site_down_alert(
        site="example.com",
        status_code=500,
        callback=open_url_callback
    )

    # Test recovery notification
    manager.send_site_recovery_alert(
        site="example.com",
        status_code=200,
        callback=open_url_callback
    )

    # Test summary notification
    manager.send_check_complete_summary(
        total=10,
        failed=2
    )
