# IntelliDue Core

IntelliDue Core is a public, project-neutral control layer for producing preliminary and red-flag due-diligence products from heterogeneous project rooms.

It defines:
- source and evidence controls;
- product-stack and quality-gate contracts;
- deterministic manifests and filesystem reconciliation;
- Current, Archive and Last-success pointers;
- atomic promotion, rollback and crash recovery;
- Reader/Control separation;
- clean-room state recovery;
- public/private data boundaries.

This repository intentionally contains no real project data or reports.

## Status
Production product standard: `v1.0.0`  
Public-core promotion-engine version: `v1.2.0`  
Schema contract version: `v1.0.0`

## Quick check
```bash
python -m unittest discover -s tests -v
intellidue validate-state tests/fixtures/synthetic_project/current_project_state.json
intellidue validate-validation tests/fixtures/synthetic_project/package_validation.json
intellidue validate-contract --state tests/fixtures/synthetic_project/current_project_state.json --lock tests/fixtures/synthetic_project/release_lock.json --validation tests/fixtures/synthetic_project/package_validation.json
intellidue validate-package tests/fixtures/synthetic_project/package.zip
```

## Promotion workspace
```bash
intellidue promote --workspace ./runtime --candidate ./candidate-v1 --release-id v1
intellidue validate-workspace ./runtime
intellidue promote --workspace ./runtime --candidate ./candidate-v2 --release-id v2 --expected-current v1
intellidue rollback --workspace ./runtime --release-id v1 --reason "regression" --expected-current v2
```

The engine writes immutable release directories, deterministic manifests, Current/Last-success pointers, an Archive index and transaction journals. Promotion failures restore the prior pointers and remove an unaccepted release. An unfinished journal requires `intellidue recover` before another writer may proceed.

## Product boundary
The core supports preliminary/red-flag due diligence. A Final Full DD product remains evidence- and professional-signoff-gated.
