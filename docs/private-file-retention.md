# Private File Retention

## 1. Objective

The private File Library should preserve only the minimum authoritative assets needed to recover the current system, start a new project and prove the most recent accepted private state. Interim development files, superseded candidates and duplicate exports should not remain in the active library.

## 2. System-level retained assets

Maintain one current copy of each of the following:

1. `START_HERE_CURRENT` - human-readable current system status, scope, version, accepted GitHub commit/release and next action;
2. `PRIVATE_PROJECT_OPERATIONAL_BASELINE` - the current accepted private operational baseline containing Control, Current Reader and Source Registry pointers;
3. `PUBLIC_CORE_RELEASE_POINTER` - machine-readable repository, version, tag, commit, checksums and release status;
4. `NEW_PROJECT_STARTER_PACKAGE` - project-neutral bootstrap templates for identity, intake, Source Registry, Questions, Evidence, conflicts, requests, workpapers, product map and Reader/Control structure;
5. `CLEAN_CHAT_RECOVERY_AND_ACCEPTANCE_PROMPT` - the fixed package-only recovery and portability test instruction;
6. `FILE_LIBRARY_RETENTION_AND_OPERATION_GUIDE` - this retention rule and the new-project role split.

A separate Golden or Regression Fixture may be retained only when it has a defined system-testing purpose and contains no uncontrolled private data.

## 3. Project-level retained assets

For each active private project, maintain:

- one immutable original-intake pointer or source-room snapshot record;
- the current Source Registry and disposition controls;
- the Current private operational release package;
- the immediately previous Last-success release or an Archive pointer to it;
- the current Reader Pack;
- the current Control Pack or workpaper baseline;
- the current open-request, critical-gate and blocked-output status;
- the latest professional sign-off or explicit unsigned limitation record.

The bulk source room normally belongs in the approved private data room, not duplicated into File Library when Google Drive or another controlled repository is the authoritative source.

## 4. Assets to remove from the active library

Remove or archive outside the active File Library:

- failed drafts and repair candidates;
- duplicate DOCX/PDF exports when the accepted package already contains both;
- superseded START_HERE files;
- intermediate phase, batch and test artifacts;
- obsolete manifests and validation reports that are already included in an immutable accepted baseline;
- uncontrolled extracts of real project source files;
- old private packages whose only purpose is satisfied by the Current/Last-success/Archive structure.

## 5. Retention discipline

- File names must include version and acceptance date.
- There must be one unambiguous Current pointer.
- A newer upload does not become Current until validation and release promotion pass.
- File Library is a recovery and handoff layer, not the primary bulk data room.
- Public GitHub never stores the private retained assets described here.
