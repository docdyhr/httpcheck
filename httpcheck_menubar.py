#!/usr/bin/env python3
"""
onSite - HTTP Site Monitoring for macOS
A lightweight menu bar application for monitoring HTTP endpoints
"""

import json
import logging
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Set, Optional
from urllib.parse import urlparse

import rumps

# Import core functionality from main httpcheck module
import httpcheck
from macos_notifications import MacOSNotificationManager


class HTTPCheckApp(rumps.App):
    """Menu bar application for HTTP status monitoring"""

    def __init__(self):
        super().__init__("onSite", title="⚡")

        # Initialize state
        self.sites: List[str] = []
        self.failed_sites: Set[str] = set()
        self.last_check_time: Optional[datetime] = None
        self.checking = False
        self.check_interval = 900  # 15 minutes default
        self.timer = None

        # Setup paths following macOS best practices
        self.config_dir = Path.home() / '.httpcheck'
        self.config_dir.mkdir(exist_ok=True)
        self.sites_file = self.config_dir / 'sites.json'
        self.config_file = self.config_dir / 'config.json'

        # Setup log directory following macOS best practices
        self.log_dir = Path.home() / 'Library' / 'Logs' / 'onSite'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / 'onsite.log'

        # Load configuration
        self.load_config()
        self.load_sites()

        # Setup logging following macOS best practices
        # Check for debug mode from config
        self.debug_mode = getattr(self, 'debug_mode', False)
        self.setup_logging()

        # Initialize native notifications
        self.notification_manager = MacOSNotificationManager()

        # Build initial menu
        self.build_menu()

        # Update icon based on initial state
        self.update_status_icon()

        # Start background checking
        if self.sites:
            self.start_background_checking()

    def validate_url(self, url: str) -> tuple[bool, str]:
        """
        Validate URL format and return (is_valid, error_message)

        Args:
            url: The URL string to validate

        Returns:
            tuple: (bool, str) - (is_valid, error_message)
        """
        if not url or not url.strip():
            return False, "URL cannot be empty"

        url = url.strip()

        # Check if URL is just the default placeholder
        if url in ("http://", "https://"):
            return False, "Please enter a complete URL"

        # Check if scheme is valid first
        if url.startswith(('ftp://', 'file://', 'mailto:')):
            return False, "URL must use http:// or https://"

        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        try:
            parsed = urlparse(url)

            # Check if scheme is valid
            if parsed.scheme not in ('http', 'https'):
                return False, "URL must use http:// or https://"

            # Check if domain exists
            if not parsed.netloc:
                return False, "URL must include a domain name"

            # Basic domain format validation
            domain_pattern = re.compile(
                r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
                r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
            )

            # Extract just the hostname (remove port if present)
            hostname = parsed.netloc.split(':')[0]

            # Check for valid domain format (allow localhost)
            if (not domain_pattern.match(hostname) and
                    not self._is_valid_ip(hostname) and
                    hostname.lower() != 'localhost'):
                return False, "Invalid domain name or IP address format"

            # Check for minimum domain requirements (allow localhost)
            if ('.' not in hostname and
                    not self._is_valid_ip(hostname) and
                    hostname.lower() != 'localhost'):
                return False, ("Domain name must contain at least one dot "
                               "(e.g., example.com)")

            # Check URL length (reasonable limit)
            if len(url) > 2048:
                return False, "URL is too long (maximum 2048 characters)"

            return True, url  # Return the normalized URL

        except Exception as exc:
            return False, f"Invalid URL format: {str(exc)}"

    def _is_valid_ip(self, hostname: str) -> bool:
        """Check if hostname is a valid IP address"""
        try:
            import ipaddress
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False

    def validate_and_add_site(self, url: str) -> tuple[bool, str]:
        """
        Validate URL and add to sites if valid

        Args:
            url: The URL to validate and add

        Returns:
            tuple: (success, message)
        """
        is_valid, result = self.validate_url(url)

        if not is_valid:
            return False, result  # result is error message

        # result is the normalized URL
        normalized_url = result

        # Check for duplicates
        if normalized_url in self.sites:
            return False, f"Site already exists: {normalized_url}"

        # Check if we're approaching a reasonable limit
        if len(self.sites) >= 50:
            return False, "Maximum number of sites reached (50 sites limit)"

        return True, normalized_url

    def setup_logging(self):
        """Setup logging following macOS best practices with DEBUG support"""
        try:
            # Clear any existing handlers to prevent duplicates
            logging.root.handlers = []

            # Determine log level based on debug mode
            log_level = logging.DEBUG if self.debug_mode else logging.INFO

            # Create file handler with rotation support
            try:
                from logging.handlers import RotatingFileHandler

                # Create rotating file handler (max 5MB, keep 5 backup files)
                file_handler = RotatingFileHandler(
                    self.log_file,
                    maxBytes=5 * 1024 * 1024,  # 5MB
                    backupCount=5,
                    encoding='utf-8'
                )

                # Create formatter following macOS conventions
                formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] onSite: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(formatter)

                # Configure root logger only
                logging.basicConfig(
                    handlers=[file_handler],
                    level=log_level,
                    format='%(asctime)s [%(levelname)s] onSite: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    force=True  # Force reconfiguration
                )

                # Log startup messages
                logging.info("onSite started successfully")
                if self.debug_mode:
                    logging.debug("Debug logging enabled")
                logging.info(f"Log file: {self.log_file}")
                logging.info(f"Config directory: {self.config_dir}")
                logging.debug(f"Log level: {logging.getLevelName(log_level)}")

            except ImportError:
                # Fallback to basic file handler if RotatingFileHandler
                # unavailable
                logging.basicConfig(
                    filename=self.log_file,
                    level=log_level,
                    format='%(asctime)s [%(levelname)s] onSite: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    encoding='utf-8',
                    force=True
                )
                logging.info("onSite started successfully (basic logging)")

        except Exception as exc:
            # Fallback to console logging if file logging fails
            print(f"Warning: Could not setup file logging: {exc}")
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s [%(levelname)s] onSite: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True
            )

    def build_menu(self):
        """Build the menu structure"""
        self.menu.clear()

        # Status section
        if self.last_check_time:
            time_str = self.last_check_time.strftime("%H:%M:%S")
            status = f"Last check: {time_str}"
        else:
            status = "Not checked yet"

        self.menu = [
            rumps.MenuItem(status, callback=None),
            rumps.separator,
        ]

        # Quick actions
        self.menu.add(rumps.MenuItem("Check Now", callback=self.check_now))
        auto_status = "ON" if self.timer else "OFF"
        self.menu.add(rumps.MenuItem(f"Auto-check: {auto_status}",
                                     callback=self.toggle_auto_check))
        self.menu.add(rumps.separator)

        # Sites section
        if self.sites:
            sites_menu = rumps.MenuItem("Sites")
            for site in self.sites:
                icon = "🔴" if site in self.failed_sites else "🟢"
                site_item = rumps.MenuItem(f"{icon} {site}")
                sites_menu.add(site_item)
            self.menu.add(sites_menu)
        else:
            self.menu.add(rumps.MenuItem("No sites configured", callback=None))

        self.menu.add(rumps.separator)

        # Configuration
        self.menu.add(rumps.MenuItem("Add Site...", callback=self.add_site))
        self.menu.add(rumps.MenuItem("Remove Site...",
                                     callback=self.remove_site))
        self.menu.add(rumps.MenuItem("Edit Sites...",
                                     callback=self.edit_sites))
        self.menu.add(rumps.separator)

        # Settings
        settings_menu = rumps.MenuItem("Settings")
        settings_menu.add(
            rumps.MenuItem(f"Check interval: {self.check_interval}s",
                           callback=self.change_interval))
        settings_menu.add(rumps.MenuItem("Clear failed sites",
                                         callback=self.clear_failed))
        settings_menu.add(rumps.MenuItem("View logs", callback=self.view_logs))
        self.menu.add(settings_menu)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("About", callback=self.about))
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    def update_status_icon(self):
        """Update the menu bar icon based on status"""
        if self.failed_sites:
            # Red lightning flash for failures
            try:
                # Try to create a red lightning icon using SF Symbols or
                # Unicode
                self.title = "⚡"
                # Don't use template mode for color control
                self.template = False

                # Try to set red color using NSColor if available
                try:
                    from AppKit import (NSColor, NSAttributedString,
                                        NSForegroundColorAttributeKey, NSFont)
                    from Foundation import NSMutableDictionary

                    # Create red attributed string
                    attrs = NSMutableDictionary.alloc().init()
                    attrs.setObject_forKey_(NSColor.redColor(),
                                            NSForegroundColorAttributeKey)
                    attrs.setObject_forKey_(NSFont.systemFontOfSize_(14),
                                            "NSFont")

                    attributed_title = (
                        NSAttributedString.alloc()
                        .initWithString_attributes_("⚡", attrs))
                    self.title = attributed_title
                except (ImportError, Exception):
                    # Fallback to red circle + lightning if NSColor
                    # doesn't work
                    self.title = "🔴⚡"

            except Exception:
                # Final fallback
                self.title = "🔴⚡"
        else:
            # White lightning flash for normal states
            # (default, checking, all good)
            self.title = "⚡"
            self.template = True  # Use template mode for white/system color

    @rumps.clicked("Check Now")
    def check_now(self, _):
        """Manually trigger a check of all sites"""
        if self.checking:
            self.notification_manager.send_notification(
                title="onSite",
                message="Check in progress",
                subtitle="Please wait..."
            )
            return

        if not self.sites:
            self.notification_manager.send_notification(
                title="onSite",
                message="No sites configured",
                subtitle="Add sites to monitor first"
            )
            return

        # Run check in background thread
        thread = threading.Thread(target=self.perform_check)
        thread.daemon = True
        thread.start()

    def perform_check(self, _=None):
        """Perform the actual HTTP checks"""
        self.checking = True
        self.update_status_icon()

        try:
            # Clear previous failed sites
            old_failed = self.failed_sites.copy()
            self.failed_sites.clear()

            total_sites = len(self.sites)

            for site in self.sites:
                try:
                    # Use the main httpcheck module's check_site function
                    result = self.check_single_site(site)

                    # Parse status code from result.status string
                    try:
                        status_code = int(result.status)
                    except ValueError:
                        # If status is not a number, treat as failure
                        status_code = 0

                    if status_code not in range(200, 400):
                        self.failed_sites.add(site)
                        logging.warning("Site failed: %s - Status: %s",
                                        site, result.status)

                        # Send notification for newly failed sites
                        if site not in old_failed:
                            self.notification_manager.send_site_down_alert(
                                site=site,
                                status_code=status_code,
                                callback=self.handle_notification_click
                            )
                    else:
                        # Site recovered
                        if site in old_failed:
                            self.notification_manager.send_site_recovery_alert(
                                site=site,
                                status_code=status_code,
                                callback=self.handle_notification_click
                            )

                except Exception as exc:
                    self.failed_sites.add(site)
                    logging.error("Error checking %s: %s", site, str(exc))

                    if site not in old_failed:
                        self.notification_manager.send_error_notification(
                            # Truncate long error messages
                            error_msg=str(exc)[:100],
                            site=site
                        )

            self.last_check_time = datetime.now()
            logging.info("Check completed: %s/%s sites failed",
                         len(self.failed_sites), total_sites)

            # Send summary notification
            self.notification_manager.send_check_complete_summary(
                total=total_sites,
                failed=len(self.failed_sites),
                callback=self.handle_notification_click
            )

        finally:
            self.checking = False
            self.update_status_icon()
            self.build_menu()

    def handle_notification_click(self, notification):
        """Handle clicks on notifications"""
        try:
            from AppKit import NSWorkspace
            user_info = notification.userInfo()
            if user_info and "url" in user_info:
                url = user_info["url"]
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                workspace = NSWorkspace.sharedWorkspace()
                workspace.openURL_(url)
        except ImportError:
            # Fallback if PyObjC is not available
            pass

    def check_single_site(self, url: str) -> httpcheck.SiteStatus:
        """Check a single site using the main httpcheck logic"""
        # Ensure URL has a scheme
        if not urlparse(url).scheme:
            url = f"https://{url}"

        # Call httpcheck.check_site with correct parameters
        return httpcheck.check_site(
            site=url,
            timeout=10.0,
            retries=2,
            follow_redirects="always",
            max_redirects=10
        )

    @rumps.clicked("Auto-check")
    def toggle_auto_check(self, sender):
        """Toggle automatic background checking"""
        if self.timer:
            self.timer.stop()
            self.timer = None
            sender.title = "Auto-check: OFF"
            logging.info("Auto-check disabled")
        else:
            self.start_background_checking()
            sender.title = "Auto-check: ON"
            logging.info("Auto-check enabled with %ss interval",
                         self.check_interval)

    def start_background_checking(self):
        """Start the background checking timer"""
        if self.sites and not self.timer:
            self.timer = rumps.Timer(self.perform_check, self.check_interval)
            self.timer.start()

    @rumps.clicked("Add Site...")
    def add_site(self, _):
        """Add a new site to monitor with input validation"""
        # Use a more reliable input method
        script = '''
        tell application "System Events"
            activate
            set userInput to text returned of (display dialog "Enter URL to monitor:" default answer "https://" with title "Add Site - onSite")
        end tell
        return userInput
        '''

        try:
            import subprocess
            result = subprocess.run(['osascript', '-e', script],
                                    capture_output=True, text=True, check=True)
            url = result.stdout.strip()

            # Validate and add the site
            success, message = self.validate_and_add_site(url)

            if success:
                normalized_url = message  # message contains the normalized URL

                self.sites.append(normalized_url)
                self.save_sites()
                logging.info(f"Added site: {normalized_url}")

                # Immediately check the new site
                self.notification_manager.send_notification(
                    title="onSite",
                    message=f"Site added: {normalized_url}"[:75],
                    subtitle="Checking status..."
                )

                # Check the new site in background
                def check_new_site():
                    try:
                        result = self.check_single_site(normalized_url)
                        try:
                            status_code = int(result.status)
                        except ValueError:
                            status_code = 0

                        if status_code not in range(200, 400):
                            self.failed_sites.add(normalized_url)
                            self.notification_manager.send_notification(
                                title="⚠️ New Site Issue",
                                message=(f"{normalized_url} is not "
                                         "responding properly"),
                                subtitle=f"Status: {result.status}"
                            )
                        else:
                            self.notification_manager.send_notification(
                                title="✅ New Site OK",
                                message=f"{normalized_url} is responding",
                                subtitle=f"Status: {result.status}"
                            )

                        self.update_status_icon()
                        self.build_menu()

                    except Exception as exc:
                        self.failed_sites.add(normalized_url)
                        logging.error(
                            f"Error checking new site {normalized_url}: {exc}")
                        self.notification_manager.send_notification(
                            title="❌ New Site Error",
                            message=f"Failed to check {normalized_url}",
                            subtitle=str(exc)[:50]
                        )
                        self.update_status_icon()
                        self.build_menu()

                thread = threading.Thread(target=check_new_site)
                thread.daemon = True
                thread.start()

                self.build_menu()

                # Start auto-check if this is the first site
                if len(self.sites) == 1 and not self.timer:
                    self.start_background_checking()
            else:
                # Show validation error
                escaped_message = message.replace('"', '\\"').replace('\n', '\\n')
                error_script = f'''
                tell application "System Events"
                    activate
                    display dialog "Invalid URL: {escaped_message}" with title "Add Site Error - onSite" buttons {{"OK"}} default button "OK" with icon caution
                end tell
                '''
                subprocess.run(['osascript', '-e', error_script], check=False)
                logging.warning(
                    f"Failed to add site - validation error: {message}")

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to rumps dialog if AppleScript fails
            response = rumps.Window(
                title="Add Site - onSite",
                message="Enter URL to monitor:",
                default_text="https://",
                ok="Add",
                cancel="Cancel"
            ).run()

            if response.clicked and response.text:
                url = response.text.strip()

                # Validate and add the site
                success, message = self.validate_and_add_site(url)

                if success:
                    # message contains the normalized URL
                    normalized_url = message

                    self.sites.append(normalized_url)
                    self.save_sites()
                    logging.info("Added site: %s", normalized_url)

                    # Immediately check the new site
                    self.notification_manager.send_notification(
                        title="onSite",
                        message=f"Site added: {normalized_url}"[:75],
                        subtitle="Checking status..."
                    )

                    # Check the new site in background
                    def check_new_site():
                        try:
                            result = self.check_single_site(normalized_url)
                            try:
                                status_code = int(result.status)
                            except ValueError:
                                status_code = 0

                            if status_code not in range(200, 400):
                                self.failed_sites.add(normalized_url)
                                self.notification_manager.send_notification(
                                    title="⚠️ New Site Issue",
                                    message=(
                                        f"{normalized_url} is not "
                                        "responding properly"),
                                    subtitle=f"Status: {result.status}"
                                )
                            else:
                                self.notification_manager.send_notification(
                                    title="✅ New Site OK",
                                    message=f"{normalized_url} is responding",
                                    subtitle=f"Status: {result.status}"
                                )

                            self.update_status_icon()
                            self.build_menu()

                        except Exception as exc:
                            self.failed_sites.add(normalized_url)
                            logging.error(
                                f"Error checking new site "
                                f"{normalized_url}: {exc}")
                            self.notification_manager.send_notification(
                                title="❌ New Site Error",
                                message=f"Failed to check {normalized_url}",
                                subtitle=str(exc)[:50]
                            )
                            self.update_status_icon()
                            self.build_menu()

                    thread = threading.Thread(target=check_new_site)
                    thread.daemon = True
                    thread.start()

                    self.build_menu()

                    # Start auto-check if this is the first site
                    if len(self.sites) == 1 and not self.timer:
                        self.start_background_checking()
                else:
                    # Show validation error using notification as fallback
                    self.notification_manager.send_notification(
                        title="❌ Invalid URL",
                        message=message,
                        subtitle="Please check the URL format and try again"
                    )
                    logging.warning(
                        f"Failed to add site - validation error: {message}")

    @rumps.clicked("Remove Site...")
    def remove_site(self, _):
        """Remove a site from monitoring"""
        if not self.sites:
            self.notification_manager.send_notification(
                title="onSite",
                message="No sites to remove"
            )
            return

        # Create a simple picker using AppleScript
        # Escape any quotes in site URLs for AppleScript
        escaped_sites = [site.replace('"', '\\"') for site in self.sites]
        sites_list = '", "'.join(escaped_sites)
        script = f'''
        tell application "System Events"
            activate
            set sitesList to {{"{sites_list}"}}
            set selectedSite to choose from list sitesList with title "Remove Site" with prompt "Select site to remove:"
            if selectedSite is not false then
                return selectedSite as string
            else
                return ""
            end if
        end tell
        '''

        try:
            import subprocess
            result = subprocess.run(['osascript', '-e', script],
                                    capture_output=True, text=True, check=True)
            selected = result.stdout.strip()

            if selected and selected in self.sites:
                self.sites.remove(selected)
                self.failed_sites.discard(selected)
                self.save_sites()
                self.build_menu()
                self.update_status_icon()
                self.notification_manager.send_notification(
                    title="onSite",
                    message=f"Site removed: {selected}"
                )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to simple numbering system
            sites_text = "\n".join(
                f"{i+1}. {site}" for i, site in enumerate(self.sites))
            response = rumps.Window(
                title="Remove Site",
                message=f"Enter number of site to remove:\n\n{sites_text}",
                default_text="1",
                ok="Remove",
                cancel="Cancel"
            ).run()

            if response.clicked and response.text:
                try:
                    index = int(response.text) - 1
                    if 0 <= index < len(self.sites):
                        removed_site = self.sites.pop(index)
                        self.failed_sites.discard(removed_site)
                        self.save_sites()
                        self.build_menu()
                        self.update_status_icon()
                        self.notification_manager.send_notification(
                            title="onSite",
                            message=f"Site removed: {removed_site}"
                        )
                except (ValueError, IndexError):
                    self.notification_manager.send_notification(
                        title="onSite",
                        message="Invalid selection"
                    )

    @rumps.clicked("Edit Sites...")
    def edit_sites(self, _):
        """Open sites file in default editor with validation instructions"""
        # Create a backup before editing
        try:
            import shutil
            backup_file = self.config_dir / 'sites_backup.json'
            shutil.copy2(self.sites_file, backup_file)
            logging.info(f"Created backup: {backup_file}")
        except Exception as exc:
            logging.warning(f"Could not create backup: {exc}")

        os.system(f"open -t {self.sites_file}")

        # Show validation instructions
        instruction_script = '''
        tell application "System Events"
            activate
            display dialog "Edit Sites Instructions:\\n\\n- Each URL should be a complete HTTP/HTTPS address\\n- Example: https://example.com\\n- Save the file when done\\n- The app will validate URLs when reloaded\\n\\nBackup created: sites_backup.json" with title "Edit Sites - onSite" buttons {"OK"} default button "OK" with icon note
        end tell
        '''

        try:
            import subprocess
            subprocess.run(['osascript', '-e', instruction_script],
                           check=False)
        except Exception:
            # Fallback to notification
            self.notification_manager.send_notification(
                title="onSite",
                message="Edit sites file",
                subtitle=("Save file when done. Backup created: "
                          "sites_backup.json")
            )

    @rumps.clicked("Check interval")
    def change_interval(self, _):
        """Change the check interval"""
        response = rumps.Window(
            title="Change Check Interval",
            message="Enter check interval in seconds:",
            default_text=str(self.check_interval),
            ok="Set",
            cancel="Cancel"
        ).run()

        if response.clicked and response.text:
            try:
                interval = int(response.text)
                if interval >= 60:  # Minimum 1 minute
                    self.check_interval = interval
                    self.save_config()

                    # Restart timer if active
                    if self.timer:
                        self.timer.stop()
                        self.start_background_checking()

                    self.build_menu()
                    self.notification_manager.send_notification(
                        title="onSite",
                        message="Interval updated",
                        subtitle=f"Now checking every {interval} seconds"
                    )
                else:
                    self.notification_manager.send_notification(
                        title="onSite",
                        message="Invalid interval",
                        subtitle="Minimum interval is 60 seconds"
                    )
            except ValueError:
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Invalid input",
                    subtitle="Please enter a number"
                )

    @rumps.clicked("Clear failed sites")
    def clear_failed(self, _):
        """Clear the failed sites list"""
        self.failed_sites.clear()
        self.update_status_icon()
        self.build_menu()
        self.notification_manager.send_notification(
            title="onSite",
            message="Failed sites list cleared"
        )

    @rumps.clicked("View logs")
    def view_logs(self, _):
        """Open the log file in Console.app"""
        try:
            # First try to open in Console.app (macOS system log viewer)
            import subprocess
            result = subprocess.run(
                ['open', '-a', 'Console', str(self.log_file)],
                capture_output=True, text=True)
            if result.returncode == 0:
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Log file opened in Console.app",
                    subtitle=f"File: {self.log_file.name}"
                )
            else:
                # Fallback to default text editor
                subprocess.run(['open', '-t', str(self.log_file)], check=True)
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Log file opened in text editor",
                    subtitle=f"File: {self.log_file.name}"
                )
        except Exception:
            # Final fallback - reveal in Finder
            try:
                subprocess.run(['open', '-R', str(self.log_file)], check=True)
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Log file revealed in Finder",
                    subtitle=f"Location: {self.log_dir}"
                )
            except Exception:
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Could not open log file",
                    subtitle=f"Check: {self.log_file}"
                )

    @rumps.clicked("About")
    def about(self, _):
        """Show about dialog"""
        # Try to show a proper macOS About dialog
        try:
            import subprocess

            about_text = """onSite
Version 1.0

A lightweight menu bar application for monitoring HTTP endpoints
with native macOS notifications and real-time status updates.

Created by Thomas Juul Dyhr
Email: thomas@dyhr.com
Copyright © June 2025. All rights reserved.

Built with Python, rumps, and PyObjC for macOS integration."""

            # Use AppleScript to show a proper dialog
            escaped_about = about_text.replace('"', '\\"').replace('\n', '\\n')
            script = f'''
            tell application "System Events"
                activate
                display dialog "{escaped_about}" with title "About onSite" buttons {{"OK"}} default button "OK" with icon note
            end tell
            '''

            subprocess.run(['osascript', '-e', script], check=False)

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to notification if AppleScript fails
            self.notification_manager.send_notification(
                title="onSite",
                message="Version 1.0",
                subtitle="Created by Thomas Juul Dyhr © June 2025"
            )

    def load_sites(self):
        """Load sites from configuration file with validation"""
        if self.sites_file.exists():
            try:
                with open(self.sites_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    raw_sites = data.get('sites', [])

                    # Validate and normalize each site
                    validated_sites = []
                    invalid_sites = []

                    for site in raw_sites:
                        if isinstance(site, str):
                            is_valid, result = self.validate_url(site)
                            if is_valid:
                                # result is normalized URL
                                validated_sites.append(result)
                            else:
                                # result is error message
                                invalid_sites.append(f"{site} - {result}")
                        else:
                            invalid_sites.append(
                                f"{site} - Invalid format (not a string)")

                    self.sites = validated_sites

                    if invalid_sites:
                        logging.warning("Found %d invalid sites in config:",
                                        len(invalid_sites))
                        for invalid in invalid_sites:
                            logging.warning("  - %s", invalid)

                        # Show notification about invalid sites
                        # Show notification about invalid sites
                        if len(invalid_sites) <= 3:
                            # Show all sites if few enough
                            pass
                        else:
                            # Show first two + count for many sites
                            pass

                        self.notification_manager.send_notification(
                            title="⚠️ Invalid Sites Found",
                            message=(f"Removed {len(invalid_sites)} "
                                     "invalid sites"),
                            subtitle="Check logs for details"
                        )

                        # Save the cleaned sites list
                        self.save_sites()

                    logging.info("Loaded %d valid sites (removed %d invalid)",
                                 len(validated_sites), len(invalid_sites))

            except Exception as exc:
                logging.error("Error loading sites: %s", exc)
                self.sites = []
        else:
            # Create default sites file
            self.sites = []
            self.save_sites()

    def save_sites(self):
        """Save sites to configuration file"""
        try:
            with open(self.sites_file, 'w', encoding='utf-8') as file:
                json.dump({'sites': self.sites}, file, indent=2)
            logging.info("Saved %s sites", len(self.sites))
        except Exception as exc:
            logging.error("Error saving sites: %s", exc)

    def load_config(self):
        """Load application configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    config = json.load(file)
                    self.check_interval = config.get('check_interval', 900)
                    self.debug_mode = config.get('debug_mode', False)
            except Exception as exc:
                # Use print before logging is setup
                print(f"Error loading config: {exc}")

    def save_config(self):
        """Save application configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump({
                    'check_interval': self.check_interval,
                    'debug_mode': getattr(self, 'debug_mode', False)
                }, file, indent=2)
        except Exception as exc:
            logging.error("Error saving config: %s", exc)


if __name__ == "__main__":
    # Check if running on macOS
    import platform
    if platform.system() != "Darwin":
        print("This menu bar app is only supported on macOS")
        exit(1)

    # Run the app
    HTTPCheckApp().run()
