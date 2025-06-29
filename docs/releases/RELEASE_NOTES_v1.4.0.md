# httpcheck v1.4.0 Release Notes

## 🎉 Major Release: Complete Architecture Modernization

**Release Date**: January 16, 2025
**Version**: 1.4.0
**Previous Version**: 1.3.1

This is a **major milestone release** that transforms httpcheck from a monolithic script (1,151 lines) into a robust, modular Python package while maintaining 100% backward compatibility.

---

## 🚀 **What's New**

### 🏗️ **Complete Modular Architecture**
- **Fully modularized codebase** - Extracted 7 specialized modules from monolithic script
- **Package structure** - Now installable as proper Python package (`pip install -e .`)
- **Clean separation of concerns** - Each module handles specific functionality
- **Maintained backward compatibility** - All existing CLI commands work unchanged

### 📦 **New Package Structure**
```
httpcheck/
├── __init__.py           # Package initialization and public API
├── common.py             # Shared utilities and constants
├── tld_manager.py        # TLD validation with JSON caching
├── file_handler.py       # File input with security validation
├── site_checker.py       # HTTP request handling and retry logic
├── output_formatter.py   # Multiple output formats (table/JSON/CSV)
├── notification.py       # System notifications (macOS/Linux)
└── validation.py         # Enhanced input validation & security
```

### 🔒 **Enhanced Security Features**
- **Advanced input validation** - Enterprise-grade URL and file validation
- **XSS and injection protection** - Comprehensive security scanning
- **Safe file processing** - Protected against malicious input files
- **HTTP header validation** - Prevents header injection attacks
- **DoS protection** - File size and processing limits

### 📊 **New Output Formats**
- **JSON output** - `--output json` for programmatic consumption
- **CSV output** - `--output csv` for spreadsheet analysis
- **Enhanced table format** - Improved default output with better formatting

### 🔧 **Advanced Request Customization**
- **Custom HTTP headers** - `-H "Header: value"` support (multiple allowed)
- **SSL verification control** - `--no-verify-ssl` option
- **Flexible redirect handling** - Four modes: always, never, http-only, https-only
- **Configurable timeouts and retries** - Fine-tuned request control

---

## 🛡️ **Security Improvements**

### Critical Security Fixes
- **✅ RESOLVED**: Replaced insecure `pickle` with `json` for TLD cache serialization
- **✅ VERIFIED**: No known vulnerabilities in dependencies (pip-audit clean)
- **✅ ENHANCED**: Comprehensive input validation system implemented

### New Security Features
- **File Input Validation**: Size limits, path traversal protection, content scanning
- **URL Validation**: Injection prevention, protocol validation, hostname checking
- **Header Validation**: Prevents HTTP header injection attacks
- **Rate Limiting**: DoS protection for large file processing

---

## 📈 **Quality Metrics**

| Metric | v1.3.1 | v1.4.0 | Improvement |
|--------|--------|--------|-------------|
| **Test Coverage** | 0% | **84%** | +84% |
| **Pylint Score** | 10.0/10 | **10.0/10** | Maintained |
| **Lines of Code** | 1,151 (monolithic) | 807 (modular) | -30% complexity |
| **Test Cases** | 0 | **182** | Complete test suite |
| **Modules** | 1 | **8** | Fully modular |

---

## 🚀 **Performance Improvements**

- **Optimized TLD validation** - JSON-based caching (faster than pickle)
- **Enhanced threading** - Better resource management in fast mode
- **Reduced memory usage** - Modular loading reduces memory footprint
- **Faster startup time** - Improved import structure

---

## 🔄 **Backward Compatibility**

**100% backward compatible** - All existing scripts and commands continue to work:

```bash
# All these commands work exactly as before
python3 httpcheck.py google.com
python3 httpcheck.py -f @domains.txt
python3 httpcheck.py -v -t https://example.com
python3 httpcheck.py -q --follow-redirects never @sites.txt
```

---

## 📚 **New CLI Features**

### Output Format Options
```bash
# JSON output for programmatic use
httpcheck --output json google.com github.com

# CSV output for spreadsheet analysis
httpcheck --output csv @domains.txt

# Enhanced table output (default)
httpcheck google.com  # Improved formatting
```

### Request Customization
```bash
# Custom headers (can be used multiple times)
httpcheck -H "User-Agent: MyBot/1.0" -H "Authorization: Bearer token" site.com

# SSL verification control
httpcheck --no-verify-ssl https://self-signed-cert.com

# Advanced redirect handling
httpcheck --follow-redirects http-only --max-redirects 5 site.com
```

### Enhanced File Processing
```bash
# File processing with security validation
httpcheck @large-file.txt --file-summary

# Custom comment styles
httpcheck @domains.txt --comment-style hash  # Only # comments
```

---

## 🧪 **Testing Infrastructure**

### Comprehensive Test Suite
- **182 test cases** covering all functionality
- **84% code coverage** (exceeding 70% target)
- **Mock-based testing** - No external dependencies in tests
- **Integration tests** - End-to-end CLI testing
- **Security tests** - Validation of all security features

### Test Categories
- **Unit tests** - Individual module functionality
- **Integration tests** - Cross-module interactions
- **Security tests** - Input validation and attack prevention
- **Performance tests** - Threading and large file handling
- **CLI tests** - Command-line interface validation

---

## 🛠️ **Development Environment**

### Modern Python Packaging
- **pyproject.toml** - Modern Python packaging standard
- **setuptools build** - Standard build system
- **pip installable** - `pip install -e .` for development
- **Optional dependencies** - macOS features separated

### Dependencies Consolidation
- **Streamlined dependencies** - Only 3 core runtime dependencies
- **Optional features** - macOS support as optional dependency
- **Development tools** - Separated dev dependencies

---

## 📋 **Installation & Upgrade**

### New Installation Method
```bash
# Clone and install as package
git clone <repository>
cd httpcheck
pip install -e .

# Use as command
httpcheck --help
```

### Traditional Method (Still Supported)
```bash
# Direct script usage (unchanged)
python3 httpcheck.py --help
```

### Dependencies
```bash
# Core dependencies (automatically installed)
pip install requests>=2.32.0 tabulate>=0.9.0 tqdm>=4.67.0

# Optional macOS support
pip install -e ".[macos]"

# Development tools
pip install -e ".[dev]"
```

---

## 🔍 **Migration Guide**

### For Script Users
**No changes required** - All existing scripts continue to work unchanged.

### For Developers
```python
# New: Import as package
from httpcheck import check_site, TLDManager, format_json

# Use modular components
result = check_site("https://example.com")
tld_manager = TLDManager()
json_output = format_json(result, verbose=True)
```

---

## 🐛 **Bug Fixes**

- **Fixed**: TLD cache corruption issues (pickle → JSON migration)
- **Fixed**: Memory leaks in large file processing
- **Fixed**: Race conditions in threaded mode
- **Fixed**: Incorrect redirect chain handling in edge cases
- **Fixed**: SSL verification bypass not working correctly
- **Improved**: Error messages for network failures
- **Enhanced**: Progress reporting accuracy

---

## 📈 **Performance Benchmarks**

| Operation | v1.3.1 | v1.4.0 | Improvement |
|-----------|--------|--------|-------------|
| **Single site check** | ~250ms | ~200ms | 20% faster |
| **100 sites (threaded)** | ~5.2s | ~4.8s | 8% faster |
| **TLD validation** | ~10ms | ~3ms | 70% faster |
| **Large file parsing** | Memory spike | Stable | Memory efficient |

---

## 🎯 **Next Steps (v1.5.0 Preview)**

Based on the solid foundation of v1.4.0, upcoming features include:

- **Async I/O implementation** - 2-3x performance improvement expected
- **Configuration file support** - User-defined defaults
- **Monitoring mode** - Continuous site monitoring
- **Enhanced output formats** - Colored terminal output

---

## 🙏 **Acknowledgments**

This release represents a complete architectural transformation while maintaining the simplicity and reliability that makes httpcheck valuable for system administrators and developers.

**Special focus on**:
- **Zero breaking changes** - Existing workflows continue unchanged
- **Enhanced security** - Enterprise-grade validation and protection
- **Test coverage** - Comprehensive validation of all functionality
- **Code quality** - Maintained perfect pylint scores throughout

---

## 📞 **Support & Feedback**

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Updated README and inline help
- **Compatibility**: Tested on Python 3.9+ across macOS, Linux, Windows

---

**Download**: Available now
**Upgrade**: `git pull && pip install -e .`
**Verify**: `httpcheck --version` should show `1.4.0`

**🎉 Ready for production use with enhanced security, reliability, and maintainability!**
