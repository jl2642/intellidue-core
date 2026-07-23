# GitHub Deployment Handoff

Recommended public repository: `intellidue-core`

## Deployment sequence
1. Create a new public, empty GitHub repository without README, .gitignore or license.
2. Unzip the public bootstrap bundle locally.
3. Review `LICENSE_PENDING.md`; choose a license before calling the repository open source.
4. Initialize Git, commit, set the remote and push `main`.
5. Confirm GitHub Actions passes.
6. Create release `v1.0.0-production-baseline` after CI is green.
7. Keep every real project package in a separate private repository or private cloud store.

## Acceptance before first release
- public-boundary scan passes;
- unit tests pass;
- synthetic package validation passes;
- no private project identifiers or binaries are present;
- branch protection and secret scanning are enabled in GitHub settings.
