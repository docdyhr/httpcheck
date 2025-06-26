#!/usr/bin/env python3
"""
onSite - HTTP Site Monitoring for macOS
A lightweight menu bar application for monitoring HTTP endpoints
"""

import json
import logging
import os
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import rumps  # pylint: disable=import-error

# Import core functionality from main httpcheck module
import httpcheck
from macos_notifications import MacOSNotificationManager


class HTTPCheckApp(rumps.App):
    """Menu bar application for HTTP status monitoring"""

    def __init__(self):
        super().__init__("onSite", title=None)

        # Initialize state
        self.sites: list[str] = []
        self.failed_sites: set[str] = set()
        self.last_check_time: Optional[datetime] = None
        self.checking = False
        self.check_interval = 900  # 15 minutes default
        self.timer = None

        # File monitoring variables
        self.file_monitor_timer = None
        self.last_file_mtime = 0

        # Icon and UI attributes
        self.title = None
        self.template = False
        self.app_icon_path = None
        self.log_level = "INFO"
        self.log_to_console = False

        # Setup paths following macOS best practices
        self.config_dir = Path.home() / ".httpcheck"
        self.config_dir.mkdir(exist_ok=True)
        self.sites_file = self.config_dir / "sites.json"
        self.config_file = self.config_dir / "config.json"

        # Setup log directory following macOS best practices
        self.log_dir = Path.home() / "Library" / "Logs" / "onSite"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "onsite.log"

        # Load configuration
        self.load_config()

        # Setup logging following macOS best practices
        # Check for debug mode from config
        self.debug_mode = getattr(self, "debug_mode", False)
        self.setup_logging()

        # Initialize native notifications (needed for load_sites error handling)
        self.notification_manager = MacOSNotificationManager()

        # Load sites after notification manager is ready
        self.load_sites()

        # Build initial menu
        self.build_menu()

        # Setup icon
        self.setup_icon()

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
        if url.startswith(("ftp://", "file://", "mailto:")):
            return False, "URL must use http:// or https://"

        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            parsed = urlparse(url)

            # Check if scheme is valid
            if parsed.scheme not in ("http", "https"):
                return False, "URL must use http:// or https://"

            # Check if domain exists
            if not parsed.netloc:
                return False, "URL must include a domain name"

            # Basic domain format validation
            domain_pattern = re.compile(
                r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
                r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
            )

            # Extract just the hostname (remove port if present)
            hostname = parsed.netloc.split(":")[0]

            # Check for valid domain format (allow localhost)
            if (
                not domain_pattern.match(hostname)
                and not self._is_valid_ip(hostname)
                and hostname.lower() != "localhost"
            ):
                return False, "Invalid domain name or IP address format"

            # Check for minimum domain requirements (allow localhost)
            if (
                "." not in hostname
                and not self._is_valid_ip(hostname)
                and hostname.lower() != "localhost"
            ):
                return False, (
                    "Domain name must contain at least one dot " "(e.g., example.com)"
                )

            # Check URL length (reasonable limit)
            if len(url) > 2048:
                return False, "URL is too long (maximum 2048 characters)"

            # Check for common invalid characters in URL
            invalid_chars = [" ", "<", ">", '"', "{", "}", "|", "\\", "^", "`"]
            for char in invalid_chars:
                if char in url:
                    return False, f"URL contains invalid character: '{char}'"

            # Check for suspicious patterns
            if url.count("://") > 1:
                return False, "URL contains multiple protocol indicators"

            # Check port number if present
            if ":" in parsed.netloc and not self._is_valid_port(parsed.netloc):
                return False, "Invalid port number"

            # Check for minimum path requirements for some common patterns
            if parsed.path and len(parsed.path) > 1000:
                return False, "URL path is too long"

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

    def _is_valid_port(self, netloc: str) -> bool:
        """Check if port number in netloc is valid"""
        try:
            if ":" in netloc:
                port_str = netloc.split(":")[-1]
                port = int(port_str)
                return 1 <= port <= 65535
            return True  # No port specified is valid
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
        """Setup logging following macOS best practices with flexible configuration"""
        try:
            # Clear any existing handlers to prevent duplicates
            logging.root.handlers = []

            # Get log level from config or use default
            try:
                log_level = getattr(logging, self.log_level)
            except AttributeError:
                log_level = logging.INFO
                print(f"Warning: Invalid log level '{self.log_level}', using INFO")

            # Create handlers list
            handlers = []

            # Create file handler with rotation support
            try:
                from logging.handlers import RotatingFileHandler

                # Create rotating file handler with configurable settings
                file_handler = RotatingFileHandler(
                    self.log_file,
                    maxBytes=self.log_max_bytes,
                    backupCount=self.log_backup_count,
                    encoding="utf-8",
                )

                # Create formatter with configurable format
                formatter = logging.Formatter(
                    self.log_format, datefmt=self.log_date_format
                )
                file_handler.setFormatter(formatter)
                handlers.append(file_handler)

            except ImportError:
                # Fallback to basic file handler if RotatingFileHandler unavailable
                file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
                formatter = logging.Formatter(
                    self.log_format, datefmt=self.log_date_format
                )
                file_handler.setFormatter(formatter)
                handlers.append(file_handler)

            # Add console handler if requested
            if self.log_to_console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                handlers.append(console_handler)

            # Configure root logger
            logging.basicConfig(
                handlers=handlers, level=log_level, force=True  # Force reconfiguration
            )

            # Apply module-specific log levels
            for module_name, module_level in self.module_log_levels.items():
                try:
                    module_logger = logging.getLogger(module_name)
                    module_logger.setLevel(getattr(logging, module_level.upper()))
                except (AttributeError, ValueError) as exc:
                    print(f"Warning: Invalid log level for module {module_name}: {exc}")

            # Configure specific loggers to reduce noise if needed
            if log_level > logging.DEBUG:
                # Reduce verbosity of urllib3 and requests
                logging.getLogger("urllib3").setLevel(logging.WARNING)
                logging.getLogger("requests").setLevel(logging.WARNING)

            # Log startup messages
            logger = logging.getLogger("onSite")
            logger.info("onSite started successfully")
            logger.info(f"Log level: {self.log_level}")
            logger.info(f"Log file: {self.log_file}")
            logger.info(f"Config directory: {self.config_dir}")

            if self.log_to_console:
                logger.debug("Console logging enabled")

            if self.module_log_levels:
                logger.debug(f"Module-specific log levels: {self.module_log_levels}")

        except Exception as exc:
            # Fallback to console logging if file logging fails
            print(f"Warning: Could not setup logging: {exc}")
            logging.basicConfig(
                level=logging.INFO,
                format=self.log_format,
                datefmt=self.log_date_format,
                force=True,
            )

    def build_menu(self):
        """Build the menu structure"""
        # pylint: disable=no-member
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
        self.menu.add(
            rumps.MenuItem(
                f"Auto-check: {auto_status}", callback=self.toggle_auto_check
            )
        )
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
        self.menu.add(rumps.MenuItem("Remove Site...", callback=self.remove_site))
        self.menu.add(rumps.MenuItem("Edit Sites...", callback=self.edit_sites))
        self.menu.add(rumps.separator)

        # Settings
        settings_menu = rumps.MenuItem("Settings")
        interval_item = rumps.MenuItem(f"Check interval: {self.check_interval}s")
        interval_item.set_callback(self.change_interval)
        settings_menu.add(interval_item)
        settings_menu.add(
            rumps.MenuItem("Clear failed sites", callback=self.clear_failed)
        )
        settings_menu.add(rumps.separator)

        # Logging submenu
        logging_menu = rumps.MenuItem("Logging")
        logging_menu.add(
            rumps.MenuItem(
                f"Level: {getattr(self, 'log_level', 'INFO')}",
                callback=self.change_log_level,
            )
        )
        logging_menu.add(
            rumps.MenuItem(
                f"Console: {'✓' if getattr(self, 'log_to_console', False) else '✗'}",
                callback=self.toggle_console_logging,
            )
        )
        logging_menu.add(rumps.MenuItem("View logs", callback=self.view_logs))
        settings_menu.add(logging_menu)

        self.menu.add(settings_menu)

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("About", callback=self.about))
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    def setup_icon(self):
        """Setup the menu bar icon from Icon.icns file"""
        try:

            # Try to find the icon file
            icon_path = None

            # Check if we're running from a bundle
            bundle_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            # Try different possible locations
            possible_paths = [
                os.path.join(bundle_path, "Resources", "Icon.icns"),
                os.path.join(bundle_path, "images", "Icon.icns"),
                os.path.join(os.path.dirname(__file__), "images", "Icon.icns"),
                "images/Icon.icns",
            ]

            # Log all paths we're trying
            logging.getLogger("onSite").debug(f"Bundle path: {bundle_path}")
            logging.getLogger("onSite").debug(
                f"__file__ dir: {os.path.dirname(__file__)}"
            )
            for i, path in enumerate(possible_paths):
                exists = os.path.exists(path)
                logging.getLogger("onSite").debug(
                    f"Path {i+1}: {path} (exists: {exists})"
                )

            for path in possible_paths:
                if os.path.exists(path):
                    icon_path = path
                    break

            if icon_path:
                # Store the app icon path for About dialog and menu bar
                self.app_icon_path = icon_path

                # Set initial icon using rumps method (expects file path)
                self.icon = icon_path
                logging.getLogger("onSite").info(f"Loaded icon from {icon_path}")
            else:
                logging.getLogger("onSite").warning(
                    "Icon.icns not found, using fallback"
                )
                self._use_fallback_icon()

        except Exception as exc:
            logging.getLogger("onSite").error(f"Error setting up icon: {exc}")
            self._use_fallback_icon()

    def _use_fallback_icon(self):
        """Use emoji fallback if icon file not available"""
        self.title = "⚡"
        self.template = True
        self.app_icon_path = None

    def update_status_icon(self):
        """Update the menu bar icon based on status"""
        if hasattr(self, "app_icon_path") and self.app_icon_path:
            # Use the icon file path
            if self.failed_sites:
                # For failures, show the icon with a red badge using title
                self.icon = self.app_icon_path
                self.title = "●"  # Red dot indicator next to icon
                self.template = False  # Don't use template mode to show color
            else:
                # Normal state - use icon as template
                self.icon = self.app_icon_path
                self.title = None  # No supplementary text
                self.template = True  # Use template mode for normal state
        else:
            # Fallback to emoji-based status
            if self.failed_sites:
                self.title = "🔴⚡"
                self.template = False
            else:
                self.title = "⚡"
                self.template = True

    @rumps.clicked("Check Now")
    def check_now(self, _):
        """Manually trigger a check of all sites"""
        if self.checking:
            self.notification_manager.send_notification(
                title="onSite", message="Check in progress", subtitle="Please wait..."
            )
            return

        if not self.sites:
            self.notification_manager.send_notification(
                title="onSite",
                message="No sites configured",
                subtitle="Add sites to monitor first",
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
                        logging.getLogger("onSite").warning(
                            "Site failed: %s - Status: %s", site, result.status
                        )

                        # Send notification for newly failed sites
                        if site not in old_failed:
                            self.notification_manager.send_site_down_alert(
                                site=site,
                                status_code=status_code,
                                callback=self.handle_notification_click,
                            )
                    else:
                        # Site recovered
                        if site in old_failed:
                            self.notification_manager.send_site_recovery_alert(
                                site=site,
                                status_code=status_code,
                                callback=self.handle_notification_click,
                            )

                except Exception as exc:
                    self.failed_sites.add(site)
                    logging.getLogger("onSite").error(
                        "Error checking %s: %s", site, str(exc)
                    )

                    if site not in old_failed:
                        self.notification_manager.send_error_notification(
                            # Truncate long error messages
                            error_msg=str(exc)[:100],
                            site=site,
                        )

            self.last_check_time = datetime.now()
            logging.getLogger("onSite").info(
                "Check completed: %s/%s sites failed",
                len(self.failed_sites),
                total_sites,
            )

            # Send summary notification
            try:
                self.notification_manager.send_check_complete_summary(
                    total=total_sites,
                    failed=len(self.failed_sites),
                    callback=None,  # Disable callback temporarily to fix crash
                )
            except Exception as exc:
                logging.getLogger("onSite").error(
                    f"Error sending summary notification: {exc}"
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
                if not url.startswith(("http://", "https://")):
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
            max_redirects=10,
        )

    @rumps.clicked("Auto-check")
    def toggle_auto_check(self, sender):
        """Toggle automatic background checking"""
        if self.timer:
            self.timer.stop()
            self.timer = None
            sender.title = "Auto-check: OFF"
            logging.getLogger("onSite").info("Auto-check disabled")
        else:
            self.start_background_checking()
            sender.title = "Auto-check: ON"
            logging.getLogger("onSite").info(
                "Auto-check enabled with %ss interval", self.check_interval
            )

    def start_background_checking(self):
        """Start the background checking timer"""
        if self.sites and not self.timer:
            self.timer = rumps.Timer(self.perform_check, self.check_interval)
            self.timer.start()

    @rumps.clicked("Add Site...")
    def add_site(self, _):
        """Add a new site to monitor with input validation"""
        # Use a more reliable input method
        script = """tell application "System Events"
    activate
    set userInput to text returned of (display dialog "Enter URL to monitor:" default answer "https://" with title "Add Site - onSite")
end tell
return userInput"""

        try:
            logging.getLogger("onSite").debug(
                f"Executing AppleScript: {script[:100]}..."
            )
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, check=True
            )
            url = result.stdout.strip()
            logging.getLogger("onSite").debug(f"AppleScript result: {url}")

            # Validate and add the site
            success, message = self.validate_and_add_site(url)

            if success:
                normalized_url = message  # message contains the normalized URL

                self.sites.append(normalized_url)
                self.save_sites()
                logging.getLogger("onSite").info(f"Added site: {normalized_url}")

                # Immediately check the new site
                self.notification_manager.send_notification(
                    title="onSite",
                    message=f"Site added: {normalized_url}"[:75],
                    subtitle="Checking status...",
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
                                    f"{normalized_url} is not " "responding properly"
                                ),
                                subtitle=f"Status: {result.status}",
                            )
                        else:
                            self.notification_manager.send_notification(
                                title="✅ New Site OK",
                                message=f"{normalized_url} is responding",
                                subtitle=f"Status: {result.status}",
                            )

                        self.update_status_icon()
                        self.build_menu()

                    except Exception as exc:
                        self.failed_sites.add(normalized_url)
                        logging.getLogger("onSite").error(
                            f"Error checking new site {normalized_url}: {exc}"
                        )
                        self.notification_manager.send_notification(
                            title="❌ New Site Error",
                            message=f"Failed to check {normalized_url}",
                            subtitle=str(exc)[:50],
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
                escaped_message = (
                    message.replace('"', '\\"')
                    .replace("\n", "\\n")
                    .replace("\\", "\\\\")
                )
                error_script = f"""tell application "System Events"
    activate
    display dialog "Invalid URL: {escaped_message}" with title "Add Site Error - onSite" buttons {{"OK"}} default button "OK" with icon caution
end tell"""
                subprocess.run(["osascript", "-e", error_script], check=False)
                logging.getLogger("onSite").warning(
                    f"Failed to add site - validation error: {message}"
                )

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to rumps dialog if AppleScript fails
            response = rumps.Window(
                title="Add Site - onSite",
                message="Enter URL to monitor:",
                default_text="https://",
                ok="Add",
                cancel="Cancel",
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
                    logging.getLogger("onSite").info("Added site: %s", normalized_url)

                    # Immediately check the new site
                    self.notification_manager.send_notification(
                        title="onSite",
                        message=f"Site added: {normalized_url}"[:75],
                        subtitle="Checking status...",
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
                                        "responding properly"
                                    ),
                                    subtitle=f"Status: {result.status}",
                                )
                            else:
                                self.notification_manager.send_notification(
                                    title="✅ New Site OK",
                                    message=f"{normalized_url} is responding",
                                    subtitle=f"Status: {result.status}",
                                )

                            self.update_status_icon()
                            self.build_menu()

                        except Exception as exc:
                            self.failed_sites.add(normalized_url)
                            logging.getLogger("onSite").error(
                                f"Error checking new site " f"{normalized_url}: {exc}"
                            )
                            self.notification_manager.send_notification(
                                title="❌ New Site Error",
                                message=f"Failed to check {normalized_url}",
                                subtitle=str(exc)[:50],
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
                        subtitle="Please check the URL format and try again",
                    )
                    logging.getLogger("onSite").warning(
                        f"Failed to add site - validation error: {message}"
                    )

    @rumps.clicked("Remove Site...")
    def remove_site(self, _):
        """Remove a site from monitoring with validation"""
        if not self.sites:
            self.notification_manager.send_notification(
                title="onSite",
                message="No sites to remove",
                subtitle="Add sites first to monitor them",
            )
            return

        # Validate that we have valid sites list
        if len(self.sites) > 50:  # Safety check
            logging.getLogger("onSite").error(
                "Too many sites detected, this shouldn't happen"
            )
            self.notification_manager.send_error_notification(
                error_msg="Site list appears corrupted, please check configuration"
            )
            return

        # Create a simple picker using AppleScript
        # Escape any quotes in site URLs for AppleScript
        escaped_sites = [
            site.replace('"', '\\"').replace("\\", "\\\\") for site in self.sites
        ]

        if not escaped_sites:
            return

        sites_list = '", "'.join(escaped_sites)
        script = f"""tell application "System Events"
    activate
    set sitesList to {{"{sites_list}"}}
    set selectedSite to choose from list sitesList with title "Remove Site" with prompt "Select site to remove:"
    if selectedSite is not false then
        return selectedSite as string
    else
        return ""
    end if
end tell"""

        try:

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, check=True
            )
            selected = result.stdout.strip()

            if selected and selected in self.sites:
                self.sites.remove(selected)
                self.failed_sites.discard(selected)
                self.save_sites()
                self.build_menu()
                self.update_status_icon()
                self.notification_manager.send_notification(
                    title="onSite", message=f"Site removed: {selected}"
                )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to simple numbering system
            sites_text = "\n".join(
                f"{i+1}. {site}" for i, site in enumerate(self.sites)
            )
            response = rumps.Window(
                title="Remove Site",
                message=f"Enter number of site to remove:\n\n{sites_text}",
                default_text="1",
                ok="Remove",
                cancel="Cancel",
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
                            title="onSite", message=f"Site removed: {removed_site}"
                        )
                except (ValueError, IndexError):
                    self.notification_manager.send_notification(
                        title="onSite", message="Invalid selection"
                    )

    @rumps.clicked("Edit Sites...")
    def edit_sites(self, _):
        """Open sites file in default editor with real-time monitoring"""
        # Create a backup before editing
        try:
            import shutil

            backup_file = self.config_dir / "sites_backup.json"
            shutil.copy2(self.sites_file, backup_file)
            logging.getLogger("onSite").info(f"Created backup: {backup_file}")
        except Exception as exc:
            logging.getLogger("onSite").warning(f"Could not create backup: {exc}")

        # Show enhanced validation instructions
        if hasattr(self, "app_icon_path") and self.app_icon_path:
            instruction_script = f"""tell application "System Events"
    activate
    display dialog "Edit Sites Instructions:\\n\\n• JSON format: {{\\\"sites\\\": [\\\"https://example.com\\\", \\\"https://another.com\\\"]}}\\n• Each URL must be complete HTTP/HTTPS address\\n• File will be monitored and reloaded automatically\\n• Backup created: sites_backup.json\\n\\nClick OK to open editor." with title "Edit Sites - onSite" buttons {{"OK", "Cancel"}} default button "OK" with icon (POSIX file "{self.app_icon_path}")
end tell
return result"""
        else:
            instruction_script = """tell application "System Events"
    activate
    display dialog "Edit Sites Instructions:\\n\\n• JSON format: {{\\\"sites\\\": [\\\"https://example.com\\\", \\\"https://another.com\\\"]}}\\n• Each URL must be complete HTTP/HTTPS address\\n• File will be monitored and reloaded automatically\\n• Backup created: sites_backup.json\\n\\nClick OK to open editor." with title "Edit Sites - onSite" buttons {{"OK", "Cancel"}} default button "OK" with icon note
end tell
return result"""

        try:
            result = subprocess.run(
                ["osascript", "-e", instruction_script],
                capture_output=True,
                text=True,
                check=True,
            )
            button_clicked = result.stdout.strip()

            if "Cancel" in button_clicked:
                return

        except Exception as exc:
            logging.getLogger("onSite").warning(
                f"Could not show instructions dialog: {exc}"
            )
            # Continue anyway

        # Open the file for editing
        os.system(f"open -t {self.sites_file}")

        # Start real-time file monitoring
        self.start_file_monitoring()

    def start_file_monitoring(self):
        """Start monitoring the sites file for changes"""
        try:
            # Stop any existing monitoring
            if hasattr(self, "file_monitor_timer") and self.file_monitor_timer:
                self.file_monitor_timer.stop()

            # Store the current modification time
            if self.sites_file.exists():
                self.last_file_mtime = self.sites_file.stat().st_mtime
            else:
                self.last_file_mtime = 0

            # Start a timer to check for file changes every 2 seconds
            self.file_monitor_timer = rumps.Timer(self.check_file_changes, 2)
            self.file_monitor_timer.start()

            # Show notification that monitoring started
            self.notification_manager.send_notification(
                title="File Monitor Started",
                message="Monitoring sites.json for changes",
                subtitle="File will be reloaded automatically when saved",
            )

            logging.getLogger("onSite").info("Started file monitoring for sites.json")

        except Exception as exc:
            logging.getLogger("onSite").error(f"Failed to start file monitoring: {exc}")
            self.notification_manager.send_error_notification(
                error_msg=f"Could not start file monitoring: {exc}"
            )

    def check_file_changes(self, timer):
        """Check if the sites file has been modified"""
        try:
            if not self.sites_file.exists():
                return

            current_mtime = self.sites_file.stat().st_mtime

            # If file was modified
            if current_mtime > self.last_file_mtime:
                self.last_file_mtime = current_mtime

                # Brief delay to ensure file is fully written
                import time

                time.sleep(0.5)

                # Validate and reload the file
                self.validate_and_reload_sites_file()

        except Exception as exc:
            logging.getLogger("onSite").error(f"Error checking file changes: {exc}")

    def validate_and_reload_sites_file(self):
        """Validate and reload the sites file after changes"""
        try:
            # Validate the sites file
            is_valid, error_message, data = self.validate_json_file(
                self.sites_file, "sites"
            )

            if not is_valid:
                # Show validation error to user
                self.notification_manager.send_error_notification(
                    error_msg=f"Sites file invalid: {error_message[:100]}"
                )

                # Also show detailed dialog
                error_script = f"""tell application "System Events"
    activate
    display dialog "Sites file validation failed:\\n\\n{error_message.replace('"', '\\\\"')[:200]}\\n\\nPlease fix the file and save again, or restore from backup." with title "Validation Error - onSite" buttons {{"OK"}} default button "OK" with icon stop
end tell"""

                try:
                    subprocess.run(["osascript", "-e", error_script], check=False)
                except Exception:
                    pass  # Notification already sent above

                logging.getLogger("onSite").error(
                    f"Sites file validation failed: {error_message}"
                )
                return

            # File is valid, reload sites
            old_sites_count = len(self.sites)
            old_sites = self.sites.copy()

            self.load_sites()
            new_sites_count = len(self.sites)

            # Check what changed
            added_sites = set(self.sites) - set(old_sites)
            removed_sites = set(old_sites) - set(self.sites)

            # Rebuild menu with new sites
            self.build_menu()
            self.update_status_icon()

            # Clear failed sites that were removed
            self.failed_sites = {
                site for site in self.failed_sites if site in self.sites
            }

            # Create change summary
            changes = []
            if added_sites:
                changes.append(f"Added: {len(added_sites)} sites")
            if removed_sites:
                changes.append(f"Removed: {len(removed_sites)} sites")

            if changes:
                change_text = ", ".join(changes)
                subtitle = f"Total: {new_sites_count} sites"
            elif new_sites_count != old_sites_count:
                change_text = f"Updated: {old_sites_count} → {new_sites_count} sites"
                subtitle = "File validation successful"
            else:
                change_text = f"Reloaded {new_sites_count} sites"
                subtitle = "No changes detected"

            # Notify user of successful update
            self.notification_manager.send_notification(
                title="✅ Sites Updated", message=change_text, subtitle=subtitle
            )

            logging.getLogger("onSite").info(
                f"Sites file reloaded successfully: {change_text}"
            )

            # If we added new sites and auto-check is off, ask to start it
            if added_sites and not self.timer and len(self.sites) > 0:
                start_script = """tell application "System Events"
    activate
    display dialog "New sites added! Would you like to start automatic checking?" with title "Start Auto-Check - onSite" buttons {"Yes", "No"} default button "Yes" with icon question
end tell
return result"""

                try:
                    result = subprocess.run(
                        ["osascript", "-e", start_script],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    if "Yes" in result.stdout:
                        self.start_background_checking()
                        self.notification_manager.send_notification(
                            title="Auto-Check Started",
                            message=f"Now checking {len(self.sites)} sites every {self.check_interval}s",
                        )
                except Exception:
                    pass  # User can start manually if needed

        except Exception as exc:
            logging.getLogger("onSite").error(
                f"Error validating and reloading sites file: {exc}"
            )
            self.notification_manager.send_error_notification(
                error_msg=f"Failed to reload sites file: {exc}"
            )

    def stop_file_monitoring(self):
        """Stop monitoring the sites file"""
        try:
            if hasattr(self, "file_monitor_timer") and self.file_monitor_timer:
                self.file_monitor_timer.stop()
                self.file_monitor_timer = None
                logging.getLogger("onSite").info("Stopped file monitoring")
        except Exception as exc:
            logging.getLogger("onSite").error(f"Error stopping file monitoring: {exc}")

    def change_interval(self, _):
        """Change the check interval"""
        response = rumps.Window(
            title="Change Check Interval",
            message="Enter check interval in seconds:",
            default_text=str(self.check_interval),
            ok="Set",
            cancel="Cancel",
        ).run()

        if response.clicked and response.text:
            try:
                # Validate input format
                if not response.text.strip():
                    self.notification_manager.send_error_notification(
                        error_msg="No interval provided"
                    )
                    return

                # Parse and validate interval
                try:
                    interval = int(response.text.strip())
                except ValueError:
                    self.notification_manager.send_error_notification(
                        error_msg="Interval must be a number"
                    )
                    return

                # Validate interval range (60 seconds to 24 hours)
                if interval < 60:
                    self.notification_manager.send_error_notification(
                        error_msg="Minimum interval is 60 seconds (1 minute)"
                    )
                    return
                elif interval > 86400:  # 24 hours
                    self.notification_manager.send_error_notification(
                        error_msg="Maximum interval is 86400 seconds (24 hours)"
                    )
                    return

                # Update the interval
                old_interval = self.check_interval
                self.check_interval = interval

                # Save configuration
                try:
                    self.save_config()
                except Exception as exc:
                    # Restore old interval if save fails
                    self.check_interval = old_interval
                    logging.getLogger("onSite").error(
                        f"Failed to save interval change: {exc}"
                    )
                    self.notification_manager.send_error_notification(
                        error_msg=f"Could not save interval change: {exc}"
                    )
                    return

                # Restart timer if active
                if self.timer:
                    try:
                        self.timer.stop()
                        self.start_background_checking()
                    except Exception as exc:
                        logging.getLogger("onSite").error(
                            f"Error restarting timer: {exc}"
                        )

                self.build_menu()

                # Format interval for display
                if interval >= 3600:
                    display_text = f"{interval // 3600}h {(interval % 3600) // 60}m"
                elif interval >= 60:
                    display_text = f"{interval // 60}m {interval % 60}s"
                else:
                    display_text = f"{interval}s"

                self.notification_manager.send_notification(
                    title="onSite",
                    message="Check interval updated",
                    subtitle=f"Now checking every {display_text}",
                )

                logging.getLogger("onSite").info(
                    f"Check interval updated: {old_interval}s → {interval}s"
                )
            except ValueError:
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Invalid input",
                    subtitle="Please enter a number",
                )

    @rumps.clicked("Clear failed sites")
    def clear_failed(self, _):
        """Clear the failed sites list"""
        self.failed_sites.clear()
        self.update_status_icon()
        self.build_menu()
        self.notification_manager.send_notification(
            title="onSite", message="Failed sites list cleared"
        )

    @rumps.clicked("Log Level")
    def change_log_level(self, _):
        """Change the logging level"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        current_level = getattr(self, "log_level", "INFO")

        # Use AppleScript to create a list picker
        escaped_levels = '", "'.join(levels)
        script = f"""tell application "System Events"
    activate
    set levelsList to {{"{escaped_levels}"}}
    set selectedLevel to choose from list levelsList with title "Change Log Level" with prompt "Select logging level:" default items {{"{current_level}"}}
    if selectedLevel is not false then
        return selectedLevel as string
    else
        return ""
    end if
end tell"""

        try:

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, check=True
            )
            selected = result.stdout.strip()

            if selected and selected in levels:
                self.log_level = selected

                # Apply new log level immediately
                try:
                    new_level = getattr(logging, selected)
                    logging.getLogger().setLevel(new_level)

                    # Update specific loggers
                    if new_level > logging.DEBUG:
                        logging.getLogger("urllib3").setLevel(logging.WARNING)
                        logging.getLogger("requests").setLevel(logging.WARNING)
                    else:
                        logging.getLogger("urllib3").setLevel(new_level)
                        logging.getLogger("requests").setLevel(new_level)

                    self.save_config()
                    self.build_menu()

                    self.notification_manager.send_notification(
                        title="onSite", message=f"Log level changed to {selected}"
                    )
                    logging.getLogger("onSite").info(f"Log level changed to {selected}")

                except Exception as exc:
                    logging.getLogger("onSite").error(
                        f"Error changing log level: {exc}"
                    )

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to simple dialog
            response = rumps.Window(
                title="Change Log Level",
                message=f"Current level: {current_level}\nEnter new level (DEBUG, INFO, WARNING, ERROR, CRITICAL):",
                default_text=current_level,
                ok="Set",
                cancel="Cancel",
            ).run()

            if response.clicked and response.text.upper() in levels:
                self.log_level = response.text.upper()
                self.save_config()
                self.build_menu()
                self.notification_manager.send_notification(
                    title="onSite", message=f"Log level changed to {self.log_level}"
                )

    @rumps.clicked("Console")
    def toggle_console_logging(self, sender):
        """Toggle console logging on/off"""
        self.log_to_console = not getattr(self, "log_to_console", False)

        # Restart logging to apply changes
        self.setup_logging()

        self.save_config()
        self.build_menu()

        status = "enabled" if self.log_to_console else "disabled"
        self.notification_manager.send_notification(
            title="onSite", message=f"Console logging {status}"
        )
        logging.getLogger("onSite").info(f"Console logging {status}")

    @rumps.clicked("View logs")
    def view_logs(self, _):
        """Open the log file in Console.app"""
        try:
            # First try to open in Console.app (macOS system log viewer)

            result = subprocess.run(
                ["open", "-a", "Console", str(self.log_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Log file opened in Console.app",
                    subtitle=f"File: {self.log_file.name}",
                )
            else:
                # Fallback to default text editor
                subprocess.run(["open", "-t", str(self.log_file)], check=True)
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Log file opened in text editor",
                    subtitle=f"File: {self.log_file.name}",
                )
        except Exception:
            # Final fallback - reveal in Finder
            try:
                subprocess.run(["open", "-R", str(self.log_file)], check=True)
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Log file revealed in Finder",
                    subtitle=f"Location: {self.log_dir}",
                )
            except Exception:
                self.notification_manager.send_notification(
                    title="onSite",
                    message="Could not open log file",
                    subtitle=f"Check: {self.log_file}",
                )

    @rumps.clicked("About")
    def about(self, _):
        """Show about dialog"""
        # Try to show a proper macOS About dialog
        try:
            # Create styled text with SF Pro Rounded for the title
            about_text = """Version 1.0

A lightweight menu bar application for monitoring HTTP endpoints
with native macOS notifications and real-time status updates.

Created by Thomas Juul Dyhr
Email: thomas@dyhr.com
Copyright © June 2025. All rights reserved.

Built with Python, rumps, and PyObjC for macOS integration."""

            # Escape the about text for AppleScript
            escaped_about = (
                about_text.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )

            # Use display dialog which supports icon parameter better
            if hasattr(self, "app_icon_path") and self.app_icon_path:
                script = f"""tell application "System Events"
    activate
    display dialog "{escaped_about}" with title "About onSite" buttons {{"OK"}} default button "OK" with icon (POSIX file "{self.app_icon_path}")
end tell"""
            else:
                script = f"""tell application "System Events"
    activate
    display dialog "{escaped_about}" with title "About onSite" buttons {{"OK"}} default button "OK"
end tell"""

            subprocess.run(["osascript", "-e", script], check=False)

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to notification if AppleScript fails
            self.notification_manager.send_notification(
                title="onSite",
                message="Version 1.0",
                subtitle="Created by Thomas Juul Dyhr © June 2025",
            )

    def validate_json_file(
        self, file_path: Path, schema_type: str
    ) -> tuple[bool, str, dict]:
        """
        Validate JSON file format and content

        Args:
            file_path: Path to the JSON file
            schema_type: Type of schema to validate ('sites' or 'config')

        Returns:
            tuple: (is_valid, error_message, data)
        """
        try:
            # Check if file exists
            if not file_path.exists():
                return False, f"File does not exist: {file_path}", {}

            # Check file size (prevent loading huge files)
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                return False, "File is too large (maximum 10MB)", {}

            # Try to read and parse JSON
            try:
                with open(file_path, encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError as exc:
                return False, f"Invalid JSON format: {exc.msg} at line {exc.lineno}", {}
            except UnicodeDecodeError as exc:
                return False, f"File encoding error: {exc}", {}

            # Validate based on schema type
            if schema_type == "sites":
                return self._validate_sites_json(data)
            elif schema_type == "config":
                return self._validate_config_json(data)
            else:
                return False, f"Unknown schema type: {schema_type}", {}

        except Exception as exc:
            return False, f"Error validating JSON file: {exc}", {}

    def _validate_sites_json(self, data: dict) -> tuple[bool, str, dict]:
        """Validate sites.json structure and content"""
        # Check if data is a dictionary
        if not isinstance(data, dict):
            return False, "Root element must be a JSON object", {}

        # Check for required 'sites' key
        if "sites" not in data:
            return False, "Missing required 'sites' key", {}

        sites = data["sites"]

        # Check if sites is a list
        if not isinstance(sites, list):
            return False, "'sites' must be an array", {}

        # Check sites count limit
        if len(sites) > 100:
            return False, "Too many sites (maximum 100 allowed)", {}

        # Validate each site URL
        for i, site in enumerate(sites):
            if not isinstance(site, str):
                return False, f"Site at index {i} is not a string", {}

            # Basic URL validation (detailed validation will be done later)
            if not site.strip():
                return False, f"Site at index {i} is empty", {}

            if len(site) > 2048:
                return False, f"Site at index {i} is too long (max 2048 characters)", {}

        return True, "Sites JSON is valid", data

    def _validate_config_json(self, data: dict) -> tuple[bool, str, dict]:
        """Validate config.json structure and content"""
        # Check if data is a dictionary
        if not isinstance(data, dict):
            return False, "Root element must be a JSON object", {}

        # Validate check_interval if present
        if "check_interval" in data:
            interval = data["check_interval"]
            if not isinstance(interval, int) or interval < 60 or interval > 86400:
                return (
                    False,
                    "check_interval must be an integer between 60 and 86400 seconds",
                    {},
                )

        # Validate logging configuration if present
        if "logging" in data:
            logging_config = data["logging"]
            if not isinstance(logging_config, dict):
                return False, "logging configuration must be a JSON object", {}

            # Validate log level
            if "level" in logging_config:
                level = logging_config["level"]
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if not isinstance(level, str) or level.upper() not in valid_levels:
                    return (
                        False,
                        f"log level must be one of: {', '.join(valid_levels)}",
                        {},
                    )

            # Validate console logging flag
            if "console" in logging_config:
                console = logging_config["console"]
                if not isinstance(console, bool):
                    return False, "console logging flag must be true or false", {}

            # Validate rotation settings
            if "rotation" in logging_config:
                rotation = logging_config["rotation"]
                if not isinstance(rotation, dict):
                    return False, "rotation configuration must be a JSON object", {}

                if "max_bytes" in rotation:
                    max_bytes = rotation["max_bytes"]
                    if (
                        not isinstance(max_bytes, int)
                        or max_bytes < 1024
                        or max_bytes > 100 * 1024 * 1024
                    ):
                        return False, "max_bytes must be between 1KB and 100MB", {}

                if "backup_count" in rotation:
                    backup_count = rotation["backup_count"]
                    if (
                        not isinstance(backup_count, int)
                        or backup_count < 1
                        or backup_count > 20
                    ):
                        return False, "backup_count must be between 1 and 20", {}

        # Validate debug_mode if present (legacy support)
        if "debug_mode" in data:
            debug_mode = data["debug_mode"]
            if not isinstance(debug_mode, bool):
                return False, "debug_mode must be true or false", {}

        return True, "Config JSON is valid", data

    def safe_json_save(
        self, file_path: Path, data: dict, backup: bool = True
    ) -> tuple[bool, str]:
        """
        Safely save JSON data with backup and validation

        Args:
            file_path: Path where to save the file
            data: Data to save as JSON
            backup: Whether to create a backup of existing file

        Returns:
            tuple: (success, error_message)
        """
        try:
            # Create backup if file exists and backup is requested
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                try:
                    import shutil

                    shutil.copy2(file_path, backup_path)
                except Exception as exc:
                    logging.getLogger("onSite").warning(
                        f"Could not create backup: {exc}"
                    )

            # Write to temporary file first
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

            try:
                with open(temp_path, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=2, ensure_ascii=False)

                # Validate the temporary file
                if file_path.name == "sites.json":
                    is_valid, error, _ = self.validate_json_file(temp_path, "sites")
                elif file_path.name == "config.json":
                    is_valid, error, _ = self.validate_json_file(temp_path, "config")
                else:
                    is_valid, error = True, ""

                if not is_valid:
                    temp_path.unlink(missing_ok=True)  # Clean up temp file
                    return False, f"Generated JSON is invalid: {error}"

                # Atomic move from temp to final location
                temp_path.replace(file_path)
                return True, ""

            except Exception as exc:
                # Clean up temp file on error
                temp_path.unlink(missing_ok=True)
                raise exc

        except Exception as exc:
            return False, f"Error saving JSON file: {exc}"

    def load_sites(self):
        """Load sites from configuration file with enhanced validation"""
        if self.sites_file.exists():
            # Validate JSON file first
            is_valid, error_message, data = self.validate_json_file(
                self.sites_file, "sites"
            )

            if not is_valid:
                logging.getLogger("onSite").error(
                    f"Invalid sites.json file: {error_message}"
                )
                self.notification_manager.send_error_notification(
                    error_msg=f"Sites configuration error: {error_message}"
                )
                self.sites = []
                return

            try:
                raw_sites = data.get("sites", [])

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
                        invalid_sites.append(f"{site} - Invalid format (not a string)")

                self.sites = validated_sites

                if invalid_sites:
                    logging.getLogger("onSite").warning(
                        "Found %d invalid sites in config:", len(invalid_sites)
                    )
                    for invalid in invalid_sites:
                        logging.getLogger("onSite").warning("  - %s", invalid)

                    # Show notification about invalid sites
                    self.notification_manager.send_notification(
                        title="⚠️ Invalid Sites Found",
                        message=(f"Removed {len(invalid_sites)} " "invalid sites"),
                        subtitle="Check logs for details",
                    )

                    # Save the cleaned sites list
                    self.save_sites()

                logging.getLogger("onSite").info(
                    "Loaded %d valid sites (removed %d invalid)",
                    len(validated_sites),
                    len(invalid_sites),
                )

            except Exception as exc:
                logging.getLogger("onSite").error("Error loading sites: %s", exc)
                self.sites = []
        else:
            # Create default sites file
            self.sites = []
            self.save_sites()

    def save_sites(self):
        """Save sites to configuration file with validation"""
        try:
            data = {"sites": self.sites}

            success, error = self.safe_json_save(self.sites_file, data, backup=True)

            if success:
                logging.getLogger("onSite").info("Saved %s sites", len(self.sites))
            else:
                logging.getLogger("onSite").error(f"Error saving sites: {error}")
                self.notification_manager.send_error_notification(
                    error_msg=f"Could not save sites: {error}"
                )

        except Exception as exc:
            logging.getLogger("onSite").error("Error saving sites: %s", exc)
            self.notification_manager.send_error_notification(
                error_msg=f"Unexpected error saving sites: {exc}"
            )

    def load_config(self):
        """Load application configuration with enhanced validation"""
        if self.config_file.exists():
            # Validate JSON file first
            is_valid, error_message, config = self.validate_json_file(
                self.config_file, "config"
            )

            if not is_valid:
                # Use print before logging is setup
                print(f"Invalid config.json file: {error_message}")
                print("Using default configuration")
                # Continue with defaults
                config = {}

            try:
                self.check_interval = config.get("check_interval", 900)

                # Load logging configuration with defaults
                logging_config = config.get("logging", {})

                # Basic logging settings
                self.log_level = logging_config.get("level", "INFO").upper()
                self.log_to_console = logging_config.get("console", False)
                self.log_format = logging_config.get(
                    "format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                )
                self.log_date_format = logging_config.get(
                    "date_format", "%Y-%m-%d %H:%M:%S"
                )

                # Log rotation settings
                rotation_config = logging_config.get("rotation", {})
                self.log_max_bytes = rotation_config.get(
                    "max_bytes", 5 * 1024 * 1024
                )  # 5MB
                self.log_backup_count = rotation_config.get("backup_count", 5)

                # Module-specific log levels
                self.module_log_levels = logging_config.get("module_levels", {})

                # Legacy debug_mode support
                self.debug_mode = config.get("debug_mode", False)
                if self.debug_mode and not hasattr(self, "log_level"):
                    self.log_level = "DEBUG"

            except Exception as exc:
                # Use print before logging is setup
                print(f"Error loading config: {exc}")
                # Set defaults on error
                self.log_level = "INFO"
                self.log_to_console = False
                self.log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                self.log_date_format = "%Y-%m-%d %H:%M:%S"
                self.log_max_bytes = 5 * 1024 * 1024
                self.log_backup_count = 5
                self.module_log_levels = {}
        else:
            # Set defaults if no config file
            self.log_level = "INFO"
            self.log_to_console = False
            self.log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            self.log_date_format = "%Y-%m-%d %H:%M:%S"
            self.log_max_bytes = 5 * 1024 * 1024
            self.log_backup_count = 5
            self.module_log_levels = {}

    def save_config(self):
        """Save application configuration with validation"""
        try:
            # Build config dictionary
            config = {
                "check_interval": self.check_interval,
                "logging": {
                    "level": getattr(self, "log_level", "INFO"),
                    "console": getattr(self, "log_to_console", False),
                    "format": getattr(
                        self,
                        "log_format",
                        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    ),
                    "date_format": getattr(
                        self, "log_date_format", "%Y-%m-%d %H:%M:%S"
                    ),
                    "rotation": {
                        "max_bytes": getattr(self, "log_max_bytes", 5 * 1024 * 1024),
                        "backup_count": getattr(self, "log_backup_count", 5),
                    },
                    "module_levels": getattr(self, "module_log_levels", {}),
                },
            }

            # Keep legacy debug_mode for backward compatibility
            if hasattr(self, "debug_mode"):
                config["debug_mode"] = self.debug_mode

            success, error = self.safe_json_save(self.config_file, config, backup=True)

            if success:
                logging.getLogger("onSite").debug("Configuration saved")
            else:
                logging.getLogger("onSite").error(f"Error saving config: {error}")
                self.notification_manager.send_error_notification(
                    error_msg=f"Could not save configuration: {error}"
                )

        except Exception as exc:
            logging.getLogger("onSite").error("Error saving config: %s", exc)
            self.notification_manager.send_error_notification(
                error_msg=f"Unexpected error saving config: {exc}"
            )

    def validate_sites_file_after_edit(self):
        """Validate and reload sites file after user editing"""
        try:
            # Validate the sites file
            is_valid, error_message, data = self.validate_json_file(
                self.sites_file, "sites"
            )

            if not is_valid:
                # Show validation error to user
                error_script = f"""tell application "System Events"
    activate
    display dialog "Sites file validation failed:\\n\\n{error_message.replace('"', '\\"')}\\n\\nPlease fix the file and save again, or restore from backup." with title "Validation Error - onSite" buttons {{"OK"}} default button "OK" with icon stop
end tell"""

                try:
                    subprocess.run(["osascript", "-e", error_script], check=False)
                except Exception:
                    # Fallback notification
                    self.notification_manager.send_error_notification(
                        error_msg=f"Sites file invalid: {error_message[:100]}"
                    )

                logging.getLogger("onSite").error(
                    f"Sites file validation failed: {error_message}"
                )
                return

            # File is valid, reload sites
            old_sites_count = len(self.sites)
            self.load_sites()
            new_sites_count = len(self.sites)

            # Rebuild menu with new sites
            self.build_menu()
            self.update_status_icon()

            # Notify user of successful update
            if new_sites_count != old_sites_count:
                change_text = f"Updated: {old_sites_count} → {new_sites_count} sites"
            else:
                change_text = f"Reloaded {new_sites_count} sites"

            self.notification_manager.send_notification(
                title="✅ Sites Updated",
                message=change_text,
                subtitle="File validation successful",
            )

            logging.getLogger("onSite").info(
                f"Sites file reloaded successfully: {change_text}"
            )

        except Exception as exc:
            logging.getLogger("onSite").error(
                f"Error validating sites file after edit: {exc}"
            )
            self.notification_manager.send_error_notification(
                error_msg=f"Failed to validate edited file: {exc}"
            )


if __name__ == "__main__":
    # Check if running on macOS
    import platform
    import sys

    if platform.system() != "Darwin":
        print("This menu bar app is only supported on macOS")
        sys.exit(1)

    # Run the app
    HTTPCheckApp().run()
