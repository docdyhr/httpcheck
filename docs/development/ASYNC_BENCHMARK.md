# Async benchmark: `--async` vs v1.4.3

Run on 2026-10-14 against `main` plus the `--async` crash fix (`fix/async-max-redirects`).
This is the v1.5.0 roadmap task "Benchmark against v1.4.3 (target: 2–3× improvement for
100+ checks)".

## Result

**The target is not met.** At default settings, `--async` runs at the same speed as
v1.4.3's threaded `-f` (0.98×). Raising `--workers` speeds up both modes, and threads
benefit at least as much as async. Above about 50 workers, `--async` gets slower as
workers increase, while `-f` keeps scaling:

| 1,000 sites | v1.4.3 `-f` | `main --async` |
|---|---:|---:|
| `--workers 10` (default) | 10.95 s | 11.14 s |
| `--workers 50` | 2.50 s | 2.85 s |
| `--workers 200` | 1.03 s | 4.77 s |
| `--workers 1000` | 0.88 s | 9.80 s |

The cause is CPU time in httpcore's connection pool, not network I/O. See
[Why async stops scaling](#why-async-stops-scaling).

## Method

`benchmarks/benchmark_async.py` starts a local asyncio HTTP server on 10 loopback ports.
The server answers every request with `200 OK` after a fixed 100 ms delay. The harness
writes a URL list spread across those ports and runs each command end to end through
`httpcheck.py`, so CLI start-up is included. For each command it records the wall-clock
time and peak RSS of the child process, and the number of requests and TCP connections
the server saw. Each command gets one untimed warm-up run, then 3 timed runs; the tables
show the median.

A run only counts if httpcheck exits 0 and the server saw exactly one request per site.
That check caught the `--async` crash: before the fix every async run "finished" in
0.18 s with zero requests served.

Both trees run under the same interpreter, with `HOME` and the working directory set to
a temporary directory so no `~/.httpcheck.toml` or `./.httpcheck.toml` applies. The
baseline is `git archive v1.4.3`.

Reproduce:

```bash
mkdir -p /tmp/httpcheck-v1.4.3
git archive v1.4.3 | tar -x -C /tmp/httpcheck-v1.4.3
python benchmarks/benchmark_async.py --baseline /tmp/httpcheck-v1.4.3
python benchmarks/benchmark_async.py --baseline /tmp/httpcheck-v1.4.3 --sites 1000 --workers 1000
```

Environment: Apple M3 Max (14 cores, 36 GB), macOS 27.2, Python 3.14.4, httpx 0.28.1,
httpcore 1.0.9, anyio 4.13.0, requests 2.33.1, urllib3 2.6.3.

## Full results

Local server: 10 ports, 100 ms per response. Speedup is relative to `v1.4.3 -f` at its
default 10 workers, at the same site count. Floor is `ceil(sites / workers) × 100 ms`,
the best possible time with exactly `workers` requests in flight.

| Sites | Command | Workers | Median s | Min–max s | Floor s | Speedup | Peak RSS MB | Requests | TCP conns |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | `v1.4.3 -f` | 10 | 1.33 | 1.33–1.39 | 1.00 | 1.00× | 43 | 100 | 100 |
| 100 | `main -f` | 10 | 1.41 | 1.34–1.42 | 1.00 | 0.94× | 46 | 100 | 100 |
| 100 | `main --async` | 10 | 1.37 | 1.36–1.38 | 1.00 | 0.98× | 50 | 100 | 10 |
| 100 | `v1.4.3 -f` | 50 | 0.57 | 0.53–0.64 | 0.20 | 2.33× | 47 | 100 | 100 |
| 100 | `main -f` | 50 | 0.53 | 0.53–0.57 | 0.20 | 2.49× | 50 | 100 | 100 |
| 100 | `main --async` | 50 | 0.55 | 0.54–0.56 | 0.20 | 2.44× | 51 | 100 | 100 |
| 100 | `v1.4.3 -f` | 200 | 0.54 | 0.50–0.63 | 0.10 | 2.48× | 51 | 100 | 100 |
| 100 | `main -f` | 200 | 0.42 | 0.42–0.46 | 0.10 | 3.15× | 54 | 100 | 100 |
| 100 | `main --async` | 200 | 0.58 | 0.57–0.59 | 0.10 | 2.30× | 51 | 100 | 100 |
| 1000 | `v1.4.3 -f` | 10 | 10.95 | 10.89–10.98 | 10.00 | 1.00× | 45 | 1000 | 1000 |
| 1000 | `main -f` | 10 | 10.90 | 10.85–10.97 | 10.00 | 1.00× | 48 | 1000 | 1000 |
| 1000 | `main --async` | 10 | 11.14 | 10.97–11.22 | 10.00 | 0.98× | 55 | 1000 | 10 |
| 1000 | `v1.4.3 -f` | 50 | 2.50 | 2.49–2.51 | 2.00 | 4.38× | 49 | 1000 | 1000 |
| 1000 | `main -f` | 50 | 2.51 | 2.50–2.58 | 2.00 | 4.36× | 52 | 1000 | 1000 |
| 1000 | `main --async` | 50 | 2.85 | 2.76–2.85 | 2.00 | 3.84× | 55 | 1000 | 990 |
| 1000 | `v1.4.3 -f` | 200 | 1.03 | 0.97–1.03 | 0.50 | 10.65× | 63 | 1000 | 1000 |
| 1000 | `main -f` | 200 | 1.03 | 0.98–2.05 | 0.50 | 10.64× | 67 | 1000 | 1000 |
| 1000 | `main --async` | 200 | 4.77 | 4.76–4.86 | 0.50 | 2.29× | 56 | 1000 | 1000 |
| 1000 | `v1.4.3 -f` | 1000 | 0.88 | 0.87–1.04 | 0.10 | 12.69×¹ | 73 | 1000 | 1000 |
| 1000 | `main -f` | 1000 | 0.90 | 0.89–0.90 | 0.10 | 12.52×¹ | 76 | 1000 | 1000 |
| 1000 | `main --async` | 1000 | 9.80 | 9.79–9.99 | 0.10 | 1.14×¹ | 64 | 1000 | 1000 |

¹ From a separate run (`--sites 1000 --workers 1000`), where the `v1.4.3 -f` reference
at 10 workers measured 11.22 s.

CLI start-up (`httpcheck.py --version`, hyperfine, 15 runs): `main` 125.9 ± 2.5 ms,
v1.4.3 111.8 ± 2.6 ms. Under `python -X importtime`, about 6 ms of the difference is
`cli.py` importing `async_site_checker` (and with it httpx) even when `--async` isn't
used, and about 1 ms is the TOML config loader.

## Observations

- **Concurrency sets the speed, not the I/O model.** At equal `--workers`, all three
  commands sit near the floor up to 50 workers. Neither mode can beat
  `ceil(sites / workers) × latency`, and the default is 10 workers for both.
- **Async reuses connections; threads don't.** At 10 workers, `--async` served 1,000
  requests over 10 TCP connections, while `-f` opened one per request. On loopback that
  costs nothing. On a real network it saves a TCP and TLS handshake per request, but
  only when many URLs share a host. That isn't measured here.
- **Async's keep-alive pool is smaller than its connection pool.** `DEFAULT_LIMITS`
  is `max_connections=50, max_keepalive_connections=20`, so at 50 workers 30
  connections are closed after each request (990 connections for 1,000 requests).
- **Memory is not a constraint for either mode.** Peak RSS stays between 43 and 76 MB
  even with 1,000 threads, under the "<100 MB for 1,000 concurrent checks" metric.

## Why async stops scaling

The obvious suspect was the fixed pool size (50). A diagnostic run called
`async_check_sites` directly on 1,000 sites, comparing the default pool against pools
sized to the worker count:

| Workers | Pool 50/20 (default) | Pool 50/50 | Pool sized to workers |
|---:|---:|---:|---:|
| 50 | 2.61 s | 2.39 s | 2.30 s |
| 200 | 4.43 s | 4.56 s | 10.15 s |
| 1000 | 9.49 s | 9.50 s | 16.58 s |

A larger pool makes it worse, so the cap isn't the bottleneck. A cProfile run at 1,000
in flight (pool sized to match) used 28.1 s of CPU in 29.7 s of wall time. 28.2 s of
that was inside `httpcore/_async/connection_pool.py:_assign_requests_to_connections`,
which called `connection.is_idle()` 94 million times over 2,000 calls. Each time a
request is queued or a connection is released, the pool scans its connections for
every queued request, so the work grows with the square of the number of requests in
flight. At 50 in flight that pass costs 1.5 s of a 3.7 s run. At 1,000 it is almost
the entire run.

So `--async` is bounded by Python CPU time in httpcore's pool scheduler, and adding
workers past about 50 makes it slower. The threaded path, which uses requests and
urllib3, has no shared scheduler of that kind.

## Limitations

- Loopback and plain HTTP only: no DNS, TLS or real network variance. Real-network
  runs would need many hosts to mean anything, and loading third-party sites for a
  benchmark isn't appropriate.
- One fixed latency (100 ms). Slower responses keep more requests in flight for the
  same throughput, which makes the pool-scheduling cost bite at lower worker counts.
- One machine and one Python version.

## Options for v1.5.0

**Decision (2026-10-14): option 1.** `--async` ships as experimental; its `--help`
text says it is not faster than `--fast`. Option 2 remains open for a later release.

1. Ship `--async` as experimental, without a speed claim, and document that `-f
   --workers N` is the faster path today.
2. Rework the async path first, for example: keep in-flight requests per client small
   (one client per host, or several sharded clients), size keep-alive to match the
   connection limit, or evaluate aiohttp. Then re-run this benchmark.
3. Leave `--async` out of v1.5.0 and ship configuration files alone.
