# IntelliDue Core

IntelliDue Core is a public, project-neutral control layer for producing preliminary and red-flag due-diligence products from heterogeneous project rooms.

It defines:
- source and evidence controls;
- product-stack and quality-gate contracts;
- deterministic manifests, pointers and package validation;
- Reader/Control separation;
- clean-room state recovery;
- public/private data boundaries.

This repository intentionally contains no real project data or reports.

## Status
Production product standard: `v1.0.0`  
Public-core contract-hardening version: `v1.1.0`

## Quick check
```bash
python -m unittest discover -s tests -v
intellidue validate-state tests/fixtures/synthetic_project/current_project_state.json
intellidue validate-package tests/fixtures/synthetic_project/package.zip
intellidue validate-validation tests/fixtures/synthetic_project/package_validation.json
intellidue validate-contract --state tests/fixtures/synthetic_project/current_project_state.json --lock tests/fixtures/synthetic_project/release_lock.json --validation tests/fixtures/synthetic_project/package_validation.json
```

## Product boundary
The core supports preliminary/red-flag due diligence. A Final Full DD product remains evidence- and professional-signoff-gated.
