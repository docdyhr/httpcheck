# httpcheck Development Plan

## Executive Summary

This document outlines the development plan for httpcheck, tracking completed work and
the active roadmap through v2.0.0. [ROADMAP.md](../../ROADMAP.md) is the canonical,
prioritised feature list; this file summarises it.

## Current State (`main`, 2026-10-10)

- **Released**: 1.4.3 (2026-03-09, PyPI)
- **Unreleased on `main`**: async I/O (`--async`) and configuration files — shipping as
  v1.5.0 (target October 2026)
- **Architecture**: 11 specialized modules plus `__init__.py`
- **Dependencies**: requests, httpx, tabulate, tqdm, validators, tomli on Python 3.10
  (pyproject.toml)
- **Tests**: 388 tests (387 passed, 1 skipped), 90% coverage (exceeds 70% target)
- **Code Quality**: pylint 10.0/10 maintained
- **Python Floor**: 3.10+ on `main` (1.4.3 still supports 3.9); CI tests 3.10–3.14
- **Security**: pip-audit clean; no known vulnerabilities

## Completed Work

Per release, as recorded in [CHANGELOG.md](../../CHANGELOG.md).

### v1.4.0 — Modular Architecture (2025-01-16)
- [x] 1,151-line monolith split into the `httpcheck/` package (8 modules incl. `__init__.py`)
- [x] `common.py` — shared constants, types, utilities
- [x] `tld_manager.py` — TLD validation, JSON-cached from publicsuffix.org (replaced pickle)
- [x] `file_handler.py` — file input with security validation
- [x] `site_checker.py` — HTTP request handling and retry logic
- [x] `output_formatter.py` — table/JSON/CSV output (`--output json|csv`)
- [x] `notification.py` — macOS/Linux system notifications
- [x] `validation.py` — enhanced input validation, injection protection, DoS limits
- [x] Custom HTTP headers (`-H`) and SSL verification control (`--no-verify-ssl`)
- [x] 182 tests, 84% coverage

### v1.4.1 — Security & CLI Module (2025-01-12)
- [x] `requests` and `urllib3` security updates
- [x] `cli.py` — centralised argument parser and entry point (replaces the subprocess call)
- [x] mypy configuration in `pyproject.toml`

### v1.4.2 — Logging, Testing & Documentation (2026-01-08)
- [x] `logger.py` — structured logging: `--debug`, `--log-file`, `--log-json`
- [x] 297 tests, 88% coverage (CLI 94%); performance benchmark suite (18 tests)
- [x] Sphinx documentation: installation, quickstart, usage, examples, API reference,
  contributing

### v1.4.3 — PyPI Republish (2026-03-09)
- [x] Republished to PyPI via GitHub Actions OIDC trusted publishing
- [x] CI/CD fixes: manual dispatch support, scoped security scanning

Also in v1.4.x: configurable retry delay (`--retry-delay`).

### Unreleased on `main` — v1.5.0
- [x] `async_site_checker.py` — async I/O via httpx (`--async`), with pytest-asyncio tests
- [x] `config.py` — TOML configuration files (`~/.httpcheck.toml`, `./.httpcheck.toml`)
- [x] Python 3.13 and 3.14 added; Python 3.9 dropped (`requires-python >=3.10`)
- [ ] Benchmark async against v1.4.3, then release

## Active Roadmap

Summary of [ROADMAP.md](../../ROADMAP.md):

- **v1.5.0 — Async I/O & Configuration (target October 2026)**: both features are done;
  remaining are the async benchmark and the release itself.
- **v1.6.0 — Monitoring Mode & Enhanced Output (target Q1 2027)**: monitoring mode
  (moved from v1.5.0, not started) — continuous checks with persisted state, alert
  thresholds, webhook/email alerts, console dashboard; config profiles and env-var
  overrides; colorised output, progress reporting, `--summary-only`; HTML/Markdown
  reports; authentication; rate limiting; content verification.
- **v1.7.0 — Integrations (target Q2 2027)**: Prometheus metrics, templated webhooks,
  SQLite/PostgreSQL storage, Slack/Discord alerts.
- **v2.0.0 — Next Generation Platform (2027)**: browser-based validation, plugin
  architecture, distributed checking, enterprise features.

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
