# GitHub-5 Real Private Project Replay — Interim Acceptance

Status: **PASS_FOR_AUTHORITATIVE_BASELINE_REPLAY**

## What was executed

A controlled real-project subset was mounted outside the public repository and replayed through IntelliDue Core `1.5.0` / Private Runtime Adapter `1.0.0`. No public CI job or GitHub commit received private project content.

The following gates passed:

- strict private-project validation and inspection;
- deterministic release build with identical outputs for identical inputs and timestamp;
- first immutable promotion into a new project-bound runtime;
- controlled incremental second promotion with `expected_current`;
- Current, Last-success and Archive reconciliation;
- validated rollback to the prior accepted release;
- controlled crash after Current mutation, fail-closed detection and recovery;
- cross-project contamination rejection using a synthetic second identity;
- final runtime validation and privacy scan.

## Deliberate limitation

The authoritative private operational baseline archive was not mounted in the active execution environment. Therefore this run proves that the adapter works against genuine private project products, but it does not yet prove byte-for-byte replay of the complete frozen private baseline.

GitHub-5 Final remains blocked until the accepted private operational baseline archive is mounted and the same sequence is rerun against that complete baseline.

## Public/private boundary

This report contains no real project filename, project fact, private source hash, control-document hash or Reader content. The public repository may receive this interim status and a generic replay runner only; it must not receive the private runtime, packages or logs.

## Next gate

Mount the authoritative private operational baseline archive, rerun the fixed replay sequence, and change status to `PASS_FOR_GITHUB_FINAL` only if all gates pass and the public-history leak scan remains zero.
