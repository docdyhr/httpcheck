"""Output formatting for httpcheck results."""

import csv
import io
import json
from typing import List

from tabulate import tabulate

from .common import STATUS_CODES, SiteStatus


def print_format(
    result: SiteStatus,
    quiet: bool,
    verbose: bool,
    code: bool,
    *,
    show_redirect_timing: bool = False,
    output_format: str = "table",
):
    """Format & print results in columns.

    Args:
        result: SiteStatus object with check results
        quiet: Only show errors
        verbose: Show detailed output
        code: Only show status code
        show_redirect_timing: Include timing for redirects
        output_format: Output format (table, json, csv)

    Returns:
        Formatted output string
    """
    output = ""

    # Handle JSON format
    if output_format == "json":
        return format_json(result, verbose)

    # Handle CSV format
    elif output_format == "csv":
        return format_csv(result, verbose)

    # Handle table formats
    elif code:
        output = result.status
    elif verbose:
        headers = ["Domain", "Status", "Response Time", "Message"]
        table_data = [
            [
                result.domain,
                result.status,
                f"{result.response_time:.2f}s",
                STATUS_CODES.get(str(result.status), "Unknown"),
            ]
        ]

        output = tabulate(table_data, headers=headers, tablefmt="grid")

        if result.redirect_chain:
            output += "\nRedirect Chain:\n"
            if show_redirect_timing and result.redirect_timing:
                timing_data = []
                for i, (url, status_code, response_time) in enumerate(
                    result.redirect_timing
                ):
                    time_str = f"{response_time:.3f}s" if response_time > 0 else "–"
                    timing_data.append([i + 1, url, status_code, time_str])
                output += tabulate(
                    timing_data,
                    headers=["Step", "URL", "Status", "Time"],
                    tablefmt="grid",
                )
            else:
                redirect_data = [
                    [i + 1, url, code]
                    for i, (url, code) in enumerate(result.redirect_chain)
                ]
                output += tabulate(
                    redirect_data,
                    headers=["Step", "URL", "Status"],
                    tablefmt="grid",
                )
    elif quiet:
        if (
            result.status in ("[timeout]", "[connection error]")
            or int(result.status) >= 400
        ):
            output = f"{result.domain} {result.status}"
    else:
        output = tabulate([[result.domain, result.status]], tablefmt="simple")

    return output


def format_json(result: SiteStatus, verbose: bool = False) -> str:
    """Format result as JSON.

    Args:
        result: SiteStatus object with check results
        verbose: Include extra details

    Returns:
        JSON formatted string
    """
    data = {
        "domain": result.domain,
        "status": result.status,
        "message": result.message,
        "response_time": round(result.response_time, 3),
    }

    if verbose:
        data["redirect_chain"] = (
            [{"url": url, "status": status} for url, status in result.redirect_chain]
            if result.redirect_chain
            else []
        )

        data["redirect_timing"] = (
            [
                {"url": url, "status": status, "time": round(time, 3)}
                for url, status, time in result.redirect_timing
            ]
            if result.redirect_timing
            else []
        )

    return json.dumps(data, indent=2)


def format_csv(result: SiteStatus, verbose: bool = False) -> str:
    """Format result as CSV.

    Args:
        result: SiteStatus object with check results
        verbose: Include extra details

    Returns:
        CSV formatted string
    """
    output = io.StringIO()

    if verbose:
        # Verbose CSV includes redirect information
        fieldnames = [
            "domain",
            "status",
            "message",
            "response_time",
            "redirect_count",
            "final_url",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write data row
        writer.writerow(
            {
                "domain": result.domain,
                "status": result.status,
                "message": result.message,
                "response_time": round(result.response_time, 3),
                "redirect_count": (
                    len(result.redirect_chain) if result.redirect_chain else 0
                ),
                "final_url": (
                    result.final_url if result.redirect_chain else result.domain
                ),
            }
        )
    else:
        # Simple CSV with basic info
        fieldnames = ["domain", "status", "response_time"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write data row
        writer.writerow(
            {
                "domain": result.domain,
                "status": result.status,
                "response_time": round(result.response_time, 3),
            }
        )

    return output.getvalue().strip()


def format_json_list(results: list[SiteStatus], verbose: bool = False) -> str:
    """Format multiple results as JSON array.

    Args:
        results: List of SiteStatus objects
        verbose: Include extra details

    Returns:
        JSON formatted string
    """
    data = []
    for result in results:
        item = {
            "domain": result.domain,
            "status": result.status,
            "message": result.message,
            "response_time": round(result.response_time, 3),
        }

        if verbose:
            item["redirect_chain"] = (
                [
                    {"url": url, "status": status}
                    for url, status in result.redirect_chain
                ]
                if result.redirect_chain
                else []
            )

            item["redirect_timing"] = (
                [
                    {"url": url, "status": status, "time": round(time, 3)}
                    for url, status, time in result.redirect_timing
                ]
                if result.redirect_timing
                else []
            )

        data.append(item)

    return json.dumps(data, indent=2)


def format_csv_list(results: list[SiteStatus], verbose: bool = False) -> str:
    """Format multiple results as CSV.

    Args:
        results: List of SiteStatus objects
        verbose: Include extra details

    Returns:
        CSV formatted string
    """
    if not results:
        return ""

    output = io.StringIO()

    if verbose:
        fieldnames = [
            "domain",
            "status",
            "message",
            "response_time",
            "redirect_count",
            "final_url",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    "domain": result.domain,
                    "status": result.status,
                    "message": result.message,
                    "response_time": round(result.response_time, 3),
                    "redirect_count": (
                        len(result.redirect_chain) if result.redirect_chain else 0
                    ),
                    "final_url": (
                        result.final_url if result.redirect_chain else result.domain
                    ),
                }
            )
    else:
        fieldnames = ["domain", "status", "response_time"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    "domain": result.domain,
                    "status": result.status,
                    "response_time": round(result.response_time, 3),
                }
            )

    return output.getvalue().strip()
