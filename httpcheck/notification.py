"""System notifications for httpcheck."""

import platform
import subprocess


def notify(title, message, failed_sites=None):
    """Send system notification using osascript on macOS."""
    if platform.system() == "Darwin":  # macOS only
        try:
            notification_message = message
            subtitle = ""
            if failed_sites:
                # Use subtitle for summary, keep message concise
                subtitle = message  # Original summary message
                if len(failed_sites) < 10:
                    failed_list = "\n".join(f"• {site}" for site in failed_sites)
                    notification_message = f"Failed sites:\n{failed_list}"
                else:
                    notification_message = (
                        f"{len(failed_sites)} sites failed. See terminal for details."
                    )

            # Construct the AppleScript command with proper escaping
            escaped_message = notification_message.replace('"', '\\"').replace(
                "\n", "\\n"
            )
            escaped_title = title.replace('"', '\\"')
            escaped_subtitle = subtitle.replace('"', '\\"')

            script = (
                f'display notification "{escaped_message}" '
                f'with title "{escaped_title}" '
                f'subtitle "{escaped_subtitle}"'
            )
            cmd = ["osascript", "-e", script]

            # Execute the command
            subprocess.run(cmd, check=True, capture_output=True)

        except FileNotFoundError:
            # This should generally not happen on macOS as osascript is standard
            print("\nWarning: 'osascript' command not found. Cannot send notification.")
        except subprocess.CalledProcessError as e:
            # Handle errors from osascript execution
            print(
                f"\nWarning: Could not send notification using osascript: {e.stderr.decode()}"
            )
        except Exception as e:
            # Catch any other unexpected errors
            print(
                f"\nWarning: An unexpected error occurred during notification: {str(e)}"
            )
