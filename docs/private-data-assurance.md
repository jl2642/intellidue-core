# Private Data Assurance

## 1. Security objective

The public IntelliDue Core repository must remain incapable of revealing a real project's identity, source room, reports, filenames, file hashes, cloud links, credentials or business facts.

The control design reduces leakage risk through separation, deny-by-default contracts and public-history scanning. It is not an absolute guarantee against every platform, account, operator or endpoint failure.

## 2. Enforced public/private boundary

The public repository may contain only project-neutral code, schemas, runbooks, synthetic fixtures, CI and anonymized acceptance results.

Real project materials remain in approved private storage and a private project workspace. The private-runtime adapter:

- performs no network writes;
- rejects external and escaping paths;
- rejects symbolic links and special files;
- requires one permanent project identity per runtime;
- requires non-empty Reader and Control roots;
- records controlled product receipts and hashes only inside the private runtime;
- rejects cross-project contamination;
- detects post-promotion tampering;
- preserves immutable releases and controlled rollback/recovery.

## 3. What GitHub can and cannot guarantee

### GitHub / IntelliDue Core can enforce

- no private project content is required in the public repository;
- generic CI runs only on synthetic fixtures;
- repository hygiene can reject prohibited file types, known private identifiers, large binaries and secret patterns;
- private packages can be built and promoted offline;
- a private runtime cannot silently switch to another project identity;
- accepted releases can be reconciled and tampering detected.

### GitHub cannot independently guarantee

- that a user never manually uploads a private file to the wrong repository;
- the security of a user's GitHub, ChatGPT, File Library, Google Drive, device or email account;
- the correctness of cloud sharing permissions;
- that copied text, screenshots or exported files are not shared outside authorized channels;
- deletion or retention behavior of external platforms;
- confidentiality after an authorized recipient downloads a file.

## 4. Operational controls

The project owner should:

- use least-privilege sharing and separate private source rooms by project;
- avoid public links for project sources and products;
- remove obsolete collaborators promptly;
- enable multi-factor authentication and platform security alerts;
- keep credentials, tokens and cloud links out of prompts, documents and repository history;
- review the destination before every upload, commit, share or email;
- retain private acceptance records that prove the public-history leak scan was zero;
- treat any suspected mis-upload as an incident requiring access revocation, history review and credential rotation where applicable.

## 5. Assurance statement

IntelliDue provides a strong architecture for keeping real project data outside the public GitHub repository. The assurance is strongest when the public core is referenced by version or commit, the private runtime remains offline and project-bound, and storage/account permissions are correctly administered. It should be described as a layered risk-control system, not as an unconditional guarantee that leakage is impossible.
