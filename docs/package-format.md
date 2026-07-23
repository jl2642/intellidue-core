# Release Package Format v1.0.0

A strict release package is a directory or ZIP with exactly one package root:

```text
<package_id>/
├─ package.json
├─ manifest.json
└─ payload/
   └─ ... product files ...
```

`package.json` records the package-format version, package ID, release ID, package class, creation time and fixed envelope paths. `manifest.json` records every payload file by relative path, size and SHA-256. The manifest root is always `payload`.

## Profiles

- `auto`: recognize strict release packages; otherwise preserve generic directory or structural ZIP validation.
- `archive`: structural ZIP safety and integrity only.
- `release`: require and validate the complete release-package envelope.

## Safety controls

Validation rejects unsafe paths, duplicate members, case-insensitive collisions, encrypted members, symbolic links, excessive file counts, oversized members, excessive expansion, excessive compression ratios and nested archives beyond the configured depth. Nested ZIP files are recursively inspected.

## Deterministic build

`build-package` sorts all members, uses fixed ZIP metadata, canonical JSON and a caller-supplied timestamp. Identical source content and arguments produce identical bytes and SHA-256. Existing output is not overwritten unless `--overwrite` is explicit.

## Safe extraction

`extract-package` validates the complete strict release package before extraction, writes only beneath the requested destination and refuses an existing destination unless `--overwrite` is explicit.
