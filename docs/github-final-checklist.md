# GitHub-Final Operational Release Checklist

Status: `PASS_FOR_OPERATIONAL_RELEASE`

## A. Accepted prerequisites

- [x] GitHub-0 private/public distribution boundary frozen.
- [x] GitHub-1 public repository bootstrap and CI accepted.
- [x] GitHub-2A strict schemas and cross-object contracts accepted.
- [x] GitHub-2B deterministic manifests, pointers, promotion, rollback and recovery accepted.
- [x] GitHub-2C stable CLI and strict release-package validation accepted.
- [x] GitHub-3 CI, dependency controls, CodeQL, reproducible build and release automation accepted.
- [x] GitHub-4 private project runtime adapter accepted on synthetic fixtures.
- [x] GitHub-5 complete authoritative private-project replay accepted and merged to `main`.

## B. Frozen versions and boundaries

- Package version: `1.5.0`.
- Production product standard: `1.0.0`.
- Schema contract: `1.0.0`.
- CLI contract: `1.0.0`.
- Release package format: `1.0.0`.
- Private runtime adapter contract: `1.0.0`.
- No License / all rights reserved remains the authority.
- Real project data in public repository: prohibited.
- Final Full DD: project-evidence and professional-signoff gated.

## C. Repository platform controls

Accepted on 2026-07-23 and recorded in `docs/acceptance/github-final-platform-controls-20260723.md` and Issue #2.

- [x] Require a pull request before merging to `main`.
- [x] Require exact `ci / required` GitHub Actions context.
- [x] Require exact `dependency-review / dependency review` GitHub Actions context.
- [x] Require exact `codeql / analyze / python` GitHub Actions context.
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
- [x] Prove protected merge recognizes all three required checks.

## D. Final source-controlled and release closure

- [x] Freeze the operating model, new-project runbook, privacy assurance and private-file retention rules.
- [x] Merge GitHub-Final PR #10 through the protected `main` workflow.
- [x] Close Issue #2 after protected-gate proof.
- [x] Verify the immutable release tag exactly matches package version: `core-v1.5.0`.
- [x] Pin the tag to accepted main commit `012ffbbe0271712408caeae93cd9b6e72fe0ee76`.
- [x] Publish wheel, source distribution, release metadata and `SHA256SUMS`.
- [x] Verify release-asset checksums.
- [x] Verify distribution metadata.
- [x] Generate provenance attestations.
- [x] Pass source tests and repository hygiene.
- [x] Pass clean installation of both candidate and published wheel.
- [x] Publish the final anonymized GitHub-Final Acceptance Report and Release Lock.
- [x] Confirm no private project identifier, filename, path, hash, report, business fact or cloud link entered Git history or release assets.

## E. Completion decision

GitHub-Final is accepted as `PASS_FOR_OPERATIONAL_RELEASE`.

This closes the initial development program for IntelliDue Production Baseline v1.0.0 and Public Core v1.5.0. The system now enters operational use and versioned maintenance. This completion statement does not assert that every private project is Final Full DD or investment-ready and does not prevent future controlled improvements.
