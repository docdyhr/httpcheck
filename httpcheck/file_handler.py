"""File input handling and URL validation for httpcheck."""

import argparse
import re


def url_validation(site_url):
    """Check if url is valid and return it."""
    site_url = site_url if site_url.startswith("http") else f"http://{site_url}"
    # check url with regex
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        #  domain
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if re.match(regex, site_url) is not None:
        return site_url
    msg = f"[-] Invalid URL: '{site_url}'"
    raise argparse.ArgumentTypeError(msg)


class FileInputHandler:
    """Handles input from domain files with enhanced features.

    Features:
    - Strips whitespace and handles empty lines
    - Supports multiple comment formats (# and //)
    - Handles inline comments
    - Performs input validation
    - Gracefully handles malformed lines
    """

    def __init__(self, file_path, verbose=False, comment_style="both"):
        """Initialize with file path and verbosity setting.

        Args:
            file_path: Path to the file to parse
            verbose: Whether to print verbose output
            comment_style: Which comment style to recognize ('hash', 'slash', or 'both')
        """
        self.file_path = file_path
        self.verbose = verbose
        self.comment_style = comment_style
        self.line_count = 0
        self.valid_count = 0
        self.comment_count = 0
        self.empty_count = 0
        self.error_count = 0

        # Set up comment markers based on style preference
        self.comment_markers = []
        if comment_style in ("hash", "both"):
            self.comment_markers.append("#")
        if comment_style in ("slash", "both"):
            self.comment_markers.append("//")

    def parse(self):
        """Parse the input file and yield valid URLs."""
        try:
            with open(self.file_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    self.line_count += 1
                    result = self._process_line(line, line_num)
                    if result:
                        yield result

            if self.verbose:
                summary = (
                    f"\nFile: {self.file_path}\n"
                    f"  Lines processed: {self.line_count}\n"
                    f"  Valid URLs: {self.valid_count}\n"
                    f"  Comments: {self.comment_count}\n"
                    f"  Empty lines: {self.empty_count}\n"
                    f"  Errors: {self.error_count}\n"
                )
                print(summary)
        except OSError as e:
            print(f"[-] Error reading file {self.file_path}: {str(e)}")

    def _process_line(self, line, line_num):
        """Process a single line from the input file."""
        # Remove whitespace
        line = line.strip()

        # Handle empty lines
        if not line:
            self.empty_count += 1
            return None

        # Handle comments based on configured comment style
        for marker in self.comment_markers:
            if line.startswith(marker):
                self.comment_count += 1
                return None

        # Handle inline comments based on configured comment style
        comment_pos = -1
        for marker in self.comment_markers:
            pos = line.find(marker)
            if pos > 0 and (comment_pos == -1 or pos < comment_pos):
                comment_pos = pos

        if comment_pos > 0:
            line = line[:comment_pos].strip()
            self.comment_count += 1

        # Skip if the line became empty after removing the comment
        if not line:
            self.empty_count += 1
            return None

        # Apply URL validation
        try:
            validated_url = url_validation(line)
            self.valid_count += 1
            return validated_url
        except argparse.ArgumentTypeError as e:
            error_msg = f"[-] Line {line_num}: {str(e)}"
            if self.verbose:
                print(error_msg)
            self.error_count += 1
            return None
