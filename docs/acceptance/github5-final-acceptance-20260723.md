# GitHub-5 Real Private Project Replay — Final Acceptance

Status: **PASS_FOR_GITHUB5_FINAL**

## Accepted execution

The authoritative frozen private operational baseline was mounted outside the public repository and replayed through IntelliDue Core `1.5.0` / Private Runtime Adapter `1.0.0`.

The complete replay passed:

- authoritative outer archive identity and integrity verification;
- nested accepted Reader-package integrity verification;
- archive security checks for unsafe paths, case collisions, corruption and symbolic links;
- frozen source-registry snapshot reconciliation;
- strict private-project validation and inspection;
- deterministic private release construction;
- strict release-package validation;
- first immutable promotion into a new project-bound runtime;
- controlled incremental second promotion with `expected_current`;
- Current, Last-success and Archive reconciliation;
- preservation of the authoritative baseline unchanged inside accepted releases;
- validated rollback to the prior accepted release;
- controlled crash after Current mutation, fail-closed detection and recovery;
- cross-project contamination rejection using a synthetic second identity;
- post-promotion tamper detection on a disposable runtime copy;
- final runtime reconciliation to the accepted rollback target.

No business conclusion was changed, no open critical gate was closed and no restricted output was restored during the replay.

## Public/private boundary

No real project identity, private filename, filesystem path, source or product hash, Reader content, business fact, private package, runtime or transaction journal was committed to the public repository or uploaded to public CI.

The public acceptance record contains only anonymized gate results and version information.

## Phase decision

GitHub-5 is accepted. The private-project runtime adapter has now passed both synthetic public-CI validation and complete authoritative private-baseline replay.

This acceptance authorizes merge of the generic replay runner and anonymized acceptance record into `main`. It does not authorize publication of private project assets, a formal public release tag, or reclassification of the underlying due-diligence product as Final Full DD.
