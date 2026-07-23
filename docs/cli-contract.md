# CLI Contract v1.0.0

Every JSON-producing command returns a stable envelope:

```json
{
  "cli_contract_version": "1.0.0",
  "core_version": "1.3.0",
  "contract_version": "1.0.0",
  "command": "validate-package",
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

Argument errors are emitted as JSON with `CLI_USAGE_ERROR`. Existing commands remain available; GitHub-2C adds `version`, `inspect-package`, `build-package` and `extract-package`.

## Compatibility

- Existing schema and promotion commands retain their names and accepted success behavior.
- `validate-package <path>` remains compatible with the earlier structural ZIP check through the default `auto` profile.
- `--profile release` requires the strict IntelliDue release-package envelope.
- Existing issue codes are not silently redefined within CLI contract version 1.0.0.
