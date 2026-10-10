# Todo list for httpcheck

## 🚀 PROJECT STATUS OVERVIEW

**Current Version**: 1.4.3 (Released 2026-03-09 ✅)
**Target Version**: 1.5.0 (Async I/O & Configuration, target October 2026)
**Project Health**: ✅ Excellent

- **Test Coverage**: 90% (Target: 70% ✅)
- **CLI Coverage**: 96% ✅
- **Code Quality**: pylint 10.0/10 ✅
- **Security**: No vulnerabilities (pip-audit clean) ✅
- **Architecture**: 11 specialized modules plus `__init__.py` ✅
- **Release Status**: PyPI 1.4.3; async I/O and config files are merged on `main`, unreleased

[ROADMAP.md](ROADMAP.md) is the canonical list of version targets and features;
this file tracks the actionable tasks.

---

## ✅ COMPLETED (v1.4.x through 1.4.3 - March 2026)

### Major Achievements

- [x] **Architecture**: Monolith split into the `httpcheck/` package in v1.4.0
  (1,151 → 807 lines, 8 modules); `cli.py` (v1.4.1) and `logger.py` (v1.4.2) followed
- [x] **Testing**: 182 tests / 84% coverage (v1.4.0) → 297 tests / 88% coverage,
  CLI 94% (v1.4.2), plus 18 performance benchmarks
- [x] **Security**: Enterprise-grade input validation system; TLD cache moved
  from pickle to JSON
- [x] **Features**: JSON/CSV output, custom headers, SSL control, retry delay,
  structured logging (`--debug`, `--log-file`, `--log-json`)
- [x] **Package**: Proper Python package, published to PyPI via GitHub Actions
  trusted publishing
- [x] **Documentation**: Sphinx docs (installation, quickstart, usage, examples,
  API reference, contributing)
- [x] **Compatibility**: 100% backward compatible

### CI/CD Pipeline

- [x] **GitHub Actions workflow** (`.github/workflows/ci.yml`) on push, PR and a
  weekly schedule:
  - pylint (must score 10.0) and pytest with coverage
  - pip-audit, bandit and CodeQL security scans
  - Test matrix: Python 3.10–3.14 on Ubuntu, macOS and Windows
- [x] **Automated release process** - Tag-based releases to PyPI (`publish.yml`)
- [x] **Dependency updates** - Dependabot, with patch bumps auto-merged
  - _Release workflow docs: `docs/release_process.md`; Dependabot rules: `.github/dependabot.yml`._

---

## 🎯 IMMEDIATE PRIORITIES

### 1. Ship v1.5.0 (async I/O + config files) — target October 2026

- [ ] **Async benchmark** - Compare `--async` against v1.4.3 (target: ≥2× faster
  for 100+ concurrent checks)
- [ ] **Release** - Follow `docs/release_process.md`; CHANGELOG `[Unreleased]`
  becomes `[1.5.0]`. Note: v1.5.0 drops Python 3.9 (`requires-python >=3.10`)

### 2. Start v1.6.0 monitoring mode — target Q1 2027

- [ ] **Design** - CLI shape, state storage and alerting for `httpcheck monitor`
  (task list under v1.6.0 below)

### 3. Documentation

- [x] **API documentation** - `docs/api/` (Sphinx autodoc)
- [x] **Real-world examples** - `docs/examples.rst` (15+ examples)
- [ ] **Migration guide** - For users wanting to use modular imports
  - _Draft issue text: `docs/github_issue_drafts.md` §3._
- [ ] **Video tutorial** - 5-minute quickstart guide

---

## 🚀 v1.5.0 DEVELOPMENT — Async I/O & Configuration (target October 2026)

### ✅ Phase 1: Async I/O Implementation (COMPLETED)

**Goal**: 2-3x performance improvement for concurrent checks

- [x] **Research & Design**
  - [x] Evaluate aiohttp vs httpx for async HTTP (chose httpx)
  - [x] Design backward-compatible async interface
  - [x] Plan migration strategy for existing threaded code

- [x] **Core Implementation**
  - [x] Create `async_site_checker.py` module
  - [x] Implement async version of check_site()
  - [x] Add connection pooling and keep-alive
  - [x] Maintain synchronous wrapper for compatibility

- [x] **Testing**
  - [x] Add async-specific test suite (`test_async_site_checker.py`)
- [ ] **Benchmarking**
  - [ ] Benchmark against v1.4.3 (target: 2-3x improvement)
  - [ ] Test with 1000+ concurrent checks
  - [ ] Memory usage profiling

### ✅ Phase 2: Configuration System (COMPLETED)

**Goal**: User-friendly defaults and enterprise configuration

- [x] **Configuration File Support** (`config.py`)

  ```toml
  # ~/.httpcheck.toml or ./.httpcheck.toml
  [defaults]
  timeout = 5.0
  retries = 2
  follow_redirects = "always"
  output_format = "table"
  verify_ssl = true

  [headers]
  User-Agent = "httpcheck/1.5.0"
  Accept = "text/html,application/json"

  [notifications]
  enabled = true
  on_failure = true
  sound = "Ping"
  ```

- [x] **Implementation Tasks**
  - [x] Create `config.py` module
  - [x] TOML format (stdlib `tomllib`; `tomli` on Python 3.10)
  - [x] Config file discovery: home (`~/.httpcheck.toml`) and cwd (`./.httpcheck.toml`)
  - [x] CLI overrides config file settings
  - _Moved to v1.6.0: YAML/JSON formats, env-var discovery, `httpcheck config` command._

> Phase 3 (Monitoring Mode) moved to v1.6.0 on 2026-10-10 so the finished async
> and config work can ship as v1.5.0.

### 📊 v1.5.0 Success Metrics

- [ ] **Async performance**: ≥2× faster for 100+ concurrent checks (stretch: 3×)
- [ ] **Memory efficiency**: <100MB for 1000 concurrent checks
- [ ] **Startup time**: <100ms with config file
- [ ] **Response time**: P95 < 50ms for local cache hits
- [ ] **Test coverage**: Maintain >80% (90% on `main`, 2026-10-10)
- [ ] **Pylint score**: Maintain 10.0/10
- [ ] **Documentation**: 100% public API documented
- [x] **Examples**: 10+ real-world usage examples (`docs/examples.rst`)
- [ ] **Config adoption**: 50% of users create config file
- [ ] **Zero regressions**: All v1.4.x features work unchanged

---

## 🔭 v1.6.0 DEVELOPMENT — Monitoring Mode & Enhanced Output (target Q1 2027)

### Monitoring Mode (moved from v1.5.0 — not started)

**Goal**: Transform httpcheck into a lightweight monitoring solution

- [ ] **Basic Monitoring**

  ```bash
  httpcheck monitor @sites.txt --interval 300 --alert-on-change
  ```

  - [ ] Continuous checking loop
  - [ ] State tracking (status changes), persisted across runs
  - [ ] Basic SQLite storage for history
  - [ ] Console dashboard view

- [ ] **Alerting System**
  - [ ] Email notifications (SMTP)
  - [ ] Webhook support (POST to URL)
  - [ ] Desktop notifications enhancement
  - [ ] Alert thresholds (fail N times before notifying)
  - _Slack/Discord delivery is a v1.7.0 Integrations item (see ROADMAP.md)._

- **Success metrics**: monitor mode stable for 24h+ continuous runs; used in 5+
  production environments

### Configuration Improvements (moved from v1.5.0)

- [ ] YAML/JSON config formats
- [ ] Config file discovery via environment variable
- [ ] `httpcheck config` command to manage settings
- [ ] Config profiles (`[profiles.strict]`) and env-var overrides (`HTTPCHECK_TIMEOUT`)

Colorized output, HTML/Markdown reports, authentication, content verification and
the rest of v1.6.0 are listed in [ROADMAP.md](ROADMAP.md).

---

## 🔮 FUTURE IDEAS (beyond v1.6.0)

Version placement and targets are canonical in [ROADMAP.md](ROADMAP.md)
(v1.7.0 Integrations: Q2 2027; v2.0.0: 2027). This is the longer idea backlog.

- [ ] **Advanced monitoring features**
  - Response time tracking and alerts
  - Content validation (regex, XPath, JSON path)
  - SSL certificate expiration monitoring
  - Custom health check endpoints

- [ ] **Dashboard and reporting**
  - Web-based dashboard (FastAPI)
  - Historical trend analysis
  - SLA reporting
  - Export to Prometheus/Grafana

- [ ] **Multi-region monitoring**
  - Distributed checking from multiple locations
  - Consensus-based alerting
  - Geographic performance analysis

- [ ] **Plugin system**
  - Custom validators
  - External notification providers
  - Authentication plugins (OAuth, API keys)

- [ ] **Browser-based validation**
  - Headless browser support (Playwright)
  - JavaScript execution
  - Screenshot on failure
  - Performance metrics (Core Web Vitals)

- [ ] **AI-powered features**
  - Anomaly detection
  - Predictive failure analysis
  - Intelligent retry strategies
  - Auto-remediation suggestions

---

## 🛠️ TECHNICAL DEBT

### Code Quality Improvements

- [ ] **Type hints**: Add comprehensive type annotations (about half of the
  functions in `httpcheck/` have return annotations)
- [ ] **Docstrings**: Add examples to all public functions
- [ ] **Error messages**: Standardize and improve clarity
- [x] **Logging**: Debug logging throughout (`logger.py`, `--debug`, v1.4.2)

### Testing Enhancements

- [ ] **Integration tests**: Real HTTP calls to test server
- [x] **Performance tests**: Regression testing for speed
  (`tests/test_performance.py`, pytest-benchmark)
- [x] **Cross-platform**: Automated Windows testing (CI matrix includes `windows-latest`)
- [ ] **Fuzzing**: Security-focused input fuzzing

### Documentation

- [ ] **Architecture guide**: Explain module interactions
- [x] **Contributing guide**: Help new contributors (`docs/contributing.rst`)
- [ ] **Troubleshooting guide**: Common issues and solutions
- [ ] **Performance tuning**: Best practices for large deployments

---

## 📋 DEVELOPMENT NOTES

### Current Architecture (`main`)

``` diagram
httpcheck/
├── __init__.py             # Package API
├── cli.py                  # Argument parser and entry point
├── common.py               # Shared utilities
├── config.py               # TOML config file loading (unreleased, v1.5.0)
├── tld_manager.py          # TLD validation (Singleton)
├── file_handler.py         # File input processing
├── site_checker.py         # HTTP checking logic (threaded)
├── async_site_checker.py   # Async I/O checks (httpx; unreleased, v1.5.0)
├── output_formatter.py     # Multiple output formats
├── notification.py         # System notifications
├── logger.py               # Centralized logging
└── validation.py           # Security validation
```

### Design Principles

1. **Backward Compatibility**: Never break existing CLI usage
2. **Security First**: Validate all inputs thoroughly
3. **Performance**: Optimize for large-scale usage
4. **Simplicity**: Keep core functionality simple
5. **Extensibility**: Enable advanced features without complexity

### Development Workflow

1. Create feature branch from `main`
2. Write tests first (TDD approach)
3. Implement feature maintaining pylint 10.0
4. Update documentation and examples
5. Run full test suite and security audit
6. Create PR with detailed description

---

## 🎯 NEXT ACTIONS (Priority Order)

1. **Benchmark async vs v1.4.3** - The last open v1.5.0 task
2. **Release v1.5.0** - Async I/O + config files (target October 2026)
3. **Design monitoring mode** - First v1.6.0 task (target Q1 2027)

---

**Last Updated**: 2026-10-10
**Maintainer Note**: v1.5.0 ships the finished async I/O and configuration work;
monitoring mode moved to v1.6.0 so it no longer holds up the release.
