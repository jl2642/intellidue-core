# GitHub-Final Acceptance — 2026-07-23

Status: `PASS_FOR_OPERATIONAL_RELEASE`

## 1. Scope

This acceptance closes the initial development program for IntelliDue Production Baseline v1.0.0 and IntelliDue Public Core v1.5.0. It covers repository governance, protected integration, public/private boundary controls, reproducible distribution, immutable release publication and operational recovery controls.

It does not declare any private project to be Final Full DD or investment-ready. Project-level conclusions remain subject to project evidence gates, external procedures and professional signoff.

## 2. Accepted operating model

- ChatGPT in an authorized private workspace is the analysis, research, professional synthesis and report-production engine.
- IntelliDue Core is the public, project-neutral control layer for contracts, validation, packaging, promotion, rollback, recovery, privacy and non-regression.
- Approved private storage holds real project sources and products.
- The public repository contains no real project files, reports, filenames, private hashes, cloud links, business facts or credentials.

## 3. Repository governance

- `main` is protected by an active ruleset.
- Pull requests, current branches and resolved conversations are required.
- Force pushes and deletion are blocked.
- Linear history and squash-only normal merge are enforced.
- Merge commits and rebase merge are disabled at repository level.
- Required GitHub Actions contexts are pinned exactly as:
  - `ci / required`;
  - `dependency-review / dependency review`;
  - `codeql / analyze / python`.
- Protected merge recognition was proven by GitHub-Final PR #10.
- Issue #2 is closed as completed.

## 4. Protected integration proof

GitHub-Final PR #10 was merged without bypass through the protected squash workflow.

- accepted PR head: `02498bcf7ad3e50b46e07c0f1736e84f61bfd790`;
- accepted main/release commit: `012ffbbe0271712408caeae93cd9b6e72fe0ee76`;
- required CI, Dependency Review and CodeQL checks: `PASS`.

## 5. Immutable operational release

- release tag: `core-v1.5.0`;
- release commit: `012ffbbe0271712408caeae93cd9b6e72fe0ee76`;
- package version at tag: `1.5.0`;
- GitHub Release: published, non-draft and non-prerelease;
- source tests: `PASS`;
- repository hygiene: `PASS`;
- distribution metadata: `PASS`;
- candidate clean installation: `PASS`;
- published-wheel clean installation: `PASS`;
- release-asset checksum verification: `PASS`;
- provenance attestation: `PASS`.

Published checksums:

| Asset | SHA-256 |
|---|---|
| `intellidue_core-1.5.0-py3-none-any.whl` | `2f99715a6bb6810c1af0c260f6f9794a54d7728fc24e3b51aca39dfb07e351ef` |
| `intellidue_core-1.5.0.tar.gz` | `091841a5a43626302f3e27d1a3951ccf0059c8248ea0459b496010108906b009` |
| `release-metadata.json` | `b9d80bd04160ebbf70f7aba51bd43535528b13855bb5f9f494062f600aec333f` |

## 6. Prior acceptance chain

- GitHub-0: private/public boundary frozen.
- GitHub-1: repository and CI bootstrap accepted.
- GitHub-2A: strict schemas and cross-object contracts accepted.
- GitHub-2B: manifests, pointers, promotion, rollback and recovery accepted.
- GitHub-2C: stable CLI and strict release packages accepted.
- GitHub-3: CI, dependency controls, CodeQL, reproducible build and release governance accepted.
- GitHub-4: private-runtime adapter accepted on synthetic fixtures.
- GitHub-5: complete authoritative private-project replay accepted without private export.
- GitHub-Final: governance, protected merge and operational release accepted.

## 7. Privacy decision

The GitHub-Final release exported no private project content. Public release artifacts contain only project-neutral code, schemas, package metadata, checksums and provenance. Storage access, sharing permissions and operator behavior remain separate platform and owner responsibilities; this acceptance is a strong workflow and repository boundary, not an absolute guarantee against every account or human failure.

## 8. Completion decision

`PASS_FOR_OPERATIONAL_RELEASE`

IntelliDue Production Baseline v1.0.0 and Public Core v1.5.0 have completed initial development and are authorized for controlled operational use. Future changes must be versioned, regression-tested and merged through the protected repository workflow.
