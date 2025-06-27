# Todo list for httpcheck

## 🚀 PHASE 1: Foundation Stabilization (Weeks 1-3) - CURRENT PRIORITY

### Week 1: Security & Dependencies (IMMEDIATE)
- [ ] **CRITICAL:** Replace pickle with JSON for TLD cache serialization
- [ ] **HIGH:** Consolidate requirements files into pyproject.toml
- [ ] **HIGH:** Audit and remove unused dependencies
- [ ] **MEDIUM:** Fix any security vulnerabilities in dependencies

### Week 2-3: Code Modularization (IN PROGRESS)
- [ ] **HIGH:** Create `httpcheck/` package directory structure
- [ ] **HIGH:** Extract `tld_manager.py` from main file (lines 600-800)
- [ ] **HIGH:** Extract `file_handler.py` for input processing (lines 200-400)
- [ ] **HIGH:** Extract `site_checker.py` for HTTP operations (lines 400-600)
- [ ] **HIGH:** Extract `output_formatter.py` for result display (lines 800-1000)
- [ ] **HIGH:** Extract `notification.py` for system notifications (lines 1000-1100)
- [ ] **HIGH:** Create `common.py` for shared utilities and constants
- [ ] **HIGH:** Update main `httpcheck.py` to use modular imports
- [ ] **CRITICAL:** Ensure backward compatibility maintained

## 🧪 PHASE 2: Testing & Quality (Weeks 4-6)

### Week 4: Test Infrastructure
- [ ] **HIGH:** Set up pytest framework and configuration
- [ ] **HIGH:** Create `tests/` directory structure
- [ ] **MEDIUM:** Add test fixtures and mock utilities
- [ ] **MEDIUM:** Configure coverage reporting (target >70%)

### Week 5-6: Test Implementation
- [ ] **HIGH:** Unit tests for `tld_manager.py`
- [ ] **HIGH:** Unit tests for `file_handler.py`
- [ ] **HIGH:** Unit tests for `site_checker.py`
- [ ] **HIGH:** Unit tests for `output_formatter.py`
- [ ] **MEDIUM:** Integration tests for CLI interface
- [ ] **MEDIUM:** Mock network requests for reliable testing
- [ ] **LOW:** Add CI/CD test automation enhancement

## 🎯 PHASE 3: Core Features (Weeks 7-10)

### Week 7-8: Output Formats
- [ ] **HIGH:** Implement JSON output format (`--output json`)
- [ ] **HIGH:** Add CSV export capability (`--output csv`)
- [ ] **MEDIUM:** Enhance table formatting options

### Week 9-10: Request Customization
- [ ] **HIGH:** Support custom HTTP headers (`-H` flag)
- [ ] **MEDIUM:** Add request timeout configuration
- [ ] **MEDIUM:** Implement retry logic improvements
- [ ] **LOW:** Add SSL verification options (`--no-verify-ssl`)

## ⚡ PHASE 4: Performance & Advanced Features (Weeks 11-16)

### Week 11-12: Performance Optimization
- [ ] **HIGH:** Implement async I/O for concurrent requests
- [ ] **MEDIUM:** Add connection pooling
- [ ] **MEDIUM:** Implement rate limiting (`--rate-limit`)
- [ ] **LOW:** Optimize memory usage

### Week 13-14: Configuration Management
- [ ] **HIGH:** Add configuration file support (~/.httpcheck.conf)
- [ ] **MEDIUM:** Support environment variable configuration
- [ ] **LOW:** Add profile-based configurations

### Week 15-16: Advanced Features
- [ ] **MEDIUM:** Colorized terminal output (using colorama)
- [ ] **MEDIUM:** Enhanced redirect handling
- [ ] **LOW:** Content verification capabilities
- [ ] **LOW:** Basic monitoring mode

## 🔮 FUTURE ENHANCEMENTS (v1.5.0+)

### Monitoring Capabilities
- [ ] Website monitoring mode with interval checks
- [ ] Store historical data in SQLite database
- [ ] Alert on status changes
- [ ] Threshold alerts for response times

### Content Verification
- [ ] Check for specific content in responses
- [ ] Verify page title, meta tags, or specific elements
- [ ] Content diff between checks

### Performance Metrics
- [ ] Add detailed timing measurements (DNS, SSL, TTFB)
- [ ] Response time statistics and trending
- [ ] Response size tracking and limits

### Integrations
- [ ] Prometheus metrics format support
- [ ] Webhook notifications
- [ ] Integration with messaging platforms (Slack, Discord)
- [ ] Email notifications for critical alerts

### Advanced Features (v2.0 vision)
- [ ] Browser-like validation (using headless Chrome/Firefox)
- [ ] API endpoint validation (JSON Schema, OpenAPI)
- [ ] Load testing capabilities
- [ ] Custom scripting support for complex validation
- [ ] Machine learning for anomaly detection

## 📋 DEVELOPMENT NOTES

### Current Status
- **Version**: 1.3.0
- **Main File**: httpcheck.py (1,151 lines)
- **Target Version**: 1.4.0
- **Timeline**: 16 weeks (4 months)

### Key Priorities
1. **IMMEDIATE**: Security fixes (pickle → JSON)
2. **CRITICAL**: Code modularization
3. **HIGH**: Test coverage >70%
4. **MEDIUM**: New output formats (JSON, CSV)

### Success Metrics
- [ ] Maintain pylint 10.0/10 score
- [ ] Achieve >70% test coverage
- [ ] Zero breaking changes to CLI
- [ ] All Phase 1 tasks completed by Week 3

### Dependencies to Remove
- [ ] Audit pickle usage
- [ ] Check for unused imports
- [ ] Consolidate requirements files
- [ ] Remove development-only dependencies from production

### Architecture Target
```
httpcheck/
├── __init__.py
├── common.py
├── tld_manager.py
├── file_handler.py
├── site_checker.py
├── output_formatter.py
├── notification.py
└── config.py
```

## Completed

* ~~Implement a progress bar for larger number of site checks~~ ✓
* ~~Notification system for macOS using terminal-notifier~~ ✓
* ~~Proper threading implementation with progress tracking~~ ✓
* ~~Implement advanced redirects check as an option~~ ✓
  * ~~Add --follow-redirects flag~~ ✓
  * ~~Show full redirect chain details~~ ✓
  * ~~Add max redirects option~~ ✓
  * ~~Track redirect timing~~ ✓

* ~~Input file improvements~~ ✓
  * ~~Strip whitespace and empty lines from domain files~~ ✓
  * ~~Validate file contents before processing~~ ✓
  * ~~Add support for comments in domain files~~ ✓
  * ~~Handle malformed lines gracefully~~ ✓

* ~~TLD validation~~ ✓
  * ~~Update TLD list with latest from publicsuffix.org~~ ✓
  * ~~Add caching for TLD list~~ ✓
  * ~~Update TLD list automatically~~ ✓
  * ~~Add option to disable TLD checks~~ ✓

* ~~Exception handling improvements~~ ✓
  * ~~Refactor to use proper HTTP exceptions~~ ✓
  * ~~Add more detailed error messages~~ ✓
  * ~~Implement better timeout handling~~ ✓
  * ~~Add connection error retry logic~~ ✓

* ~~Timeout and retry enhancements~~ ✓
  * ~~Add per-domain timeout settings~~ ✓
  * ~~Implement retry logic~~ ✓
  * ~~Add retry delay configuration~~ ✓

```

The updated TODO list now aligns with the roadmap I provided, prioritizing tasks based on:

1. **User Impact**: Features that provide immediate value to users are placed higher in the list
2. **Complexity**: More complex items are given appropriate priority based on effort-to-value ratio
3. **Dependencies**: Items that serve as foundations for other features are prioritized accordingly

The High Priority section focuses on code organization and essential features that will have the greatest immediate impact on maintainability and user experience. These items align with the Version 1.4.0 milestone in the roadmap.

Medium Priority items correspond to the Version 1.5.0 milestone features, which build upon the foundation established by the high-priority items.

Future Enhancements align with Version 1.6.0 and beyond, representing more advanced capabilities that will transform httpcheck from a simple status checker into a comprehensive monitoring solution.

The Completed section acknowledges the significant work already done, maintaining continuity with previous development efforts.

This structured approach ensures that development efforts are focused on the most impactful features first, while still maintaining a vision for the project's long-term evolution.
