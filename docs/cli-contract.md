# CLI Contract v1.0.0

Every JSON-producing command returns a stable envelope:

```json
{
  "cli_contract_version": "1.0.0",
  "core_version": "1.5.0",
  "contract_version": "1.0.0",
  "command": "validate-private-project",
  "ok": true,
  "exit_code": 0,
  "issues": []
}
```

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Success |
| 1 | Validation failed |
| 2 | CLI usage or argument error |
| 3 | Operational failure, conflict or filesystem refusal |
| 4 | Unexpected internal error |

Argument errors are emitted as JSON with `CLI_USAGE_ERROR`. Existing commands remain available. GitHub-4 adds `inspect-private-project`, `validate-private-project`, `build-private-release`, `promote-private-release`, `inspect-private-runtime`, `validate-private-runtime`, `rollback-private-release` and `recover-private-runtime`.

## Compatibility

- Existing schema, package and promotion commands retain their names and accepted success behavior.
- `validate-package <path>` preserves the `auto` profile and strict `release` profile.
- Private-runtime commands use the same JSON envelope and exit-code meanings.
- Existing issue codes are not silently redefined within CLI contract version `1.0.0`.
