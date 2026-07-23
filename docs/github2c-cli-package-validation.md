# GitHub-2C CLI & Package Validation

GitHub-2C freezes the public command contract and strict release-package format.

Accepted scope:

- stable JSON command envelope and documented exit codes;
- compatibility-preserving package profiles;
- deterministic package build;
- package inspection and strict validation;
- safe extraction;
- recursive ZIP inspection and configurable resource limits;
- package descriptor schema and payload-manifest reconciliation;
- CI package lifecycle smoke test.

Deliberate boundary:

- no private project adapter;
- no private source-room ingestion;
- no due-diligence analysis or Reader generation;
- no repository Release automation, branch protection or security-setting closure, which belong to GitHub-3.
