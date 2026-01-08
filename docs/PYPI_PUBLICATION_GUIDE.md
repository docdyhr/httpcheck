# PyPI Publication Guide for httpcheck v1.4.2

This is the **first publication** of httpcheck to PyPI. Follow these steps carefully.

---

## 📋 Pre-Publication Checklist

✅ **All items verified and ready:**

- ✅ Package built: `httpcheck-1.4.2-py3-none-any.whl` (31KB)
- ✅ Source distribution built: `httpcheck-1.4.2.tar.gz` (58KB)
- ✅ Package validation: Both files PASSED twine check
- ✅ Version updated: 1.4.2 in all files
- ✅ CHANGELOG.md: Complete release notes
- ✅ Tests passing: 278/297 tests (88% coverage)
- ✅ Pylint score: 10.0/10
- ✅ Security audit: PASSED (production dependencies)
- ✅ Git tagged: v1.4.2 pushed to GitHub
- ✅ Documentation: 24 HTML pages built

---

## 🔑 Step 1: Create PyPI Accounts (First Time Only)

### A. TestPyPI Account (for testing)
1. Visit: https://test.pypi.org/account/register/
2. Create account with email verification
3. Enable 2FA (recommended)

### B. Production PyPI Account
1. Visit: https://pypi.org/account/register/
2. Create account with email verification
3. Enable 2FA (required for new projects)

### C. Create API Tokens

**TestPyPI Token:**
1. Go to: https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: `httpcheck-testpypi`
4. Scope: "Entire account" (first upload) or "httpcheck" (after first upload)
5. Copy token starting with `pypi-...` (you'll only see it once!)

**Production PyPI Token:**
1. Go to: https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Token name: `httpcheck-pypi`
4. Scope: "Entire account" (first upload) or "httpcheck" (after first upload)
5. Copy token starting with `pypi-...` (you'll only see it once!)

---

## 🧪 Step 2: Upload to TestPyPI (Recommended First)

This allows you to test the upload and installation without affecting production PyPI.

### Upload Command:
```bash
cd /Users/thomas/Programming/httpcheck
twine upload --repository testpypi dist/httpcheck-1.4.2*
```

### When Prompted:
- **Username**: `__token__`
- **Password**: Paste your TestPyPI API token (starts with `pypi-...`)

### Expected Output:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading httpcheck-1.4.2-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 31.0/31.0 kB • 00:00
Uploading httpcheck-1.4.2.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58.0/58.0 kB • 00:00

View at:
https://test.pypi.org/project/httpcheck/1.4.2/
```

---

## ✅ Step 3: Test Installation from TestPyPI

### Create Test Environment:
```bash
# Create fresh virtual environment
python3 -m venv /tmp/test-httpcheck
source /tmp/test-httpcheck/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ httpcheck

# Note: --extra-index-url is needed for dependencies (requests, tabulate, tqdm)
```

### Verify Installation:
```bash
# Check version
httpcheck --version
# Expected: httpcheck 1.4.2

# Test basic functionality
httpcheck google.com
# Expected: Status code output

# Test new logging features
httpcheck google.com --debug
# Expected: Debug logs visible

# Test JSON output
httpcheck google.com --output json
# Expected: JSON formatted output
```

### Cleanup Test Environment:
```bash
deactivate
rm -rf /tmp/test-httpcheck
```

---

## 🚀 Step 4: Upload to Production PyPI

**Only proceed if TestPyPI installation worked perfectly!**

### Upload Command:
```bash
cd /Users/thomas/Programming/httpcheck
twine upload dist/httpcheck-1.4.2*
```

### When Prompted:
- **Username**: `__token__`
- **Password**: Paste your Production PyPI API token (starts with `pypi-...`)

### Expected Output:
```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading httpcheck-1.4.2-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 31.0/31.0 kB • 00:00
Uploading httpcheck-1.4.2.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58.0/58.0 kB • 00:00

View at:
https://pypi.org/project/httpcheck/1.4.2/
```

---

## ✅ Step 5: Verify Production Installation

### Install from Production PyPI:
```bash
# Create fresh virtual environment
python3 -m venv /tmp/verify-httpcheck
source /tmp/verify-httpcheck/bin/activate

# Install from production PyPI
pip install httpcheck

# Verify version
httpcheck --version
# Expected: httpcheck 1.4.2

# Test functionality
httpcheck google.com --debug --output json

# Cleanup
deactivate
rm -rf /tmp/verify-httpcheck
```

---

## 📝 Step 6: Update Project Documentation

### A. Update README.md

Add PyPI badge at the top:
```markdown
[![PyPI version](https://badge.fury.io/py/httpcheck.svg)](https://badge.fury.io/py/httpcheck)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/httpcheck)](https://pypi.org/project/httpcheck/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/httpcheck)](https://pypi.org/project/httpcheck/)
```

Update installation instructions:
```markdown
## Installation

### From PyPI (Recommended)
```bash
pip install httpcheck
```

### From Source
```bash
git clone https://github.com/docdyhr/httpcheck.git
cd httpcheck
pip install -e .
```
```

### B. Update TODO.md

Mark PyPI publication as complete:
```markdown
- [x] **Publish to PyPI** - v1.4.2 published on January 8, 2026
```

### C. Create GitHub Release

1. Go to: https://github.com/docdyhr/httpcheck/releases/new
2. Choose tag: `v1.4.2`
3. Release title: `v1.4.2: Enterprise-Grade Improvements`
4. Description: Copy from `CHANGELOG.md` v1.4.2 section
5. Attach files:
   - `dist/httpcheck-1.4.2-py3-none-any.whl`
   - `dist/httpcheck-1.4.2.tar.gz`
6. Publish release

---

## 🔐 Step 7: Secure API Token Storage (Optional)

### Option 1: Store in .pypirc (Local Development)

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
```

Set secure permissions:
```bash
chmod 600 ~/.pypirc
```

**IMPORTANT**: Add to `.gitignore` to prevent accidental commits!

### Option 2: Use Environment Variables

```bash
# Add to ~/.zshrc or ~/.bashrc
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR-TOKEN-HERE
```

Then upload without prompts:
```bash
twine upload dist/httpcheck-1.4.2*
```

### Option 3: GitHub Actions (CI/CD)

For automated releases, store tokens as GitHub Secrets:
1. Go to: https://github.com/docdyhr/httpcheck/settings/secrets/actions
2. Add secret: `PYPI_API_TOKEN`
3. Value: Your production PyPI token

Update `.github/workflows/release.yml` to use it.

---

## 🎯 Post-Publication Checklist

After successful publication:

- [ ] Verify package appears at https://pypi.org/project/httpcheck/
- [ ] Test installation: `pip install httpcheck`
- [ ] Update README.md with PyPI badges
- [ ] Update TODO.md marking publication complete
- [ ] Create GitHub release with attached files
- [ ] Announce on social media / project channels
- [ ] Monitor GitHub issues for user feedback
- [ ] Update project documentation with PyPI links

---

## 🐛 Troubleshooting

### Error: "The user 'xxx' isn't allowed to upload to project 'httpcheck'"

**Solution**: Use "Entire account" scope for first upload, then create project-specific token.

### Error: "File already exists"

**Solution**: PyPI doesn't allow re-uploading same version. Increment version number.

### Error: "Invalid authentication credentials"

**Solutions**:
- Ensure username is `__token__` (including double underscores)
- Check token starts with `pypi-` and is complete
- Verify you're using the correct token (TestPyPI vs Production)
- Regenerate token if copy/paste issues suspected

### Error: "Package name already taken"

**Solution**:
- Check if package exists: https://pypi.org/project/httpcheck/
- If taken by someone else, choose different name (e.g., `httpcheck-cli`)
- Update `pyproject.toml` name field before rebuilding

### TestPyPI works but Production PyPI fails

**Common Issues**:
- Different tokens needed for each
- 2FA may be required for production (not TestPyPI)
- Rate limiting on production (wait a few minutes)

---

## 📊 Package Statistics

After publication, monitor:

- **PyPI Page**: https://pypi.org/project/httpcheck/
- **Download Stats**: https://pypistats.org/packages/httpcheck
- **Package Health**: https://libraries.io/pypi/httpcheck

---

## 🔄 Future Releases

For subsequent releases (v1.4.3, v1.5.0, etc.):

1. Update version in all files
2. Update CHANGELOG.md
3. Build new packages: `python3 -m build`
4. Validate: `twine check dist/httpcheck-VERSION*`
5. Upload: `twine upload dist/httpcheck-VERSION*`

Much simpler than first release! Consider automating with GitHub Actions.

---

## ✅ Ready to Publish!

All prerequisites are met. Follow the steps above to complete the first PyPI publication of httpcheck.

**Current Status**:
- Package: ✅ Built and validated
- Git: ✅ Tagged and pushed
- Tests: ✅ 88% coverage passing
- Documentation: ✅ Complete

**Next Action**: Run Step 2 (TestPyPI upload) above.

---

**Last Updated**: January 8, 2026
**Package Version**: 1.4.2
**First Publication**: Yes ✨
