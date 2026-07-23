# Schema & Contract Standard v1.0.0

## Scope

GitHub-2A hardens four project-neutral JSON document types: Current Project State, Release Lock, Package Validation and Product Manifest. The schemas use JSON Schema Draft 2020-12, reject unknown fields, require explicit `schema_version`, and are packaged with the Python distribution.

## Compatibility

- Supported schema version: `1.0.0`.
- Missing versions fail with `SCHEMA_VERSION_MISSING`.
- Unknown versions fail with `SCHEMA_VERSION_UNSUPPORTED`.
- Validators never silently coerce, discard or rename fields.

## Cross-object contract

State, Release Lock and Package Validation must agree on project identity, critical gates, restricted outputs and decision readiness. State and Release Lock must also agree on status, accepted product class and next action.

`decision_ready=true` requires zero open critical gates and no restricted outputs. `FINAL_FULL_DD` additionally requires `decision_ready=true`.

## Machine-readable errors

Every CLI response contains `contract_version`, `command`, `ok` and a deterministic `issues` list. Each issue contains `code`, `path`, `message` and `severity`.

## Deliberate boundary

GitHub-2A validates contracts. It does not implement Current/Archive/Last-success promotion, atomic pointer updates, rollback or failure injection; those belong to GitHub-2B.
