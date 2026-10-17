# Agent skills

Installed from [github/awesome-copilot](https://github.com/github/awesome-copilot) (MIT License, see [`LICENSE`](LICENSE)) at commit `cb64ad12e32737ae764becd6885462e9b4c7cb00`.
Lives in `.claude/skills/`, which Claude Code loads as project skills and GitHub Copilot (cloud agent, CLI, VS Code agent mode) also reads.
`github-release` and `conventional-commit` were deliberately left out because they conflict with this repo's release and commit conventions.
`pytest-coverage` (its goal is 100% coverage; this repo's gate is 70%) and `dependabot` (overlaps the owner's triage workflow and this repo's existing Dependabot automation) were removed for the same reason.

| Skill | Purpose |
|---|---|
| `github-actions-hardening` | Security hardening reviewer for GitHub Actions workflow files (.github/workflows/*.yml). Reasons about the Act… |
| `test-gap-audit` | Run a read-only audit for missing, weak, stale, or mis-scoped test coverage. If the user does not name a scope… |
| `docs-sync-audit` | Run a read-only documentation drift audit for a feature, PR, branch, release, API, configuration change, workf… |
