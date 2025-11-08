# Release Process

The automated workflow in `.github/workflows/release.yml` publishes tagged
versions to PyPI via trusted publishing. Use this checklist for every release.

## 1. Prepare the Release

1. Update `pyproject.toml` and `httpcheck/common.py` with the new version.
2. Document the changes in `CHANGELOG.md` and ensure README/docs reflect new
   features or breaking changes.
3. Run the full quality gate locally:
   ```bash
   pip install -e ".[dev]"
   pip install pip-audit
   pytest
   pip-audit
   ```
4. Verify CI is green on the target branch before tagging.

## 2. Tag the Release

1. Create an annotated tag that matches `vX.Y.Z`.
   ```bash
   git tag -a v1.5.0 -m "Release v1.5.0"
   git push origin v1.5.0
   ```
2. The `Publish Release` workflow builds the wheel+sdist and publishes to PyPI
   using OpenID Connect; no secrets are required once the PyPI project trusts
   `docdyhr/httpcheck`.

## 3. Post-Release Tasks

1. Create a GitHub Release via the tag, including highlights and upgrade notes.
2. Share the release announcement and link to any migration guide updates.
3. Update `ROADMAP.md`/`TODO.md` to reflect completed work and next milestones.

> Tip: protect `main`/`master` so only branches that pass the updated CI checks
> can be merged; this keeps release tags reproducible.
