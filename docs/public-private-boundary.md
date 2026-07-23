# Public GitHub Core / Private Project Boundary

## Public repository may contain
- generic architecture, standards, schemas and runbooks;
- validators, manifest and pointer utilities;
- synthetic fixtures with fictional data;
- CI workflows and contribution/security policies;
- generic document templates without project facts.

## Public repository must not contain
- client or project names and IDs;
- source filenames, folder structures, hashes or file inventories;
- contracts, financial figures, operating metrics or legal findings;
- Reader or Control packages from a real project;
- private prompts containing project-specific facts;
- personal information, credentials, access tokens or cloud links.

## Private environment contains
- project source rooms and Source Registry;
- workpapers, Reader/Control packages and acceptance records;
- Current/Archive/Last-success project pointers;
- reviewer names, signatures and commercial decisions.

## Enforcement
The public CI must scan for prohibited extensions, known project identifiers, large binaries and secret patterns. Private project repositories should be separate and access-controlled; they should reference the public core by version or commit, not copy private data into the public repository.
