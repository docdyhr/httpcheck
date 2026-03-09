# GitHub Environment Configuration Fix

## Issue

The PyPI publish workflow is failing with:
```
Tag 'v1.4.2' is not allowed to deploy to pypi due to environment protection rules.
```

## Solution

You need to configure the GitHub `pypi` environment to allow deployments from tags.

### Step 1: Go to Environment Settings

Visit: **https://github.com/docdyhr/httpcheck/settings/environments/pypi**

### Step 2: Configure Deployment Branches and Tags

1. Scroll down to **"Deployment branches and tags"** section

2. Current setting is likely: "Selected branches and tags" with no tags configured

3. Choose ONE of these options:

   **Option A: Allow All Branches and Tags (Simplest)**
   - Select: **"All branches"**
   - This allows any tag or branch to trigger deployment
   - ✅ Recommended for solo projects

   **Option B: Allow Specific Tag Pattern (More Secure)**
   - Select: **"Selected branches and tags"**
   - Click **"Add deployment branch or tag rule"**
   - Select: **"Ref type: Tag"**
   - Enter pattern: `v*.*.*`
   - Click **"Add rule"**
   - ✅ Recommended for team projects

### Step 3: Save Changes

Changes are saved automatically. No need to click a save button.

### Step 4: Re-run the Workflow

After fixing the environment settings, re-run the failed workflow:

**Option A: Re-run from GitHub UI**
1. Go to: https://github.com/docdyhr/httpcheck/actions/runs/20819352811
2. Click **"Re-run failed jobs"**
3. Confirm re-run

**Option B: Push Tag Again**
```bash
cd /Users/thomas/Programming/httpcheck
git tag -d v1.4.2
git push origin :refs/tags/v1.4.2
git tag -a v1.4.2 -m "v1.4.2: Enterprise-Grade Improvements"
git push origin v1.4.2
```

## Quick Fix Instructions

1. **Go to**: https://github.com/docdyhr/httpcheck/settings/environments/pypi
2. **Find**: "Deployment branches and tags"
3. **Select**: "All branches" (simplest option)
4. **Re-run**: Go to https://github.com/docdyhr/httpcheck/actions/runs/20819352811 and click "Re-run failed jobs"

That's it! The workflow should now succeed and publish to PyPI.

## Why This Happened

When you created the `pypi` environment in GitHub, it automatically set up protection rules that restrict which branches/tags can deploy. This is a security feature to prevent accidental deployments, but it needs to be configured to allow your version tags.

## Verification

After re-running, you should see:
1. Workflow completes successfully (green checkmark)
2. Package appears at: https://pypi.org/project/httpcheck/
3. You can install with: `pip install httpcheck`

---

**Last Updated**: January 8, 2026
**Issue**: Environment protection blocking tag deployments
**Status**: Awaiting manual configuration
