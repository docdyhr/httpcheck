# GitHub Issue Drafts

These ready-to-file issue descriptions capture the highest-priority follow-ups
identified for the v1.4.0 release. Copy each block into a GitHub issue so the
work is visible to collaborators.

---

## 1. Track v1.4.0 Adoption & Feedback

**Summary**
- Stand up a lightweight process (issue labels + discussion template) to record
  user feedback, regressions, or performance data from the newly released
  modular architecture.

**Why Now**
- TODO.md lists “Monitor v1.4.0 adoption” as an immediate priority, yet no
  GitHub artifact exists to collect observations.

**Acceptance Criteria**
- Create an issue label (e.g., `release-feedback`) and a pinned tracking issue.
- Link the tracking issue from README/ROADMAP so testers know where to report.
- Include a short questionnaire covering environment, CLI flags, and failures.

---

## 2. Update Project Website & Docs

**Summary**
- Refresh README, docs site, and any external landing pages to reflect the new
  module layout, CLI options, and installation flow (`pip install -e .`).

**Why Now**
- Documentation still references the monolithic script in several places.

**Acceptance Criteria**
- Audit every doc under `docs/`, `README.md`, and the website for outdated
  references to the old structure.
- Add a “What’s New in 1.4.0” section with screenshots of JSON/CSV output.
- Verify all command snippets run end-to-end in a clean venv.

---

## 3. Publish Modular Migration Guide

**Summary**
- Provide a concise guide showing how to import the new modules (`httpcheck.*`)
  so library users can adopt the package without reading the entire codebase.

**Why Now**
- Immediate priority in TODO.md; currently undocumented.

**Acceptance Criteria**
- New doc (e.g., `docs/migration.md`) with before/after code snippets.
- Cover CLI users, library importers, and macOS menu bar configuration.
- Link guide from README and the release notes section in CHANGELOG.md.

---

## 4. Automate Releases (PyPI + Tags)

**Summary**
- Implement the “Automated release process” item from TODO.md by adding a
  GitHub Actions workflow that, on version tag, builds wheels/sdists and
  uploads them to PyPI using trusted publishing.

**Why Now**
- Manual releases are error-prone and delay distributing fixes.

**Acceptance Criteria**
- New workflow triggered on semver tags.
- Uses `pypa/gh-action-pypi-publish` with OIDC.
- Includes release checklist in docs (verify changelog, version bump, tests).

---

## 5. Dependabot Configuration

**Summary**
- Add `.github/dependabot.yml` to keep runtime and GitHub Actions dependencies
  current, addressing the remaining CI item in TODO.md.

**Acceptance Criteria**
- Schedule weekly checks for:
  - `pip` ecosystem (pyproject dependencies)
  - GitHub Actions workflows
- Document auto-merge policy (if any) in CONTRIBUTING.md.

---

> Once these issues are opened, reference them back in `TODO.md` so contributors
> can find the authoritative tracking links.
