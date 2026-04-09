# ADR 0001: Async HTTP Client Choice

- Status: Accepted
- Date: 2026-03-11
- Context: v1.5.0 requires an async implementation with pooling, HTTP/2 readiness, timeouts, and minimal surface-change from requests.
- Decision: Use `httpx.AsyncClient`.
  - Rationale: requests-style API; built-in HTTP/2 toggle; connection pooling and limits; granular timeouts; sync+async parity for future convergence; active maintenance.
  - Alternatives: `aiohttp` (rich but different API, heavier migration); `urllib3` async (unstable, fewer ergonomics).
- Consequences:
  - Add runtime dependency `httpx>=0.27`.
  - Implement async module `httpcheck/async_site_checker.py`.
  - Keep follow_redirects limited to `always|never` initially; add protocol-restricted handling later.
  - Add pytest-asyncio to dev deps and new async perf tests.
