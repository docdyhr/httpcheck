# Release Process

Tagged versions are published to PyPI by `.github/workflows/publish.yml`
("Publish to PyPI") using trusted publishing (OIDC). **Pushing a `vX.Y.Z` tag
starts the workflow**, which then waits for the maintainer's approval on the
`pypi` environment before it builds and uploads. A PyPI version can never be
re-uploaded, so everything is verified before the tag is pushed and again before
approving. Use this checklist for every release.

## 1. Prepare the Release (release PR)

1. Create `release/vX.Y.Z` from an up-to-date `main`.
2. Bump the version everywhere it lives. Search for the old value instead of
   trusting a list:
   ```bash
   grep -rnF "OLD_VERSION" . --exclude-dir=.git --exclude-dir=.venv --exclude=CHANGELOG.md
   ```
   The sites that must change are `pyproject.toml`, `httpcheck/__init__.py`,
   `httpcheck/common.py` (`httpcheck --version` prints this one), the `Version:`
   line in the `httpcheck/cli.py` docstring, `docs/conf.py` (`version` and
   `release`) and `tests/test_init.py`. Leave historical mentions (benchmark
   baselines, past releases) alone.
3. Move `[Unreleased]` in `CHANGELOG.md` to `[X.Y.Z] - YYYY-MM-DD`, add the entry
   to `docs/changelog.rst`, and update README, ROADMAP, TODO and CLAUDE.md wherever
   they say "current", "unreleased" or "target".
4. Run the quality gate locally:
   ```bash
   pip install -e ".[dev]"
   pytest
   pylint --fail-under=10.0 httpcheck.py httpcheck/*.py
   mypy httpcheck
   ```
   `pip-audit` runs in CI (test matrix and Security Scanning jobs); check it on
   the PR.
5. Open a PR titled `chore(release): vX.Y.Z` against `main`. The `Protect main`
   ruleset requires a PR and these checks: Code Quality Check, Security Scanning,
   and Test Python 3.10 / 3.14 on ubuntu-latest. Wait for all CI checks, then
   merge. Never push the release commit to `main` directly.

## 2. Tag the Release (this publishes)

1. Update `main` and create an annotated tag on the **merge commit** of the
   release PR:
   ```bash
   git checkout main && git pull --ff-only origin main
   git tag -a vX.Y.Z -m "Release vX.Y.Z" <merge-commit-sha>
   ```
2. Before pushing, check the version at the tagged commit in `pyproject.toml`,
   `httpcheck/__init__.py` and `httpcheck/common.py`, for example
   `git show vX.Y.Z:pyproject.toml | grep '^version'`.
3. Push only the tag: `git push origin vX.Y.Z`. The workflow's job is bound to
   the `pypi` environment, so it waits for approval (Actions -> the run -> Review
   deployments) before it builds the wheel and sdist, runs `twine check` and
   uploads via OpenID Connect; no secrets are needed while PyPI trusts
   `docdyhr/httpcheck`.
4. Before approving, check the run is for the tag you pushed. After approval,
   watch it (`gh run watch`) and confirm the new version on
   https://pypi.org/project/httpcheck/.

Do not push old or ad-hoc tags: any `v*.*.*` tag starts the publish workflow.

## 3. Post-Release Tasks

1. Create a GitHub Release from the tag, using the CHANGELOG section as notes:
   `gh release create vX.Y.Z --verify-tag --title vX.Y.Z --notes-file <notes.md>`.
2. Smoke-test the published package in a throwaway virtualenv:
   `pip install httpcheck==X.Y.Z && httpcheck --version`.
3. Share the release announcement and link to any migration guide updates.
4. GitHub deletes the merged release branch on the remote; delete the local one
   and run `git fetch --prune`.

> `main` is protected by the `Protect main` ruleset: a PR and the four named
> checks are required, and force-push and deletion are blocked. Repository admins
> can bypass it only through a PR. This keeps release tags reproducible.
