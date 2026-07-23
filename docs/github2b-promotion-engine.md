# GitHub-2B Manifest, Pointer & Promotion Engine

## Accepted scope

GitHub-2B implements a project-neutral filesystem promotion engine with:

- deterministic product manifests and file-by-file reconciliation;
- immutable release directories;
- versioned Current and Last-success pointers;
- a versioned Archive index;
- optimistic concurrency through `expected_current`;
- a single-writer workspace lock;
- transaction journals;
- automatic rollback on controlled failures;
- recovery from an unfinished crash journal;
- manual rollback to an existing immutable release;
- typed machine-readable errors and CLI exit codes.

## Workspace layout

```text
workspace/
├─ releases/<release_id>/
├─ manifests/<release_id>.manifest.json
├─ pointers/current.json
├─ pointers/last_success.json
├─ pointers/archive.json
├─ transactions/active.json
├─ transactions/history/<transaction_id>.json
└─ .promotion.lock
```

The active journal exists only while a transaction is incomplete. Finalized transaction records remain in `transactions/history`.

## Promotion sequence

1. Acquire the single-writer lock.
2. Reject an unfinished transaction until recovery is completed.
3. Enforce the expected Current release when supplied.
4. Build and validate the candidate manifest.
5. Copy to a staging release and reconcile every file.
6. Install the immutable release and manifest.
7. Archive the prior Current release.
8. Atomically replace Current and Last-success pointer files.
9. Finalize the transaction journal.

A normal exception restores the previous pointer bytes and removes the unaccepted release. A simulated process crash leaves the journal for `recover` to resolve.

## Deliberate boundary

GitHub-2B does not connect a private project room, run professional due-diligence analysis, or generate Reader products. It also does not yet freeze the complete end-user CLI compatibility contract; that broader command and package-validation surface belongs to GitHub-2C.
