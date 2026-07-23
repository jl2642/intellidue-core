# IntelliDue Core

IntelliDue Core is a public, project-neutral control layer for producing preliminary and red-flag due-diligence products from heterogeneous project rooms.

It defines:
- source and evidence controls;
- product-stack and quality-gate contracts;
- deterministic manifests and filesystem reconciliation;
- strict release-package construction and validation;
- Current, Archive and Last-success pointers;
- atomic promotion, rollback and crash recovery;
- Reader/Control separation;
- clean-room state recovery;
- public/private data boundaries;
- CI, security scanning and reproducible release controls;
- an offline private-project runtime adapter with project binding and controlled promotion.

This repository intentionally contains no real project data or reports.

## Status

Production product standard: `v1.0.0`  
Public-core private-runtime-adapter version: `v1.5.0`  
Schema contract version: `v1.0.0`  
CLI contract version: `v1.0.0`  
Release package format: `v1.0.0`  
Private-project replay: `PASS_FOR_GITHUB5_FINAL`  
Repository platform controls: `CONDITIONAL_PASS_REQUIRED_CHECK_REBINDING`  
Operational release: `BLOCKED_PROTECTED_MERGE_GATE`

The complete authoritative private-project baseline has passed deterministic build, two-release promotion, Current/Last-success/Archive reconciliation, rollback, crash recovery, cross-project contamination rejection and tamper detection without exporting private project content to GitHub.

GitHub-Final governance and security controls are accepted except for effective required-check binding. PR #10 has successful CI, Dependency Review and CodeQL runs, but the protected merge gate still reports the three checks as expected. The ruleset checks must be rebound before merge, immutable tag creation and final release verification. See `docs/github-final-checklist.md`.

## Operating model

ChatGPT in the authorized private project workspace remains the analysis and professional production engine. IntelliDue Core freezes project-neutral controls and supplies deterministic validation, promotion, rollback, recovery, privacy and non-regression infrastructure. It does not perform due-diligence analysis or generate Reader content.

- `docs/operating-model.md`
- `docs/new-project-runbook.md`
- `docs/private-data-assurance.md`
- `docs/private-file-retention.md`

## Quick check

```bash
python -m unittest discover -s tests -v
intellidue version
intellidue validate-state tests/fixtures/synthetic_project/current_project_state.json
intellidue validate-validation tests/fixtures/synthetic_project/package_validation.json
intellidue validate-contract --state tests/fixtures/synthetic_project/current_project_state.json --lock tests/fixtures/synthetic_project/release_lock.json --validation tests/fixtures/synthetic_project/package_validation.json
intellidue validate-package tests/fixtures/synthetic_project/package.zip
```

## Release package

```bash
intellidue build-package \
  --source ./candidate-v1 \
  --output ./release-v1.zip \
  --package-id release-v1 \
  --release-id v1 \
  --timestamp 2026-07-23T00:00:00Z

intellidue inspect-package ./release-v1.zip --profile release
intellidue validate-package ./release-v1.zip --profile release
intellidue extract-package --package ./release-v1.zip --destination ./extracted
```

The default `auto` package profile preserves structural validation for earlier generic ZIP fixtures. The `release` profile requires `package.json`, `manifest.json` and `payload/`, then reconciles every payload file by path, size and SHA-256.

## Promotion workspace

```bash
intellidue promote --workspace ./runtime --candidate ./candidate-v1 --release-id v1
intellidue validate-workspace ./runtime
intellidue promote --workspace ./runtime --candidate ./candidate-v2 --release-id v2 --expected-current v1
intellidue rollback --workspace ./runtime --release-id v1 --reason "regression" --expected-current v2
```

The promotion engine writes immutable release directories, deterministic manifests, Current/Last-success pointers, an Archive index and transaction journals. Promotion failures restore the prior pointers and remove an unaccepted release. An unfinished journal requires `intellidue recover` before another writer may proceed.

## Private project runtime

The public core can operate against a local private project directory without copying private project data into this repository or performing network writes. A project-controlled `adapter.json` binds the project identity, three control contracts and Reader/Control product roots.

```bash
intellidue validate-private-project --project-root /private/project
intellidue inspect-private-project --project-root /private/project
intellidue build-private-release --project-root /private/project --output /private/releases/project-v1.zip
intellidue promote-private-release --project-root /private/project --runtime /private/runtime
intellidue validate-private-runtime --runtime /private/runtime
intellidue inspect-private-runtime --runtime /private/runtime
```

The runtime is permanently bound to one `project_id`, stores immutable private releases under its own local `core/` workspace, reconciles control hashes and product receipts, and reuses the accepted Current/Archive/Last-success, rollback and recovery engine. The adapter packages existing controlled products; it does not perform due-diligence analysis or generate Reader content.

## Security and release governance

Pull requests are tested across supported Python versions and are subject to package-security regression checks, dependency review and CodeQL analysis. Tag-driven release automation builds wheel and source distributions, verifies checksums and package metadata, creates provenance attestations and publishes a GitHub Release only for an existing `core-vX.Y.Z` tag.

Repository-level administrative controls and the remaining required-check binding defect are recorded in `docs/acceptance/github-final-platform-controls-20260723.md` and repository issue #2.

## Licensing

This public repository deliberately has **no software license**. Public visibility does not grant permission to copy, modify, distribute, sublicense or commercially reuse the code. See `NO_LICENSE.md`.

## Product boundary

The core supports preliminary/red-flag due diligence. A Final Full DD product remains evidence- and professional-signoff-gated.
