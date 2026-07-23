# Private Runtime Adapter Contract v1.0.0

## Private project input

```text
<project_root>/
├─ adapter.json
├─ control/
│  ├─ current_project_state.json
│  ├─ release_lock.json
│  └─ package_validation.json
└─ products/
   ├─ reader/
   ├─ control/
   └─ supplemental/       # optional
```

`adapter.json` contains only relative paths and declares `private_runtime_only=true`, `public_export_allowed=false`, `allow_external_paths=false` and `allow_symlinks=false`. Reader and Control classes are mandatory and non-empty.

## Runtime layout

```text
<runtime_root>/
├─ private_runtime.json
└─ core/
   ├─ releases/<release_id>/
   ├─ manifests/<release_id>.manifest.json
   ├─ pointers/current.json
   ├─ pointers/last_success.json
   ├─ pointers/archive.json
   └─ transactions/...
```

The binding fixes one `project_id` for the lifetime of the runtime. A different project ID is rejected before promotion.

## Candidate release

Each private release contains the three control JSON documents, Reader/Control/Supplemental products and `runtime/private_runtime_receipt.json`. The receipt records project identity, release ID, accepted product class, decision boundaries, control SHA-256 values, product file counts and total bytes.

## Validation

A private project is accepted only when:

- all three control documents pass their strict schemas and cross-object contract;
- all project IDs match the adapter;
- project state is `CURRENT`;
- package validation is `PASS`;
- required product roots exist and contain files;
- all configured paths stay inside the project root;
- symlinks, special files, root overlap and case collisions are absent.

A runtime is accepted only when the core workspace validates, every release receipt matches the runtime project binding, control hashes reconcile, required products remain present and Current agrees with its receipt.

## Operations

- `validate-private-project` and `inspect-private-project` are read-only.
- `build-private-release` creates a deterministic local strict release package.
- `promote-private-release` creates or verifies the private binding, then atomically promotes an immutable release.
- `validate-private-runtime` and `inspect-private-runtime` are read-only.
- `rollback-private-release` verifies the target private release before changing Current.
- `recover-private-runtime` restores the prior accepted state after an unfinished core transaction.

The adapter never performs network writes. Public repository hygiene remains responsible for preventing private project assets from being committed.
