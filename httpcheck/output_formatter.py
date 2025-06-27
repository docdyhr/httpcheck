"""Output formatting for httpcheck results."""

from tabulate import tabulate

from .common import STATUS_CODES, SiteStatus


def print_format(
    result: SiteStatus,
    quiet: bool,
    verbose: bool,
    code: bool,
    show_redirect_timing: bool = False,
):
    """Format & print results in columns."""
    output = ""
    if code:
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
