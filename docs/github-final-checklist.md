# GitHub-Final Operational Release Checklist

Status: `IN_PROGRESS_OWNER_PLATFORM_CONTROLS_REQUIRED`

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

The repository owner must verify and evidence all items before Issue #2 may close:

- [ ] Require a pull request before merging to `main`.
- [ ] Require `ci / required`.
- [ ] Require Dependency Review using its stable check name.
- [ ] Require CodeQL Python analysis using its stable check name.
- [ ] Require branches to be up to date before merge.
- [ ] Require conversation resolution.
- [ ] Block force pushes and deletion of `main`.
- [ ] Apply the rule to administrators, or document a narrowly controlled emergency bypass.
- [ ] Enable dependency graph.
- [ ] Enable Dependabot alerts.
- [ ] Enable Dependabot security updates.
- [ ] Enable secret scanning.
- [ ] Enable push protection.
- [ ] Enable private vulnerability reporting.
- [ ] Confirm CodeQL advanced setup is active.
- [ ] Retain squash merge as the normal merge method.
- [ ] Disable merge commits and rebase merge for normal work.
- [ ] Enable automatic branch updates where available.
- [ ] Record screenshots/exported evidence, date and account used in Issue #2.

Current repository metadata shows squash, merge-commit and rebase methods are all enabled, and automatic branch updates are disabled. Therefore the merge-policy portion is not yet compliant.

## D. Final source-controlled closure

After Section C is verified:

- [ ] Update Issue #2 with evidence and close it.
- [ ] Update README and Current state to Operational Release.
- [ ] Freeze the operating model, new-project runbook, privacy assurance and private-file retention rules.
- [ ] Run final unit, compatibility, package, privacy, security and reproducible-build checks.
- [ ] Verify the release tag exactly matches package version: `core-v1.5.0`.
- [ ] Push the immutable tag and allow the release workflow to create checksummed assets and provenance.
- [ ] Verify release assets, checksums, package metadata, provenance and clean installation.
- [ ] Publish an anonymized GitHub-Final Acceptance Report and Release Lock.
- [ ] Confirm no private project identifier, filename, path, hash, report, business fact or cloud link entered Git history or release assets.

## E. Completion decision

GitHub-Final may be declared `PASS_FOR_OPERATIONAL_RELEASE` only after every hard item above passes. This closes the initial development program for IntelliDue Production Baseline v1.0.0 and Public Core v1.5.0.

The completion statement is system-level and phase-specific. It does not assert that every private project is Final Full DD or investment-ready, and it does not prevent future versioned improvements.
