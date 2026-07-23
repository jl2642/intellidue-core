# GitHub-5 Real Private Project Replay

## Purpose

GitHub-5 proves that the accepted private-runtime adapter can operate against a genuine private project outside the public repository. It is an operational acceptance step, not a due-diligence analysis step and not a public release.

## Required private inputs

Prepare four caller-controlled private project roots that all satisfy the Private Runtime Adapter Contract:

1. `v1`: the first accepted private release;
2. `v2`: a controlled incremental release for the same project;
3. `crash`: a third release for the same project, reserved for failure injection and recovery;
4. `contamination`: a synthetic project with a different `project_id`.

The real project roots must remain outside the repository and outside public CI. The contamination root must be synthetic and must contain no second real project.

## Fixed replay sequence

Run `scripts/run_private_replay_acceptance.py` in a private working directory. The runner:

- validates and inspects all four private project roots;
- builds `v1` twice with the same timestamp and requires identical SHA-256 results;
- promotes `v1` into a new project-bound runtime;
- promotes `v2` with `expected_current=v1`;
- reconciles Current, Last-success and Archive;
- rolls back to `v1` and validates the runtime;
- injects a controlled crash after Current mutation and requires fail-closed recovery;
- rejects the synthetic cross-project promotion with `PRIVATE_RUNTIME_PROJECT_CONFLICT`;
- writes an anonymized JSON result only.

Example:

```bash
python scripts/run_private_replay_acceptance.py \
  --v1-project /private/project-v1 \
  --v2-project /private/project-v2 \
  --crash-project /private/project-v3-crash \
  --contamination-project /private/synthetic-other \
  --runtime /private/github5-runtime \
  --work-dir /private/github5-work \
  --output /private/github5-public-result.json \
  --timestamp 2026-07-23T06:30:00Z
```

The runtime and work directory must not exist before the run. This prevents an acceptance run from silently reusing prior state.

## Public result boundary

The output may contain gate names, PASS/FAIL states, core and adapter versions, and boolean privacy assertions. It must not contain:

- a real project identity or name;
- a private filename or filesystem path;
- a source, control-document or product hash;
- a business fact or Reader excerpt;
- a private runtime, package or transaction journal.

On failure, the runner exports only the exception type, not the exception message, because messages may contain private paths or identifiers.

## Acceptance gate

GitHub-5 passes only when the complete frozen private operational baseline is mounted, every replay step passes, the anonymized result passes a leak scan, and no private asset enters public Git history or public CI artifacts.

A controlled real-project subset may prove the runner and adapter path, but it authorizes only a complete-baseline replay. It is not GitHub-5 Final acceptance.
