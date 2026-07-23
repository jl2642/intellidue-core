# GitHub-3 CI, Security & Release Automation

## Accepted code-managed scope

GitHub-3 adds:

- a supported-Python CI matrix;
- an immutable `ci / required` merge-gate check;
- explicit archive-security regression tests;
- wheel and source-distribution build verification;
- Dependency Review for pull requests;
- CodeQL advanced scanning for Python;
- Dependabot version-update configuration for pip and GitHub Actions;
- CODEOWNERS and a vulnerability-reporting policy;
- explicit No License / all-rights-reserved posture;
- a tag-driven release workflow with checksums, provenance attestations and GitHub Release publication;
- version and license validation before release.

## Administrative controls

Some controls live in GitHub repository settings rather than source code. They remain tracked in issue #2 and `docs/repository-settings.md`:

- main-branch rules or protection;
- required status checks;
- secret scanning and push protection confirmation;
- Dependabot alerts and security updates;
- merge-method restrictions;
- private vulnerability reporting.

These settings must be confirmed before GitHub-Final. The absence of a connector action for an administrative setting must not be misreported as completion.

## Deliberate boundary

GitHub-3 does not connect a private project workspace, ingest real project files, perform due-diligence analysis or generate Reader products. Those functions remain outside the public repository.
