# Repository Administrative Settings

Source-controlled workflows cannot prove or change every repository-level setting. The repository owner must confirm these settings in GitHub before GitHub-Final.

## Main branch rule

Target: `main`

Required configuration:

- require a pull request before merging;
- require status checks to pass;
- require the stable `ci / required` check;
- require `dependency-review / dependency review`;
- require `codeql / analyze / python` after its check name is confirmed;
- require branches to be up to date before merging;
- block force pushes and branch deletion;
- require conversation resolution;
- apply the rule to administrators unless an emergency bypass is explicitly recorded.

## Security settings

Confirm:

- dependency graph enabled;
- Dependabot alerts enabled;
- Dependabot security updates enabled;
- secret scanning enabled;
- push protection enabled;
- private vulnerability reporting enabled;
- CodeQL advanced setup active and producing results.

## Merge policy

Recommended:

- allow squash merge;
- disable merge commits and rebase merge for normal work;
- enable automatic branch updates;
- optionally enable auto-merge after required checks pass.

## License posture

The repository intentionally has no software license. `NO_LICENSE.md` is the authority. Do not add a standard open-source license without a separate owner decision and a new release review.

## Evidence

Record screenshots or exported settings, required-check names and the completion date in issue #2. Close issue #2 only after every platform setting is verified.
