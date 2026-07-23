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
| Private Project Adapter | Yes | Yes | Project identity, safe paths and product-root controls |
| Private Runtime Binding | Yes | Yes | Single-project runtime isolation |
| Private Runtime Receipt | Yes | Yes | Control hashes, products and decision-boundary reconciliation |

GitHub-4 adds the private runtime adapter contract while preserving schema contract version `1.0.0`.
