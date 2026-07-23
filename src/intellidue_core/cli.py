from __future__ import annotations

import argparse
import json

from .contracts import SCHEMA_VERSION
from .manifest import save_manifest
from .validators import (
    validate_contract_files,
    validate_manifest,
    validate_package_validation,
    validate_release_lock,
    validate_state,
    validate_zip,
)


def _result(command: str, issues) -> int:
    payload = {
        "contract_version": SCHEMA_VERSION,
        "command": command,
        "ok": not issues,
        "issues": [issue.to_dict() for issue in issues],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not issues else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="intellidue")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("validate-state", "validate-lock", "validate-validation", "validate-manifest", "validate-package"):
        command = sub.add_parser(name)
        command.add_argument("path")
    command = sub.add_parser("validate-contract")
    command.add_argument("--state", required=True)
    command.add_argument("--lock", required=True)
    command.add_argument("--validation", required=True)
    command = sub.add_parser("build-manifest")
    command.add_argument("root")
    command.add_argument("output")

    args = parser.parse_args(argv)
    if args.cmd == "validate-state":
        return _result(args.cmd, validate_state(args.path))
    if args.cmd == "validate-lock":
        return _result(args.cmd, validate_release_lock(args.path))
    if args.cmd == "validate-validation":
        return _result(args.cmd, validate_package_validation(args.path))
    if args.cmd == "validate-manifest":
        return _result(args.cmd, validate_manifest(args.path))
    if args.cmd == "validate-package":
        return _result(args.cmd, validate_zip(args.path))
    if args.cmd == "validate-contract":
        return _result(args.cmd, validate_contract_files(args.state, args.lock, args.validation))

    save_manifest(args.root, args.output)
    print(json.dumps({"contract_version": SCHEMA_VERSION, "command": args.cmd, "ok": True, "output": args.output}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
