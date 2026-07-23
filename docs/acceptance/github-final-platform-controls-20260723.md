# GitHub-Final Platform Controls Acceptance — 2026-07-23

Status: `PASS_PLATFORM_CONTROLS`

## Evidence basis

The repository owner completed the platform settings and supplied owner-view screenshots for the effective repository configuration. Connected repository metadata was then re-read after the change.

The evidence confirms:

- an active ruleset targets the default branch (`main`);
- pull requests are required before merge;
- conversation resolution is required;
- required status checks are `ci / required`, `dependency-review / dependency review`, and `codeql / analyze / python`;
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

PR #10 workflow runs for CI, Dependency Review and CodeQL all completed successfully.

## Administrator and emergency posture

The ruleset has no routine bypass entry. Emergency owner intervention, if ever required, must be exceptional, documented in an issue, followed by immediate restoration of the rule and a post-event audit. Normal changes use pull requests and squash merge.

## Decision

Repository platform controls satisfy the GitHub-Final governance gate. Issue #2 may close. This acceptance does not authorize private project data, reports, identifiers, paths, hashes, cloud links or business facts to enter the public repository or its workflow artifacts.
