# Schema & Contract Standard v1.0.0

## Scope

GitHub-2A hardens four project-neutral JSON document types:

- Current Project State;
- Release Lock;
- Package Validation;
- Product Manifest.

The schemas use JSON Schema Draft 2020-12, reject unknown top-level and nested fields, require explicit `schema_version`, and are packaged with the Python distribution.

## Compatibility

- Supported schema version: `1.0.0`.
- Missing versions fail with `SCHEMA_VERSION_MISSING`.
- Unknown versions fail with `SCHEMA_VERSION_UNSUPPORTED` before ordinary schema checks.
- A future incompatible schema requires a new version and explicit migration; validators never silently coerce or drop fields.

## Cross-object contract

State, Release Lock and Package Validation must agree on:

- `project_id`;
- critical gates open;
- restricted outputs;
- decision readiness.

State and Release Lock must also agree on:

- accepted product class;
- next authorized action.

`FINAL_FULL_DD` additionally requires zero open critical gates, no restricted outputs and `decision_ready=true`.

## Machine-readable error contract

Every CLI validation response contains:

```json
{
  "contract_version": "1.0.0",
  "command": "validate-state",
  "ok": false,
  "issues": [
    {
      "code": "SCHEMA_VIOLATION",
      "path": "$.project_id",
      "message": "...",
      "severity": "error"
    }
  ]
}
```

Stable error families include schema/version, cross-object contract, manifest semantics and ZIP/package integrity.

## Deliberate boundary

GitHub-2A validates contracts. It does not yet implement Current/Archive/Last-success promotion, atomic pointer updates, rollback or failure injection; those belong to GitHub-2B.
