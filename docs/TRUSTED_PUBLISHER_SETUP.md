# PyPI Trusted Publisher Setup Guide

This guide walks you through setting up automated PyPI publishing using GitHub Actions and Trusted Publishers (OIDC). This is **more secure** than using API tokens as it doesn't require storing secrets.

---

## 🎯 Overview

**What is Trusted Publishing?**
- Uses OpenID Connect (OIDC) for authentication
- No API tokens or passwords needed
- GitHub Actions directly publishes to PyPI
- More secure and maintainable than token-based auth

**Repository**: https://github.com/docdyhr/httpcheck
**PyPI Project**: httpcheck (will be created on first publish)

---

## ✅ Step 1: Configure PyPI Trusted Publisher

### Go to PyPI Trusted Publishers Page

Since this is the **first publication**, use the "pending publisher" feature:

**URL**: https://pypi.org/manage/account/publishing/

### Fill in the Form

| Field | Value | Notes |
|-------|-------|-------|
| **PyPI Project Name** | `httpcheck` | Must match name in pyproject.toml |
| **Owner** | `docdyhr` | Your GitHub username |
| **Repository name** | `httpcheck` | GitHub repository name |
| **Workflow name** | `publish.yml` | Name of workflow file (without .github/workflows/) |
| **Environment name** | `pypi` | GitHub environment (recommended for protection) |

### Click "Add"

This creates a "pending publisher" that will automatically create the PyPI project when first used.

---

## ✅ Step 2: Configure GitHub Environment (Recommended)

GitHub environments add an extra layer of protection and approval workflow.

### A. Create Environment

1. Go to: https://github.com/docdyhr/httpcheck/settings/environments
2. Click "New environment"
3. Name: `pypi`
4. Click "Configure environment"

### B. Add Protection Rules (Optional but Recommended)

**Required reviewers** (if working with a team):
- Add trusted reviewers who must approve before publishing
- Skip this if you're the only maintainer

**Wait timer**:
- Add a delay (e.g., 5 minutes) before deployment
- Gives you time to cancel if tag was pushed accidentally
- Recommended: 0 minutes for solo projects

**Deployment branches and tags**:
- Select: "Selected branches and tags"
- Add rule: `refs/tags/v*.*.*`
- This ensures only version tags trigger publishing

### C. Environment Variables (None needed)

With trusted publishing, no secrets or tokens are required!

---

## ✅ Step 3: Verify Workflow File

The workflow file has been created at `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*.*.*"  # Triggers on version tags like v1.4.2

permissions:
  id-token: write  # Required for OIDC trusted publishing
  contents: read

jobs:
  build-and-publish:
    name: Build and publish to PyPI
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/project/httpcheck/

    steps:
      - name: Checkout code
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install build dependencies
        run: python -m pip install --upgrade pip build twine

      - name: Build distribution packages
        run: python -m build

      - name: Check distribution packages
        run: twine check dist/*

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No token needed - uses OIDC!
```

**Key Points**:
- ✅ Triggers on version tags (v*.*.*)
- ✅ Uses `id-token: write` permission for OIDC
- ✅ References `pypi` environment
- ✅ No secrets or tokens required

---

## ✅ Step 4: Commit and Push Workflow

Since the workflow file is new, commit it:

```bash
cd /Users/thomas/Programming/httpcheck
git add .github/workflows/publish.yml docs/TRUSTED_PUBLISHER_SETUP.md
git commit -m "feat: Add GitHub Actions workflow for automated PyPI publishing

- Uses PyPI Trusted Publishers (OIDC) for secure authentication
- No API tokens required
- Triggers on version tags (v*.*.*)
- Includes twine validation before publishing"
git push origin master
```

---

## 🚀 Step 5: Test the First Publication

### Option A: Re-push Existing Tag (Recommended for Testing)

Since v1.4.2 tag already exists, delete and re-push it to trigger the workflow:

```bash
# Delete local tag
git tag -d v1.4.2

# Delete remote tag
git push origin :refs/tags/v1.4.2

# Recreate tag
git tag -a v1.4.2 -m "v1.4.2: Enterprise-Grade Improvements"

# Push tag (this triggers the workflow)
git push origin v1.4.2
```

### Option B: Create New Test Tag

If you prefer not to delete/recreate v1.4.2:

```bash
# Create a test tag
git tag -a v1.4.2-test -m "Test automated publishing"
git push origin v1.4.2-test

# Delete after testing
git push origin :refs/tags/v1.4.2-test
git tag -d v1.4.2-test
```

---

## ✅ Step 6: Monitor the Workflow

### Watch the Action Run

1. Go to: https://github.com/docdyhr/httpcheck/actions
2. You should see "Publish to PyPI" workflow running
3. Click on it to see real-time progress

### Expected Output

**Successful Run**:
```
✓ Checkout code
✓ Set up Python
✓ Install build dependencies
✓ Build distribution packages
✓ Check distribution packages
✓ Publish to PyPI
  → Successfully published httpcheck 1.4.2 to PyPI
```

**If it Fails on First Run**:
- Check that PyPI Trusted Publisher is configured correctly
- Verify environment name matches exactly: `pypi`
- Ensure workflow name is exactly: `publish.yml`
- Check GitHub Actions logs for specific error

---

## ✅ Step 7: Verify Publication

### Check PyPI

1. Visit: https://pypi.org/project/httpcheck/
2. Verify version 1.4.2 is published
3. Check files are uploaded (wheel + source)

### Test Installation

```bash
# Create test environment
python3 -m venv /tmp/test-httpcheck
source /tmp/test-httpcheck/bin/activate

# Install from PyPI
pip install httpcheck

# Verify version
httpcheck --version
# Expected: httpcheck 1.4.2

# Test functionality
httpcheck google.com --debug

# Cleanup
deactivate
rm -rf /tmp/test-httpcheck
```

---

## 🎉 Success! What Happens Now?

### Automatic Publishing Process

Every time you push a version tag:

1. **Developer pushes tag**: `git push origin v1.5.0`
2. **GitHub Actions triggered**: Workflow runs automatically
3. **Build packages**: Creates wheel and source distribution
4. **Validate packages**: Runs twine check
5. **Authenticate via OIDC**: GitHub proves identity to PyPI
6. **Publish to PyPI**: Packages uploaded automatically
7. **Done**: No manual intervention needed!

### Benefits

✅ **Secure**: No API tokens to manage or leak
✅ **Auditable**: All publishes logged in GitHub Actions
✅ **Automatic**: Just push a tag, everything else is handled
✅ **Protected**: Environment rules prevent accidental publishes
✅ **Transparent**: Full logs of every publication

---

## 🔄 Future Releases Workflow

For all future releases:

```bash
# 1. Update version in files
# - httpcheck/common.py: VERSION = "1.5.0"
# - httpcheck/__init__.py: __version__ = "1.5.0"
# - pyproject.toml: version = "1.5.0"
# - docs/conf.py: version = "1.5.0"

# 2. Update CHANGELOG.md with release notes

# 3. Commit changes
git add .
git commit -m "Release v1.5.0: [Your release description]"
git push origin master

# 4. Create and push tag
git tag -a v1.5.0 -m "v1.5.0: [Your release description]"
git push origin v1.5.0

# 5. Done! GitHub Actions publishes to PyPI automatically
```

---

## 🐛 Troubleshooting

### Error: "Token is invalid"

**Cause**: PyPI Trusted Publisher not configured correctly
**Solution**:
1. Go to https://pypi.org/manage/account/publishing/
2. Verify all fields match exactly (especially workflow name and environment)
3. For first publish, use "Add a pending publisher"

### Error: "Environment protection rules failed"

**Cause**: GitHub environment requires approval
**Solution**:
1. Go to: https://github.com/docdyhr/httpcheck/deployments
2. Click "Review deployments"
3. Approve the deployment

### Error: "Permission denied"

**Cause**: Missing `id-token: write` permission
**Solution**: Verify workflow has this in permissions section:
```yaml
permissions:
  id-token: write
  contents: read
```

### Workflow Doesn't Trigger

**Causes**:
1. Tag doesn't match pattern `v*.*.*`
2. Workflow file not in `main`/`master` branch
3. Workflow file has syntax errors

**Solution**:
- Check tag format: `git tag -l`
- Verify workflow exists: `ls .github/workflows/publish.yml`
- Check workflow syntax: https://github.com/docdyhr/httpcheck/actions

### Package Already Exists Error

**Cause**: Version already published to PyPI
**Solution**: Increment version number - PyPI doesn't allow re-uploading

---

## 📊 Monitoring and Stats

### GitHub Actions Dashboard
- **URL**: https://github.com/docdyhr/httpcheck/actions
- View all workflow runs
- Download logs for debugging
- See timing and status

### PyPI Project Page
- **URL**: https://pypi.org/project/httpcheck/
- View all published versions
- Download statistics
- Package metadata

### PyPI Stats
- **URL**: https://pypistats.org/packages/httpcheck
- Daily/monthly download trends
- Python version breakdown
- Geographic distribution

---

## 🔐 Security Best Practices

### What This Setup Prevents

✅ **No leaked tokens**: Tokens can't leak because they don't exist
✅ **No token rotation**: OIDC tokens are short-lived and automatic
✅ **No compromised secrets**: Nothing stored in GitHub Secrets
✅ **Audit trail**: Every publish logged with full context
✅ **Limited scope**: Only specific workflow can publish

### Additional Protections

**Environment protection rules**:
- Require manual approval for publishes
- Restrict to specific tags/branches
- Add wait timers

**Branch protection**:
- Require PR reviews before merging
- Require status checks to pass
- Prevent direct pushes to main

**Tag protection** (when available):
- Restrict who can create version tags
- Require signed tags

---

## 📚 Additional Resources

- **PyPI Trusted Publishers**: https://docs.pypi.org/trusted-publishers/
- **GitHub OIDC**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **gh-action-pypi-publish**: https://github.com/pypa/gh-action-pypi-publish

---

## ✅ Quick Reference Card

### PyPI Trusted Publisher Configuration
```
Project Name: httpcheck
Owner: docdyhr
Repository: httpcheck
Workflow: publish.yml
Environment: pypi
```

### Publish New Version
```bash
# Update version, commit changes
git tag -a v1.X.Y -m "Release message"
git push origin v1.X.Y
# Done! Automatic publishing starts
```

### Monitor Workflow
```
https://github.com/docdyhr/httpcheck/actions
```

### Verify Publication
```
https://pypi.org/project/httpcheck/
pip install --upgrade httpcheck
```

---

**Setup Date**: January 8, 2026
**First Version**: 1.4.2
**Status**: Ready to configure and test 🚀
