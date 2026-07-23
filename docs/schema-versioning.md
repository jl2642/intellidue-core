# Schema Versioning

Current contract version: `1.0.0`.

Compatibility rules:

1. Every controlled JSON document carries `schema_version`.
2. Unsupported versions fail before ordinary field validation.
3. Validators never silently coerce, rename or drop fields.
4. Breaking changes require a new contract version and an explicit migration path.
5. Public-core package version and schema contract version are tracked separately.
