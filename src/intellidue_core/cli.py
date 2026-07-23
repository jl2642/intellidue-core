from __future__ import annotations

import argparse
import json
from typing import Callable

from . import __version__
from .contracts import SCHEMA_VERSION, ValidationIssue
from .manifest import save_manifest, verify_manifest_file
from .package_format import PackageLimits, build_release_package, extract_release_package, inspect_package
from .promotion import PromotionError, promote_release, recover_workspace, rollback_release, validate_workspace
from .validators import validate_archive, validate_contract_files, validate_manifest, validate_package_validation, validate_pointer, validate_release_lock, validate_state

CLI_CONTRACT_VERSION = "1.0.0"
PACKAGE_FORMAT_VERSION = "1.0.0"
EXIT_OK = 0
EXIT_VALIDATION_FAILED = 1
EXIT_USAGE_ERROR = 2
EXIT_OPERATION_FAILED = 3
EXIT_INTERNAL_ERROR = 4


class CLIUsageError(Exception):
    pass


class ContractArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CLIUsageError(message)


def _payload(command: str, issues, exit_code: int, **extra) -> dict:
    return {
        "cli_contract_version": CLI_CONTRACT_VERSION,
        "core_version": __version__,
        "contract_version": SCHEMA_VERSION,
        "command": command,
        "ok": exit_code == EXIT_OK,
        "exit_code": exit_code,
        "issues": [issue.to_dict() for issue in issues],
        **extra,
    }


def _emit(command: str, issues=(), *, exit_code: int | None = None, **extra) -> int:
    issues = list(issues)
    if exit_code is None:
        exit_code = EXIT_OK if not issues else EXIT_VALIDATION_FAILED
    print(json.dumps(_payload(command, issues, exit_code, **extra), indent=2, sort_keys=True))
    return exit_code


def _execute(command: str, operation: Callable[[], object]) -> int:
    try:
        result = operation()
    except PromotionError as exc:
        return _emit(command, [exc.issue], exit_code=EXIT_OPERATION_FAILED)
    except FileExistsError as exc:
        return _emit(command, [ValidationIssue("DESTINATION_EXISTS", "$", str(exc))], exit_code=EXIT_OPERATION_FAILED)
    except ValueError as exc:
        return _emit(command, [ValidationIssue("OPERATION_INVALID", "$", str(exc))], exit_code=EXIT_OPERATION_FAILED)
    except OSError as exc:
        return _emit(command, [ValidationIssue("FILESYSTEM_ERROR", "$", str(exc))], exit_code=EXIT_OPERATION_FAILED)
    return _emit(command, result=result)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value cannot be negative")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _limits(args) -> PackageLimits:
    return PackageLimits(max_entries=args.max_entries, max_total_uncompressed=args.max_total_uncompressed, max_member_uncompressed=args.max_member_uncompressed, max_compression_ratio=args.max_compression_ratio, max_nested_depth=args.max_nested_depth)


def _add_package_options(command) -> None:
    command.add_argument("--profile", choices=("auto", "archive", "release"), default="auto")
    command.add_argument("--max-entries", type=_positive_int, default=10_000)
    command.add_argument("--max-total-uncompressed", type=_positive_int, default=1_073_741_824)
    command.add_argument("--max-member-uncompressed", type=_positive_int, default=268_435_456)
    command.add_argument("--max-compression-ratio", type=_positive_float, default=200.0)
    command.add_argument("--max-nested-depth", type=_nonnegative_int, default=2)


def build_parser() -> argparse.ArgumentParser:
    parser = ContractArgumentParser(prog="intellidue")
    parser.add_argument("--version", action="version", version=f"intellidue-core {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True, parser_class=ContractArgumentParser)
    sub.add_parser("version")
    for name in ("validate-state", "validate-lock", "validate-validation", "validate-manifest", "validate-pointer", "validate-archive"):
        command = sub.add_parser(name)
        command.add_argument("path")
    command = sub.add_parser("validate-package")
    command.add_argument("path")
    _add_package_options(command)
    command = sub.add_parser("inspect-package")
    command.add_argument("path")
    _add_package_options(command)
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
    command = sub.add_parser("build-package")
    command.add_argument("--source", required=True)
    command.add_argument("--output", required=True)
    command.add_argument("--package-id", required=True)
    command.add_argument("--release-id", required=True)
    command.add_argument("--timestamp")
    command.add_argument("--overwrite", action="store_true")
    command = sub.add_parser("extract-package")
    command.add_argument("--package", required=True)
    command.add_argument("--destination", required=True)
    command.add_argument("--overwrite", action="store_true")
    _add_package_options(command)
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
    return parser


def _dispatch(args) -> int:
    command = args.cmd
    if command == "version":
        return _emit(command, version={"core": __version__, "schema_contract": SCHEMA_VERSION, "cli_contract": CLI_CONTRACT_VERSION, "package_format": PACKAGE_FORMAT_VERSION})
    if command == "validate-state": return _emit(command, validate_state(args.path))
    if command == "validate-lock": return _emit(command, validate_release_lock(args.path))
    if command == "validate-validation": return _emit(command, validate_package_validation(args.path))
    if command == "validate-manifest": return _emit(command, validate_manifest(args.path))
    if command == "validate-pointer": return _emit(command, validate_pointer(args.path))
    if command == "validate-archive": return _emit(command, validate_archive(args.path))
    if command in {"validate-package", "inspect-package"}:
        inspection, issues = inspect_package(args.path, profile=args.profile, limits=_limits(args))
        return _emit(command, issues, inspection=inspection.to_dict())
    if command == "validate-contract": return _emit(command, validate_contract_files(args.state, args.lock, args.validation))
    if command == "verify-manifest": return _emit(command, verify_manifest_file(args.root, args.manifest))
    if command == "validate-workspace": return _emit(command, validate_workspace(args.workspace))
    if command == "build-manifest": return _execute(command, lambda: {"output": args.output, "manifest": save_manifest(args.root, args.output, root_name=args.root_name)})
    if command == "build-package": return _execute(command, lambda: build_release_package(args.source, args.output, package_id=args.package_id, release_id=args.release_id, timestamp=args.timestamp, overwrite=args.overwrite))
    if command == "extract-package": return _execute(command, lambda: extract_release_package(args.package, args.destination, overwrite=args.overwrite, limits=_limits(args)))
    if command == "promote": return _execute(command, lambda: promote_release(args.workspace, args.candidate, args.release_id, expected_current=args.expected_current, transaction_id=args.transaction_id, timestamp=args.timestamp))
    if command == "rollback": return _execute(command, lambda: rollback_release(args.workspace, args.release_id, args.reason, expected_current=args.expected_current, transaction_id=args.transaction_id, timestamp=args.timestamp))
    if command == "recover": return _execute(command, lambda: recover_workspace(args.workspace, force_lock=args.force_lock))
    return _emit(command, [ValidationIssue("COMMAND_UNSUPPORTED", "$", f"unsupported command: {command}")], exit_code=EXIT_INTERNAL_ERROR)


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except CLIUsageError as exc:
        return _emit("usage", [ValidationIssue("CLI_USAGE_ERROR", "$", str(exc))], exit_code=EXIT_USAGE_ERROR)
    try:
        return _dispatch(args)
    except Exception as exc:
        return _emit(getattr(args, "cmd", "internal"), [ValidationIssue("INTERNAL_ERROR", "$", f"{type(exc).__name__}: {exc}")], exit_code=EXIT_INTERNAL_ERROR)


if __name__ == "__main__":
    raise SystemExit(main())
