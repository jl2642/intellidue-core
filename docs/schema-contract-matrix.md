# Schema Contract Matrix

| Object | Strict schema | Versioned | Cross-object / semantic checks |
|---|---:|---:|---:|
| Current Project State | Yes | Yes | Yes |
| Release Lock | Yes | Yes | Yes |
| Package Validation | Yes | Yes | Yes |
| Product Manifest | Yes | Yes | File paths, order and filesystem reconciliation |
| Current / Last-success Pointer | Yes | Yes | Target, manifest and pointer-type checks |
| Archive Index | Yes | Yes | Unique ordered releases and target reconciliation |

Promotion, automatic rollback, crash recovery and manual rollback are implemented in GitHub-2B. Private project adapters remain outside the public core.
