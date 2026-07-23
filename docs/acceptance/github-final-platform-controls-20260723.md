# GitHub-Final Platform Controls Acceptance — 2026-07-23

Status: `PASS_PLATFORM_CONTROLS`

## Evidence basis

The repository owner completed the platform settings and supplied owner-view screenshots for the effective repository configuration. Connected repository metadata and protected-merge behavior were then independently rechecked.

The accepted configuration includes:

- an active ruleset targeting the default branch (`main`);
- pull requests required before merge;
- conversation resolution required;
- branches required to be up to date before merge;
- force pushes and branch deletion blocked;
- no routine bypass entry;
- linear history and squash-only normal merge policy;
- repository-level merge commits and rebase merge disabled;
- pull-request branch update suggestions enabled;
- dependency graph, Dependabot alerts and Dependabot security updates enabled;
- private vulnerability reporting enabled;
- secret scanning and push protection confirmed by the owner;
- CodeQL advanced setup active and passing.

## Stable required-check identities

The protected branch requires these exact GitHub Actions check-run contexts:

- `ci / required`;
- `dependency-review / dependency review`;
- `codeql / analyze / python`.

The workflow job names were explicitly pinned to those contexts. A fresh validation set completed successfully and the protected merge endpoint then recognized the checks, first reporting only the still-running dependency check and subsequently accepting the squash merge after completion.

## Independent metadata confirmation

Repository metadata reported:

- `allow_merge_commit = false`;
- `allow_rebase_merge = false`;
- `allow_squash_merge = true`;
- `allow_update_branch = true`.

## Protected merge proof

GitHub-Final PR #10 merged through the protected squash-only workflow without bypass.

- accepted head: `02498bcf7ad3e50b46e07c0f1736e84f61bfd790`;
- resulting main commit: `012ffbbe0271712408caeae93cd9b6e72fe0ee76`;
- Issue #2: closed as completed after merge proof.

## Administrator and emergency posture

The ruleset has no routine bypass entry. Emergency owner intervention, if ever required, must be exceptional, documented in an issue, followed by immediate restoration of the rule and a post-event audit. Normal changes use pull requests and squash merge.

## Decision

Repository governance, security settings, stable required checks and protected-merge enforcement satisfy the GitHub-Final platform-control gate. This acceptance does not authorize private project data, reports, identifiers, paths, hashes, cloud links or business facts to enter the public repository or its workflow artifacts.
