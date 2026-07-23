# Schema Contract Matrix

| Object | Strict schema | Versioned | Cross-object / semantic checks |
|---|---:|---:|---:|
| Current Project State | Yes | Yes | Yes |
| Release Lock | Yes | Yes | Yes |
| Package Validation | Yes | Yes | Yes |
| Product Manifest | Yes | Yes | File paths, order and filesystem reconciliation |
| Package Descriptor | Yes | Yes | Package root, envelope and payload-manifest reconciliation |
| Current / Last-success Pointer | Yes | Yes | Target, manifest and pointer-type checks |
| Archive Index | Yes | Yes | Unique ordered releases and target reconciliation |

GitHub-2C adds strict package-envelope validation while preserving the existing schema contract version `1.0.0`.
