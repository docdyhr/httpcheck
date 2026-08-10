# httpcheck Development Roadmap

**Status snapshot (2026-06-22)**
- Current release: 1.4.3 (2026-03-09) ✅
- v1.5.0: async I/O ✅, config ✅, monitoring ⏳ — release targeting July 2026
- Test coverage: 88% | pylint: 10.0/10 | Security: clean

This roadmap tracks the development path for httpcheck. Completed versions are
archived for reference; active development is at the top.

---

## ⏳ Version 1.5.0 - Async Performance & Configuration (Target: July 2026)

**Focus**: Performance via async I/O, user-defined defaults, lightweight monitoring

### ✅ Phase 1: Async I/O (COMPLETE)

- [x] Evaluate aiohttp vs httpx — chose httpx
- [x] Create `async_site_checker.py` with connection pooling
- [x] Synchronous compatibility wrapper preserved
- [x] Async test suite (`test_async_site_checker.py`)
- [ ] Benchmark against v1.4.3 (target: 2–3× improvement for 100+ checks)

### ✅ Phase 2: Configuration File Support (COMPLETE)

- [x] `config.py` module with TOML support
- [x] Config discovery: `~/.httpcheck.toml`, `./httpcheck.toml`, env var
- [x] CLI flags override config file
- [x] Sections: `[defaults]`, `[headers]`, `[notifications]`

### ⏳ Phase 3: Monitoring Mode (IN PROGRESS)

- [ ] `httpcheck monitor @sites.txt --interval 300 --alert-on-change`
- [ ] Continuous check loop with state tracking
- [ ] SQLite storage for check history
- [ ] Console status dashboard
- [ ] Webhook and email alert delivery

### 📊 v1.5.0 Success Metrics

- [ ] Async mode ≥2× faster for 100+ concurrent checks
- [ ] Config file adopted with zero regressions on existing CLI
- [ ] Monitor mode stable for 24h+ continuous runs
- [ ] Test coverage ≥80%, pylint 10.0/10

---

## 🔍 Version 1.6.0 - Enhanced Output & Request Features (Target: Q4 2026)

**Focus**: Richer output options, advanced request control, content verification

### Output & Reporting

- [ ] **HIGH:** HTML report export with sortable table
- [ ] **HIGH:** Markdown report for documentation pipelines
- [ ] **MEDIUM:** XML output for CI system integration
- [ ] **MEDIUM:** Colorized terminal output
- [ ] **LOW:** PDF report generation

### Advanced Request Features

- [ ] **HIGH:** Cookie and session handling
- [ ] **HIGH:** Authentication: Basic, Bearer, API key
- [ ] **MEDIUM:** Request body support for POST/PUT checks
- [ ] **MEDIUM:** Rate limiting (`--rate-limit`) with burst control
- [ ] **LOW:** Certificate client authentication

### Content Verification

- [ ] **HIGH:** Pattern matching (`--content-check "regex"`)
- [ ] **MEDIUM:** Page title and meta tag assertions
- [ ] **MEDIUM:** Content change detection with diff output
- [ ] **LOW:** SSL certificate expiration warnings

### Performance Analytics

- [ ] **HIGH:** Timing breakdowns: DNS, SSL handshake, TTFB, download
- [ ] **MEDIUM:** Response time statistics (mean, P95, P99)
- [ ] **MEDIUM:** Performance baseline comparison across runs
- [ ] **LOW:** Response size tracking

### 📊 v1.6.0 Success Metrics

- [ ] HTML/Markdown output usable in CI pipelines
- [ ] Auth methods cover the top-3 enterprise patterns
- [ ] Content verification with <50ms overhead per check
- [ ] Test coverage ≥80%, pylint 10.0/10

---

## 🌐 Version 1.7.0 - Integrations (Target: Q1 2027)

**Focus**: Push data out to external systems; make httpcheck a data source

- [ ] **HIGH:** Prometheus metrics endpoint
- [ ] **HIGH:** Webhook notifications with Jinja2 templating
- [ ] **MEDIUM:** SQLite/PostgreSQL persistent storage
- [ ] **MEDIUM:** Slack and Discord alert delivery
- [ ] **LOW:** REST API for programmatic access
- [ ] **LOW:** Message queue output (Redis, RabbitMQ)

---

## 🌟 Version 2.0.0 - Next Generation Platform (Target: 2027)

**Focus**: Browser-level validation, AI-assisted analysis, enterprise features

### Browser-Based Validation

- [ ] Headless browser support via Playwright
- [ ] JavaScript execution and DOM assertions
- [ ] Screenshot on failure
- [ ] Core Web Vitals (LCP, CLS, FID)
- [ ] Accessibility testing integration

### AI-Powered Features

- [ ] Anomaly detection for response time and status changes
- [ ] Predictive failure analysis from historical data
- [ ] Smart alert grouping and deduplication
- [ ] Auto-remediation suggestions

### Enterprise Features

- [ ] Multi-tenant architecture
- [ ] SSO integration (SAML, OAuth 2.0)
- [ ] Role-based access control
- [ ] Audit logging and compliance export
- [ ] Distributed checking from multiple regions

### Developer Platform

- [ ] GraphQL API with real-time subscriptions
- [ ] SDK for Python, Go, Node.js
- [ ] Plugin architecture for custom validators
- [ ] Visual workflow builder

---

## ✅ Version 1.4.x - Foundation (RELEASED — March 2026)

All items delivered through v1.4.3 (2026-03-09):

- [x] Full modularization: 1,151-line monolith → 11 focused modules
- [x] 182 tests, 88% coverage (target was 70%)
- [x] Security: pickle → JSON for TLD cache; pip-audit clean
- [x] Output formats: JSON, CSV, table
- [x] Custom HTTP headers (`-H`), SSL control (`--no-verify-ssl`)
- [x] Package installation via `pip install -e .`
- [x] Async I/O groundwork (`async_site_checker.py`)
- [x] Centralized logging (`logger.py`), input validation module
- [x] GitHub Actions CI: test matrix Python 3.9–3.14, Dependabot, auto-merge
- [x] pylint 10.0/10 maintained throughout

---

## 📋 Development Guidelines

### Prioritization Framework

1. **User Impact** — direct value delivered to end users
2. **Technical Debt** — foundation quality for future development
3. **Market Demand** — user-requested features
4. **Effort-to-value** — avoid complexity that doesn't pull its weight

### Quality Standards

- **Code quality**: pylint 10.0/10, no exceptions
- **Test coverage**: ≥70% floor, ≥80% target
- **Security**: pip-audit clean on every release
- **Backward compatibility**: no CLI breakage within a major version

### Release Process

1. Feature branch from `main`
2. Tests written first (TDD)
3. Full suite green, pylint 10.0, pip-audit clean
4. PR review → merge → semantic-release tag
5. PyPI publish via CI on tag push

### Roadmap Maintenance

Reviewed after each minor release. Timelines are targets, not commitments —
quality and correctness take priority over dates.

---

**Last Updated**: 2026-06-22
**Next Review**: after v1.5.0 release

> Timelines are estimates. We ship when features are solid, not when the
> calendar says so.
