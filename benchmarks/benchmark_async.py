"""Benchmark httpcheck's --async mode against a baseline release (v1.4.3).

Starts a local asyncio HTTP server that answers every request after a fixed
delay, writes a URL list spread over several ports, then runs each httpcheck
command end to end and records wall-clock time, peak RSS, and the number of
requests and TCP connections the server saw. No external sites are contacted.

Extract the baseline without touching the working tree, then run:

    mkdir -p /tmp/httpcheck-v1.4.3
    git archive v1.4.3 | tar -x -C /tmp/httpcheck-v1.4.3
    python benchmarks/benchmark_async.py --baseline /tmp/httpcheck-v1.4.3

Both trees run under the current interpreter, with HOME and the working
directory pointed at a temporary directory so no ~/.httpcheck.toml or
./.httpcheck.toml affects the result.
"""

from __future__ import annotations

import argparse
import asyncio
import http.client
import json
import math
import multiprocessing
import os
import pathlib
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Scenario:
    """One httpcheck invocation to benchmark."""

    label: str
    tree: str  # "baseline" or "current"
    mode: str  # "fast" or "async"
    workers: int


@dataclass
class Result:
    """Measurements for one scenario at one site count."""

    scenario: Scenario
    sites: int
    times: list[float] = field(default_factory=list)
    peak_rss_mb: list[float] = field(default_factory=list)
    requests: list[int] = field(default_factory=list)
    connections: list[int] = field(default_factory=list)
    exit_codes: list[int] = field(default_factory=list)


def _scenarios(workers: list[int]) -> list[Scenario]:
    """Each worker count for every command; v1.4.3 -f at 10 is the reference."""
    scenarios = [Scenario("v1.4.3 -f", "baseline", "fast", 10)]
    for count in workers:
        if count != 10:
            scenarios.append(Scenario("v1.4.3 -f", "baseline", "fast", count))
        scenarios.append(Scenario("main -f", "current", "fast", count))
        scenarios.append(Scenario("main --async", "current", "async", count))
    return scenarios


def _raise_fd_limit() -> None:
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    target = 10240 if hard == resource.RLIM_INFINITY else min(hard, 10240)
    if soft < target:
        resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))


async def _handle(reader, writer, latency: float, stats: dict) -> None:
    """Serve HTTP/1.1 keep-alive requests, each after `latency` seconds."""
    stats["connections"] += 1
    try:
        while True:
            request_line = await reader.readline()
            if not request_line:
                break
            close = False
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                if line.lower().startswith(b"connection:") and b"close" in line.lower():
                    close = True
            parts = request_line.split()
            path = parts[1] if len(parts) > 1 else b"/"
            if path == b"/__stats":
                body = json.dumps(stats).encode()
            else:
                stats["requests"] += 1
                await asyncio.sleep(latency)
                body = b"OK"
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n"
                + b"Content-Length: %d\r\n" % len(body)
                + (b"Connection: close\r\n" if close else b"")
                + b"\r\n"
                + body
            )
            await writer.drain()
            if close:
                break
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        writer.close()


def _serve(port_count: int, latency: float, queue) -> None:
    """Run the delay server on `port_count` OS-assigned loopback ports."""
    _raise_fd_limit()
    stats = {"connections": 0, "requests": 0}

    async def _run() -> None:
        servers = [
            await asyncio.start_server(
                lambda r, w: _handle(r, w, latency, stats),
                "127.0.0.1",
                0,
                backlog=4096,
            )
            for _ in range(port_count)
        ]
        queue.put([s.sockets[0].getsockname()[1] for s in servers])
        await asyncio.Event().wait()

    asyncio.run(_run())


def _server_stats(port: int) -> dict:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        conn.request("GET", "/__stats", headers={"Connection": "close"})
        return json.loads(conn.getresponse().read())
    finally:
        conn.close()


def _command(scenario: Scenario, roots: dict, url_file: pathlib.Path) -> list[str]:
    cmd = [sys.executable, str(roots[scenario.tree] / "httpcheck.py")]
    cmd += ["--timeout", "30", "--workers", str(scenario.workers)]
    cmd.append("-f" if scenario.mode == "fast" else "--async")
    cmd.append(f"@{url_file}")
    return cmd


def _run_once(cmd: list[str], workdir: pathlib.Path) -> tuple[float, float, int]:
    """Run `cmd`; return (wall seconds, peak RSS in MB, exit code)."""
    env = dict(os.environ, HOME=str(workdir))
    with open(workdir / "stdout.log", "wb") as out:
        start = time.perf_counter()
        # Popen is not used as a context manager: os.wait4 reaps the child to
        # read its own rusage, which Popen.wait() would otherwise discard.
        proc = subprocess.Popen(  # pylint: disable=consider-using-with
            cmd, cwd=workdir, env=env, stdout=out, stderr=subprocess.STDOUT
        )
        _, status, usage = os.wait4(proc.pid, 0)
        elapsed = time.perf_counter() - start
    proc.returncode = os.waitstatus_to_exitcode(status)
    # ru_maxrss is bytes on macOS and kilobytes on Linux.
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return elapsed, usage.ru_maxrss / divisor, proc.returncode


def _floor_seconds(sites: int, workers: int, latency: float) -> float:
    """Lower bound if exactly `workers` requests are always in flight."""
    return math.ceil(sites / workers) * latency


def _report(results: list[Result], latency: float, ports: int) -> str:
    lines = [
        f"Local server: {ports} ports, {latency * 1000:.0f} ms per response. "
        f"Python {sys.version.split()[0]} on {sys.platform}.",
        "",
        "| Sites | Command | Workers | Median s | Min–max s | Floor s | "
        "Speedup | Peak RSS MB | Requests | TCP conns |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    baselines = {
        r.sites: statistics.median(r.times)
        for r in results
        if r.scenario.tree == "baseline" and r.scenario.workers == 10
    }
    for r in results:
        median = statistics.median(r.times)
        speedup = baselines[r.sites] / median
        lines.append(
            f"| {r.sites} | `{r.scenario.label}` | {r.scenario.workers} "
            f"| {median:.2f} | {min(r.times):.2f}–{max(r.times):.2f} "
            f"| {_floor_seconds(r.sites, r.scenario.workers, latency):.2f} "
            f"| {speedup:.2f}× | {statistics.median(r.peak_rss_mb):.0f} "
            f"| {statistics.median(r.requests)} "
            f"| {statistics.median(r.connections)} |"
        )
    lines += [
        "",
        "Speedup is relative to `v1.4.3 -f` with its default 10 workers at the "
        "same site count. Floor is ceil(sites / workers) x latency.",
    ]
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--baseline",
        type=pathlib.Path,
        required=True,
        help="extracted baseline tree (e.g. git archive v1.4.3)",
    )
    parser.add_argument(
        "--current",
        type=pathlib.Path,
        default=REPO_ROOT,
        help="tree under test (default: this repository)",
    )
    parser.add_argument("--sites", type=int, nargs="+", default=[100, 1000])
    parser.add_argument(
        "--workers",
        type=int,
        nargs="+",
        default=[10, 50, 200],
        help="--workers values to run for every command (default: 10 50 200)",
    )
    parser.add_argument("--latency", type=float, default=0.1)
    parser.add_argument("--ports", type=int, default=10)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--json", type=pathlib.Path, help="write raw results here")
    return parser.parse_args()


def main() -> int:
    """Run every scenario at every site count and print a Markdown table."""
    args = _parse_args()
    _raise_fd_limit()
    roots = {"baseline": args.baseline.resolve(), "current": args.current.resolve()}
    for name, root in roots.items():
        if not (root / "httpcheck.py").is_file():
            print(f"error: no httpcheck.py in {name} tree {root}", file=sys.stderr)
            return 2

    queue = multiprocessing.Queue()
    server = multiprocessing.Process(
        target=_serve, args=(args.ports, args.latency, queue), daemon=True
    )
    server.start()
    ports = queue.get(timeout=30)
    results: list[Result] = []
    failed = False
    try:
        with tempfile.TemporaryDirectory(prefix="httpcheck-bench-") as tmp:
            workdir = pathlib.Path(tmp)
            for sites in args.sites:
                url_file = workdir / f"urls-{sites}.txt"
                url_file.write_text(
                    "".join(
                        f"http://127.0.0.1:{ports[i % len(ports)]}/{i}\n"
                        for i in range(sites)
                    )
                )
                for scenario in _scenarios(args.workers):
                    cmd = _command(scenario, roots, url_file)
                    _run_once(cmd, workdir)  # warm-up: imports, page cache
                    result = Result(scenario, sites)
                    for _ in range(args.runs):
                        before = _server_stats(ports[0])
                        elapsed, rss, code = _run_once(cmd, workdir)
                        after = _server_stats(ports[0])
                        result.times.append(elapsed)
                        result.peak_rss_mb.append(rss)
                        result.exit_codes.append(code)
                        result.requests.append(after["requests"] - before["requests"])
                        # The "after" stats call opens one connection itself.
                        result.connections.append(
                            after["connections"] - before["connections"] - 1
                        )
                    if any(result.exit_codes) or any(
                        n != sites for n in result.requests
                    ):
                        failed = True
                        print(
                            f"WARNING: {scenario.label} w={scenario.workers} "
                            f"n={sites}: exit codes {result.exit_codes}, "
                            f"requests {result.requests}",
                            file=sys.stderr,
                        )
                    print(
                        f"{sites:>5} {scenario.label:<14} w={scenario.workers:<4} "
                        f"median {statistics.median(result.times):6.2f}s",
                        file=sys.stderr,
                    )
                    results.append(result)
    finally:
        server.terminate()

    print(_report(results, args.latency, args.ports))
    if args.json:
        args.json.write_text(json.dumps([asdict(r) for r in results], indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
