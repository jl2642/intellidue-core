# GitHub-Final Platform Controls Acceptance — 2026-07-23

Status: `REVALIDATING_REQUIRED_CHECK_BINDING`

## Evidence basis

The repository owner completed the platform settings and supplied owner-view screenshots for the effective repository configuration. Connected repository metadata was then re-read after the change.

The evidence confirms:

- an active ruleset targets the default branch (`main`);
- pull requests are required before merge;
- conversation resolution is required;
- the intended required status checks are `ci / required`, `dependency-review / dependency review`, and `codeql / analyze / python`;
- branches must be up to date before merge;
- force pushes and branch deletion are blocked;
- no routine bypass entry is configured;
- linear history is required and the ruleset permits squash only;
- repository-level merge commits and rebase merges are disabled;
- squash merge remains enabled;
- pull-request branch update suggestions are enabled;
- dependency graph, Dependabot alerts and Dependabot security updates are enabled;
- private vulnerability reporting is enabled;
- CodeQL advanced setup is active and passing;
- the owner confirmed secret scanning and push protection after completing the requested settings.

## Independent metadata confirmation

After the owner changes, repository metadata independently reported:

- `allow_merge_commit = false`;
- `allow_rebase_merge = false`;
- `allow_squash_merge = true`;
- `allow_update_branch = true`.

## Required-check binding revalidation

A protected merge attempt previously reported all three required checks as `expected` despite successful workflow runs. The owner then removed and reselected the three checks from the current GitHub Actions identities, with `GitHub Actions` shown as the source for each check.

This commit intentionally triggers a fresh PR validation set. GitHub-Final will accept the required-check binding only when the latest head receives successful CI, Dependency Review and CodeQL results and the protected squash merge recognizes them.

## Administrator and emergency posture

The ruleset has no routine bypass entry. Emergency owner intervention, if ever required, must be exceptional, documented in an issue, followed by immediate restoration of the rule and a post-event audit. Normal changes use pull requests and squash merge.

## Decision

The platform configuration is provisionally accepted and is undergoing final required-check binding revalidation. Issue #2 remains open until the protected merge gate recognizes all three successful checks. This acceptance does not authorize private project data, reports, identifiers, paths, hashes, cloud links or business facts to enter the public repository or its workflow artifacts.
