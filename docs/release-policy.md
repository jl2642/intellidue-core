# Release Policy

## Version and tag

A publishable source tag must be named `core-vX.Y.Z`. The `X.Y.Z` value must exactly match both:

- `[project].version` in `pyproject.toml`;
- `__version__` in `src/intellidue_core/__init__.py`.

The `scripts/release_gate.py` check must pass before artifacts are built.

## Release assets

The workflow builds:

- a Python wheel;
- a source distribution;
- `release-metadata.json`;
- `SHA256SUMS`.

Every checksum is verified before upload. The workflow generates GitHub artifact attestations for the release assets. A GitHub Release is created only from an existing pushed `core-vX.Y.Z` tag.

## Dry run

`workflow_dispatch` performs a full build, test, checksum and attestation dry run. It does not publish a GitHub Release. A dispatch request with `publish=true` is deliberately rejected because publication requires an immutable pushed tag.

## No-license boundary

A release is blocked unless `NO_LICENSE.md` exists and no `LICENSE`, `LICENSE.md`, `LICENSE.txt` or `COPYING` file is present. Public release does not grant external reuse rights.

## Private data boundary

Release metadata states that no private project data is included. The public-repository hygiene test remains a required precondition. Real project packages are never attached to a public release.
