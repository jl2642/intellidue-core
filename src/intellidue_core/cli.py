from __future__ import annotations

import argparse
import json

from .contracts import SCHEMA_VERSION, ValidationIssue
from .manifest import save_manifest, verify_manifest_file
from .promotion import PromotionError, promote_release, recover_workspace, rollback_release, validate_workspace
from .validators import (
    validate_archive, validate_contract_files, validate_manifest,
    validate_package_validation, validate_pointer, validate_release_lock,
    validate_state, validate_zip,
)


def _result(command: str, issues, **extra) -> int:
    payload = {
        "contract_version": SCHEMA_VERSION,
        "command": command,
        "ok": not issues,
        "issues": [issue.to_dict() for issue in issues],
        **extra,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not issues else 1


def _execute(command: str, operation):
    try:
        result = operation()
    except PromotionError as exc:
        return _result(command, [exc.issue])
    return _result(command, [], result=result)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="intellidue")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("validate-state", "validate-lock", "validate-validation", "validate-manifest", "validate-pointer", "validate-archive", "validate-package"):
        command = sub.add_parser(name)
        command.add_argument("path")
    command = sub.add_parser("validate-contract")
    command.add_argument("--state", required=True)
    command.add_argument("--lock", required=True)
    command.add_argument("--validation", required=True)
    command = sub.add_parser("build-manifest")
    command.add_argument("root")
    command.add_argument("output")
    command.add_argument("--root-name")
    command = sub.add_parser("verify-manifest")
    command.add_argument("root")
    command.add_argument("manifest")
    command = sub.add_parser("validate-workspace")
    command.add_argument("workspace")
    command = sub.add_parser("promote")
    command.add_argument("--workspace", required=True)
    command.add_argument("--candidate", required=True)
    command.add_argument("--release-id", required=True)
    command.add_argument("--expected-current")
    command.add_argument("--transaction-id")
    command.add_argument("--timestamp")
    command = sub.add_parser("rollback")
    command.add_argument("--workspace", required=True)
    command.add_argument("--release-id", required=True)
    command.add_argument("--reason", required=True)
    command.add_argument("--expected-current")
    command.add_argument("--transaction-id")
    command.add_argument("--timestamp")
    command = sub.add_parser("recover")
    command.add_argument("--workspace", required=True)
    command.add_argument("--force-lock", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "validate-state":
        return _result(args.cmd, validate_state(args.path))
    if args.cmd == "validate-lock":
        return _result(args.cmd, validate_release_lock(args.path))
    if args.cmd == "validate-validation":
        return _result(args.cmd, validate_package_validation(args.path))
    if args.cmd == "validate-manifest":
        return _result(args.cmd, validate_manifest(args.path))
    if args.cmd == "validate-pointer":
        return _result(args.cmd, validate_pointer(args.path))
    if args.cmd == "validate-archive":
        return _result(args.cmd, validate_archive(args.path))
    if args.cmd == "validate-package":
        return _result(args.cmd, validate_zip(args.path))
    if args.cmd == "validate-contract":
        return _result(args.cmd, validate_contract_files(args.state, args.lock, args.validation))
    if args.cmd == "verify-manifest":
        return _result(args.cmd, verify_manifest_file(args.root, args.manifest))
    if args.cmd == "validate-workspace":
        return _result(args.cmd, validate_workspace(args.workspace))
    if args.cmd == "promote":
        return _execute(args.cmd, lambda: promote_release(args.workspace, args.candidate, args.release_id, expected_current=args.expected_current, transaction_id=args.transaction_id, timestamp=args.timestamp))
    if args.cmd == "rollback":
        return _execute(args.cmd, lambda: rollback_release(args.workspace, args.release_id, args.reason, expected_current=args.expected_current, transaction_id=args.transaction_id, timestamp=args.timestamp))
    if args.cmd == "recover":
        return _execute(args.cmd, lambda: recover_workspace(args.workspace, force_lock=args.force_lock))

    manifest = save_manifest(args.root, args.output, root_name=args.root_name)
    return _result(args.cmd, [], output=args.output, manifest=manifest)


if __name__ == "__main__":
    raise SystemExit(main())
