# Public Repository Disclosure Audit — 2026-08-07

## Scope

This review covers the public `jl2642/intellidue-core` repository at the then-current `main` baseline and the public GitHub surfaces available through the connected account: tracked tree, current repository text search, commit messages, recent pull-request descriptions, public security/data-boundary documents and repository metadata.

This is a disclosure-control review, not a cryptographic guarantee that no external cache, fork or previously downloaded copy can exist.

## Result

`PUBLIC_REPOSITORY_DISCLOSURE_AUDIT = PASS_AFTER_MINOR_METADATA_REMEDIATION`

The current tracked repository remains project-neutral. No real project source files, private System Current package, deployment package, office-document source room, client/transaction facts, private source hashes, cloud share links, API keys, passwords or obvious secret tokens were identified in the reviewed current tree/search surfaces.

## Current-tree controls observed

- the tracked tree is code / schemas / runbooks / tests plus one tiny approved synthetic ZIP fixture;
- `.gitignore` excludes ZIPs by default (except the explicit synthetic fixture), PDF/DOCX/XLSX files and `private/`, `projects/`, `secrets/` directories;
- repository hygiene code rejects prohibited project-file types, unapproved ZIPs, large files and configured private identifiers;
- `SECURITY.md` explicitly prohibits real project sources, filenames, hashes, workpapers, Reader products, commercial facts, legal findings, signatures, tokens and private cloud links;
- public/private assurance documentation keeps real project materials outside GitHub and treats operator/account/platform risk as residual risk rather than claiming zero leakage risk.

## Search checks

Public repository content searches returned no current-tree matches for the reviewed real-project identifiers or for representative sensitive patterns including project codenames, company identifiers, `OPENAI_API_KEY`, `password`, `secret`, `sk-`, `drive.google`, `chatgpt.com/share`, `sandbox:/`, `INTELLIDUE_SYSTEM_CURRENT.zip` and `DEPLOYMENT_PACKAGE`.

## Historical / collaboration-surface finding

One legacy merged pull-request description contained a real project codename in a sentence stating that no such project data was committed. The wording has been generalized to remove the codename from the currently displayed PR description. No associated project facts, filenames, hashes, source data or Reader content were present in that PR.

This is treated as a **minor metadata disclosure**, not a source-room or business-data leak. Because public GitHub content may be cached, copied or archived externally, remediation reduces current visibility but cannot guarantee deletion of every historical external copy.

## Repository-owner metadata

Normal Git/GitHub author metadata may expose repository-owner account information associated with commits. This audit does not classify owner account metadata as private project data. Future commits may use GitHub-provided no-reply addresses if the maintainer wants to minimize public personal contact metadata.

## Public / private release boundary

Safe to publish:

- README / product overview;
- project-neutral Core code;
- schemas / validators;
- synthetic fixtures;
- public-safe architecture, security and acceptance documents.

Do not publish:

- `INTELLIDUE_SYSTEM_CURRENT.zip` or recovery baseline packages;
- IntelliDue Deployment Package;
- real project sources, workpapers or reports;
- source-room filenames / hashes / private locators;
- commercial, legal, financial or transaction facts;
- private cloud links, credentials or tokens.

## Conclusion

The public repository is suitable for a lightweight product showcase **provided the public/private boundary remains unchanged**. Promotional changes should stay documentation-only, use project-neutral examples, and keep the complete private operational system and all real Case data outside the repository.
