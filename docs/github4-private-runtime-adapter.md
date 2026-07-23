# GitHub-4 Private Project Runtime Adapter

## Accepted scope

GitHub-4 adds a project-neutral adapter that runs entirely against caller-supplied local private directories. It provides:

- strict `adapter.json`, runtime-binding and release-receipt schemas;
- project identity binding across adapter, state, release lock and package validation;
- required Reader and Control product roots;
- safe relative-path, symlink, special-file, case-collision and root-overlap controls;
- deterministic private release-package construction;
- immutable local private releases;
- Current, Last-success, Archive, rollback and crash recovery through the accepted core engine;
- per-release control hashes and product summaries;
- cross-project contamination rejection;
- local runtime inspection and validation;
- stable CLI commands and typed errors.

## Deliberate boundary

The adapter does not upload private data to GitHub, does not perform network writes, does not discover cloud data rooms, does not conduct due-diligence analysis and does not generate Reader products. The caller supplies already-controlled state, lock, validation and product directories.

Only synthetic fixtures are committed and exercised in public CI. A real private-project replay belongs to GitHub-5 and must run outside the public repository.

## Phase gate

GitHub-4 may pass when all synthetic adapter, promotion, rollback, recovery, contamination and tamper tests pass across the supported Python matrix. Passing GitHub-4 authorizes GitHub-5 private replay; it does not authorize a formal public release or Final Full DD.
