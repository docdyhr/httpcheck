# httpcheck Development Plan

## Executive Summary

This document outlines the development plan for httpcheck, tracking completed work and
the active roadmap through v2.0.0.

## Current State (v1.4.3 — Released)

- **Version**: 1.4.3
- **Architecture**: Fully modular package (11 specialized modules)
- **Dependencies**: requests, httpx, tabulate, tqdm, validators, tomli (pyproject.toml)
- **Test Coverage**: 90%+ (exceeds 70% target); 387 tests, 1 skipped
- **Code Quality**: pylint 10.0/10 maintained
- **Python Floor**: 3.10+
- **Security**: pip-audit clean; no known vulnerabilities

## Completed Work

### v1.4.0 — Modular Architecture
- [x] Full package restructure: `httpcheck/` with 11 specialised modules
- [x] `cli.py` — centralised argument parser and entry point
- [x] `common.py` — shared constants, types, utilities
- [x] `tld_manager.py` — TLD validation, JSON-cached from publicsuffix.org
- [x] `file_handler.py` — file input with security validation
- [x] `site_checker.py` — HTTP request handling and retry logic
- [x] `async_site_checker.py` — async I/O via httpx
- [x] `output_formatter.py` — table/JSON/CSV output
- [x] `notification.py` — macOS/Linux system notifications
- [x] `logger.py` — centralised structured logging
- [x] `validation.py` — enhanced input validation and security
- [x] `config.py` — TOML configuration file support

### v1.4.1 — Security & Testing
- [x] Replaced pickle with JSON for TLD cache (security fix)
- [x] pip-audit clean
- [x] Enhanced input validation and injection protection
- [x] SSL certificate verification options

### v1.4.2 — Output & Request Features
- [x] JSON output format (`--output json`)
- [x] CSV output format (`--output csv`)
- [x] Custom HTTP headers (`-H` flag)
- [x] Configurable retry delay (`--retry-delay`)
- [x] SSL verification control (`--no-verify-ssl`)

### v1.4.3 — Observability & Quality
- [x] Structured logging: `--debug`, `--log-file`, `--log-json`
- [x] pytest-asyncio integration; async site checker tests
- [x] Performance benchmark suite (18 tests)
- [x] 387 tests, 90%+ coverage
- [x] PyPI published via GitHub Actions OIDC trusted publishers
- [x] Configuration file support (`~/.httpcheck.toml`)

## Active Roadmap

### v1.5.0 — Monitoring & UX (Next Release)

#### Monitoring Mode
- [ ] Continuous site monitoring with configurable intervals
- [ ] Persistent failure state across runs
- [ ] Alert thresholds (fail N times before notifying)

#### Enhanced UX
- [ ] Colorised terminal output (green/red/yellow per status class)
- [ ] Improved progress reporting for large lists
- [ ] `--summary-only` flag for batch runs

#### Configuration Improvements
- [ ] Profile support in config file (`[profiles.strict]`, etc.)
- [ ] Environment variable overrides (`HTTPCHECK_TIMEOUT`, etc.)

### v1.6.0 — Advanced Features

- [ ] Rate limiting (`--rate-limit N` requests/second)
- [ ] Content verification (check response body, not just status)
- [ ] Export to SQLite for historical trending
- [ ] Webhook notifications (POST result JSON to a URL)

### v2.0.0 — Long-term Vision

- [ ] Plugin/hook system for custom checks
- [ ] Dashboard output (terminal UI)
- [ ] Distributed checking across multiple nodes

## Quality Standards

### Invariants (never regress)
- pylint score 10.0/10
- Test coverage ≥ 70% (current: 90%+)
- pip-audit clean
- CLI interface backward-compatible
- Python 3.10+ floor

### Development Workflow
```bash
# Before each commit
source .venv/bin/activate
pylint --fail-under=10.0 httpcheck.py httpcheck/*.py
pytest tests/ -q
httpcheck google.com  # smoke test
```

### Test Strategy
- Mock all network I/O (`requests.Session.get`, `httpx.AsyncClient`)
- Use `AsyncMock` for async patches to avoid "coroutine never awaited" warnings
- Mock filesystem and notification subsystems
- Performance benchmarks run in CI to catch regressions
