# GitHub-Final Operational Release Checklist

Status: `READY_FOR_IMMUTABLE_RELEASE`

## A. Accepted prerequisites

- [x] GitHub-0 private/public distribution boundary frozen.
- [x] GitHub-1 public repository bootstrap and CI accepted.
- [x] GitHub-2A strict schemas and cross-object contracts accepted.
- [x] GitHub-2B deterministic manifests, pointers, promotion, rollback and recovery accepted.
- [x] GitHub-2C stable CLI and strict release-package validation accepted.
- [x] GitHub-3 CI, dependency controls, CodeQL, reproducible build and tag-driven release automation accepted.
- [x] GitHub-4 private project runtime adapter accepted on synthetic fixtures.
- [x] GitHub-5 complete authoritative private-project replay accepted and merged to `main`.

## B. Current source-controlled state

- Package version: `1.5.0`.
- Production product standard: `1.0.0`.
- Schema contract: `1.0.0`.
- CLI contract: `1.0.0`.
- Release package format: `1.0.0`.
- Private runtime adapter contract: `1.0.0`.
- No License / all rights reserved remains the authority.
- Real project data in public repository: prohibited.
- Final Full DD: still project-evidence and professional-signoff gated.

## C. Repository-owner platform controls

Accepted on 2026-07-23. Evidence is recorded in `docs/acceptance/github-final-platform-controls-20260723.md` and Issue #2.

- [x] Require a pull request before merging to `main`.
- [x] Require `ci / required`.
- [x] Require Dependency Review using its stable check name.
- [x] Require CodeQL Python analysis using its stable check name.
- [x] Require branches to be up to date before merge.
- [x] Require conversation resolution.
- [x] Block force pushes and deletion of `main`.
- [x] Apply the rule without routine bypass; emergency owner intervention must be documented and audited.
- [x] Enable dependency graph.
- [x] Enable Dependabot alerts.
- [x] Enable Dependabot security updates.
- [x] Enable secret scanning.
- [x] Enable push protection.
- [x] Enable private vulnerability reporting.
- [x] Confirm CodeQL advanced setup is active.
- [x] Retain squash merge as the normal merge method.
- [x] Disable merge commits and rebase merge for normal work.
- [x] Enable automatic branch updates where available.
- [x] Record owner-view evidence, date and account basis in Issue #2 and the acceptance record.

Independent repository metadata confirms merge commits disabled, rebase merges disabled, squash merge enabled and pull-request branch update suggestions enabled.

## D. Final source-controlled closure

- [x] Update Issue #2 with evidence and authorize closure.
- [x] Update README and Current state to the immutable-release gate.
- [x] Freeze the operating model, new-project runbook, privacy assurance and private-file retention rules.
- [x] Run final unit, compatibility, package, privacy, security and reproducible-build checks on the GitHub-Final PR head.
- [ ] Merge the GitHub-Final PR through the protected `main` workflow.
- [ ] Verify the release tag exactly matches package version: `core-v1.5.0`.
- [ ] Push the immutable tag and allow the release workflow to create checksummed assets and provenance.
- [ ] Verify release assets, checksums, package metadata, provenance and clean installation.
- [ ] Publish the final anonymized GitHub-Final Acceptance Report and Release Lock.
- [ ] Confirm no private project identifier, filename, path, hash, report, business fact or cloud link entered Git history or release assets.

## E. Completion decision

GitHub-Final may be declared `PASS_FOR_OPERATIONAL_RELEASE` only after every remaining item in Section D passes. This closes the initial development program for IntelliDue Production Baseline v1.0.0 and Public Core v1.5.0.

The completion statement is system-level and phase-specific. It does not assert that every private project is Final Full DD or investment-ready, and it does not prevent future versioned improvements.
