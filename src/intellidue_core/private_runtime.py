from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import Any

from .contracts import SCHEMA_VERSION, ValidationIssue, load_json, validate_contract_objects, validate_object
from .manifest import canonical_json_bytes, file_hash
from .package_format import build_release_package
from .promotion import PromotionError, promote_release, recover_workspace, rollback_release, validate_workspace
from .workspace import WorkspaceLock, atomic_write_json, read_json

ADAPTER_CONTRACT_VERSION = "1.0.0"
ADAPTER_FILENAME = "adapter.json"
BINDING_FILENAME = "private_runtime.json"
CORE_WORKSPACE = "core"
RECEIPT_PATH = "runtime/private_runtime_receipt.json"
CONTROL_OUTPUTS = {
    "state": "control/current_project_state.json",
    "lock": "control/release_lock.json",
    "validation": "control/package_validation.json",
}
PRODUCT_CLASSES = {"READER": "reader", "CONTROL": "control", "SUPPLEMENTAL": "supplemental"}


class PrivateRuntimeError(Exception):
    def __init__(self, code: str, message: str, path: str = "$"):
        super().__init__(message)
        self.issue = ValidationIssue(code, path, message)


@dataclass(frozen=True)
class ProductRoot:
    product_class: str
    source: Path
    output: str
    required: bool
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class PrivateProject:
    root: Path
    config_path: Path
    config: dict[str, Any]
    control_paths: dict[str, Path]
    control_docs: dict[str, dict[str, Any]]
    product_roots: tuple[ProductRoot, ...]

    @property
    def project_id(self) -> str:
        return self.config["project_id"]

    @property
    def release_id(self) -> str:
        return self.config["release_id"]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _prefix(issue: ValidationIssue, prefix: str) -> ValidationIssue:
    suffix = issue.path[1:] if issue.path.startswith("$") else issue.path
    return ValidationIssue(issue.code, f"{prefix}{suffix}", issue.message, issue.severity)


def _relative_path(value: str) -> PurePosixPath | None:
    if not value or "\\" in value or value.startswith("/"):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path


def _inside(root: Path, path: Path) -> bool:
    return path == root or root in path.parents


def _resolve_private_path(root: Path, value: str, label: str, issues: list[ValidationIssue]) -> Path | None:
    relative = _relative_path(value)
    if relative is None:
        issues.append(ValidationIssue("PRIVATE_PATH_INVALID", label, f"path must be safe and relative: {value!r}"))
        return None
    root_resolved = root.resolve()
    candidate = root.joinpath(*relative.parts)
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        issues.append(ValidationIssue("PRIVATE_PATH_RESOLVE_FAILED", label, str(exc)))
        return None
    if not _inside(root_resolved, resolved):
        issues.append(ValidationIssue("PRIVATE_PATH_ESCAPE", label, f"path escapes project root: {value}"))
        return None
    cursor = root_resolved
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            issues.append(ValidationIssue("PRIVATE_PATH_SYMLINK", label, f"symbolic links are not allowed: {value}"))
            return None
    return candidate


def _tree_stats(root: Path, prefix: str, issues: list[ValidationIssue]) -> tuple[int, int, set[str]]:
    count = 0
    total = 0
    folded: set[str] = set()
    if not root.exists():
        return 0, 0, folded
    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            issues.append(ValidationIssue("PRIVATE_PRODUCT_SYMLINK", f"{prefix}[{relative!r}]", "symbolic links are not allowed"))
            continue
        if item.is_dir():
            continue
        if not item.is_file():
            issues.append(ValidationIssue("PRIVATE_PRODUCT_SPECIAL_FILE", f"{prefix}[{relative!r}]", "special files are not allowed"))
            continue
        key = relative.casefold()
        if key in folded:
            issues.append(ValidationIssue("PRIVATE_PRODUCT_CASE_COLLISION", prefix, f"case-insensitive duplicate path: {relative}"))
        folded.add(key)
        count += 1
        total += item.stat().st_size
    return count, total, folded


def _load_private_project(project_root: str | Path, config: str = ADAPTER_FILENAME) -> tuple[PrivateProject | None, list[ValidationIssue]]:
    root = Path(project_root)
    issues: list[ValidationIssue] = []
    if not root.exists():
        return None, [ValidationIssue("PRIVATE_PROJECT_ROOT_MISSING", "$.project_root", f"project root not found: {root}")]
    if not root.is_dir():
        return None, [ValidationIssue("PRIVATE_PROJECT_ROOT_NOT_DIRECTORY", "$.project_root", f"project root is not a directory: {root}")]
    if root.is_symlink():
        return None, [ValidationIssue("PRIVATE_PROJECT_ROOT_SYMLINK", "$.project_root", "project root must not be a symbolic link")]

    config_path = _resolve_private_path(root, config, "$.config", issues)
    if config_path is None:
        return None, sorted(set(issues))
    config_obj, current = load_json(config_path)
    issues.extend(_prefix(issue, "$.config") for issue in current)
    if config_obj is None:
        return None, sorted(set(issues))
    issues.extend(_prefix(issue, "$.config") for issue in validate_object("private_adapter", config_obj))
    structural = {"SCHEMA_VERSION_MISSING", "SCHEMA_VERSION_UNSUPPORTED", "SCHEMA_VIOLATION"}
    if any(issue.code in structural for issue in issues):
        return None, sorted(set(issues))

    control_paths: dict[str, Path] = {}
    control_docs: dict[str, dict[str, Any]] = {}
    for key in ("state", "lock", "validation"):
        path = _resolve_private_path(root, config_obj["control"][key], f"$.config.control.{key}", issues)
        if path is None:
            continue
        if not path.is_file():
            issues.append(ValidationIssue("PRIVATE_CONTROL_FILE_MISSING", f"$.config.control.{key}", f"control file not found: {config_obj['control'][key]}"))
            continue
        document, current = load_json(path)
        issues.extend(_prefix(issue, f"$.control.{key}") for issue in current)
        if document is not None:
            control_paths[key] = path
            control_docs[key] = document

    if len(control_docs) == 3:
        contract_issues = validate_contract_objects(control_docs["state"], control_docs["lock"], control_docs["validation"])
        issues.extend(_prefix(issue, "$.control.contract") for issue in contract_issues)
        for key, document in control_docs.items():
            if document.get("project_id") != config_obj["project_id"]:
                issues.append(ValidationIssue("PRIVATE_PROJECT_ID_MISMATCH", f"$.control.{key}.project_id", "control project_id must match adapter project_id"))
        if control_docs["state"].get("status") != "CURRENT":
            issues.append(ValidationIssue("PRIVATE_STATE_NOT_CURRENT", "$.control.state.status", "private release requires CURRENT project state"))
        if control_docs["validation"].get("status") != "PASS":
            issues.append(ValidationIssue("PRIVATE_VALIDATION_NOT_PASS", "$.control.validation.status", "private release requires package validation PASS"))

    product_roots: list[ProductRoot] = []
    seen_classes: set[str] = set()
    source_paths: list[tuple[str, Path]] = []
    output_keys: set[str] = set()
    for index, item in enumerate(config_obj["product_roots"]):
        prefix = f"$.config.product_roots[{index}]"
        product_class = item["class"]
        if product_class in seen_classes:
            issues.append(ValidationIssue("PRIVATE_PRODUCT_CLASS_DUPLICATE", f"{prefix}.class", f"duplicate product class: {product_class}"))
            continue
        seen_classes.add(product_class)
        path = _resolve_private_path(root, item["path"], f"{prefix}.path", issues)
        if path is None:
            continue
        source_paths.append((prefix, path.resolve(strict=False)))
        if not path.exists():
            if item["required"]:
                issues.append(ValidationIssue("PRIVATE_PRODUCT_ROOT_MISSING", f"{prefix}.path", f"required product root not found: {item['path']}"))
            continue
        if not path.is_dir():
            issues.append(ValidationIssue("PRIVATE_PRODUCT_ROOT_NOT_DIRECTORY", f"{prefix}.path", f"product root is not a directory: {item['path']}"))
            continue
        count, total, relative_keys = _tree_stats(path, f"$.products.{product_class.lower()}", issues)
        if item["required"] and count == 0:
            issues.append(ValidationIssue("PRIVATE_PRODUCT_ROOT_EMPTY", f"{prefix}.path", f"required product root is empty: {item['path']}"))
        output = f"products/{PRODUCT_CLASSES[product_class]}"
        for relative_key in relative_keys:
            output_key = f"{output}/{relative_key}".casefold()
            if output_key in output_keys:
                issues.append(ValidationIssue("PRIVATE_OUTPUT_CASE_COLLISION", prefix, f"duplicate candidate output path: {output}/{relative_key}"))
            output_keys.add(output_key)
        product_roots.append(ProductRoot(product_class, path, output, item["required"], count, total))

    for required_class in ("READER", "CONTROL"):
        if required_class not in seen_classes:
            issues.append(ValidationIssue("PRIVATE_REQUIRED_PRODUCT_CLASS_MISSING", "$.config.product_roots", f"required product class is missing: {required_class}"))
    for left_index, (left_prefix, left) in enumerate(source_paths):
        for right_prefix, right in source_paths[left_index + 1:]:
            if _inside(left, right) or _inside(right, left):
                issues.append(ValidationIssue("PRIVATE_PRODUCT_ROOT_OVERLAP", left_prefix, f"product roots must not overlap: {left} and {right}"))
                issues.append(ValidationIssue("PRIVATE_PRODUCT_ROOT_OVERLAP", right_prefix, f"product roots must not overlap: {left} and {right}"))

    if issues:
        return None, sorted(set(issues))
    return PrivateProject(root, config_path, config_obj, control_paths, control_docs, tuple(sorted(product_roots, key=lambda item: item.product_class))), []


def _receipt(project: PrivateProject, timestamp: str) -> dict[str, Any]:
    state = project.control_docs["state"]
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "receipt_class": "PRIVATE_PROJECT_RELEASE",
        "project_id": project.project_id,
        "project_name": state["project_name"],
        "release_id": project.release_id,
        "accepted_product_class": state["accepted_product_class"],
        "project_boundaries": state["project_boundaries"],
        "control_sha256": {key: file_hash(path) for key, path in sorted(project.control_paths.items())},
        "product_summary": [
            {
                "class": item.product_class,
                "path": item.output,
                "file_count": item.file_count,
                "total_bytes": item.total_bytes,
            }
            for item in project.product_roots
        ],
        "created_at": timestamp,
        "privacy": {
            "private_runtime_only": True,
            "public_export_allowed": False,
            "network_write_performed": False,
        },
    }
    issues = validate_object("private_receipt", receipt)
    if issues:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    return receipt


def _copy_tree(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.rglob("*")):
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.is_file() and not item.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)


def _build_candidate(project: PrivateProject, destination: Path, timestamp: str) -> dict[str, Any]:
    if destination.exists():
        raise FileExistsError(f"candidate destination already exists: {destination}")
    destination.mkdir(parents=True)
    for key, output in CONTROL_OUTPUTS.items():
        target = destination / output
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project.control_paths[key], target)
    for product in project.product_roots:
        _copy_tree(product.source, destination / product.output)
    receipt = _receipt(project, timestamp)
    receipt_path = destination / RECEIPT_PATH
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(canonical_json_bytes(receipt))
    return receipt


def inspect_private_project(project_root: str | Path, config: str = ADAPTER_FILENAME) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    project, issues = _load_private_project(project_root, config)
    if issues or project is None:
        return None, issues
    state = project.control_docs["state"]
    return {
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "project_id": project.project_id,
        "project_name": state["project_name"],
        "release_id": project.release_id,
        "accepted_product_class": state["accepted_product_class"],
        "project_boundaries": state["project_boundaries"],
        "product_summary": [
            {
                "class": item.product_class,
                "path": item.output,
                "required": item.required,
                "file_count": item.file_count,
                "total_bytes": item.total_bytes,
            }
            for item in project.product_roots
        ],
        "privacy": project.config["privacy"],
    }, []


def validate_private_project(project_root: str | Path, config: str = ADAPTER_FILENAME) -> list[ValidationIssue]:
    return _load_private_project(project_root, config)[1]


def build_private_release_package(
    project_root: str | Path,
    output: str | Path,
    *,
    config: str = ADAPTER_FILENAME,
    timestamp: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    project, issues = _load_private_project(project_root, config)
    if issues or project is None:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    timestamp = timestamp or _now()
    with tempfile.TemporaryDirectory() as tmp:
        candidate = Path(tmp) / project.release_id
        receipt = _build_candidate(project, candidate, timestamp)
        result = build_release_package(candidate, output, package_id=project.release_id, release_id=project.release_id, timestamp=timestamp, overwrite=overwrite)
    return {**result, "project_id": project.project_id, "adapter_contract_version": ADAPTER_CONTRACT_VERSION, "receipt": receipt}


def _binding(project_id: str, timestamp: str) -> dict[str, Any]:
    value = {
        "schema_version": SCHEMA_VERSION,
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "runtime_class": "PRIVATE_PROJECT_RUNTIME",
        "project_id": project_id,
        "created_at": timestamp,
        "core_workspace": CORE_WORKSPACE,
        "privacy": {"private_runtime_only": True, "public_export_allowed": False},
    }
    issues = validate_object("private_binding", value)
    if issues:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    return value


def _read_binding(runtime_root: Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    binding_path = runtime_root / BINDING_FILENAME
    value, issues = load_json(binding_path)
    if value is None:
        return None, [_prefix(issue, "$.binding") for issue in issues]
    current = [_prefix(issue, "$.binding") for issue in validate_object("private_binding", value)]
    return value, sorted(set(current))


def promote_private_release(
    project_root: str | Path,
    runtime: str | Path,
    *,
    config: str = ADAPTER_FILENAME,
    expected_current: str | None = None,
    transaction_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    project, issues = _load_private_project(project_root, config)
    if issues or project is None:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    timestamp = timestamp or _now()
    runtime_root = Path(runtime)
    if runtime_root.exists() and (not runtime_root.is_dir() or runtime_root.is_symlink()):
        raise PrivateRuntimeError("PRIVATE_RUNTIME_ROOT_INVALID", "runtime root must be a non-symlink directory", "$.runtime")

    binding_path = runtime_root / BINDING_FILENAME
    created_binding = False
    with WorkspaceLock(runtime_root):
        if binding_path.exists():
            binding, binding_issues = _read_binding(runtime_root)
            if binding_issues or binding is None:
                issue = binding_issues[0]
                raise PrivateRuntimeError(issue.code, issue.message, issue.path)
            if binding["project_id"] != project.project_id:
                raise PrivateRuntimeError("PRIVATE_RUNTIME_PROJECT_CONFLICT", f"runtime is bound to {binding['project_id']}, not {project.project_id}", "$.binding.project_id")
        else:
            atomic_write_json(binding_path, _binding(project.project_id, timestamp))
            created_binding = True
        try:
            with tempfile.TemporaryDirectory() as tmp:
                candidate = Path(tmp) / project.release_id
                receipt = _build_candidate(project, candidate, timestamp)
                result = promote_release(
                    runtime_root / CORE_WORKSPACE,
                    candidate,
                    project.release_id,
                    expected_current=expected_current,
                    transaction_id=transaction_id,
                    timestamp=timestamp,
                )
        except Exception:
            if created_binding and not (runtime_root / CORE_WORKSPACE / "pointers/current.json").exists():
                binding_path.unlink(missing_ok=True)
            raise
    runtime_issues = validate_private_runtime(runtime_root)
    if runtime_issues:
        issue = runtime_issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    return {**result, "project_id": project.project_id, "adapter_contract_version": ADAPTER_CONTRACT_VERSION, "runtime": str(runtime_root), "receipt": receipt}


def rollback_private_release(
    runtime: str | Path,
    release_id: str,
    reason: str,
    *,
    expected_current: str | None = None,
    transaction_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    runtime_root = Path(runtime)
    binding, issues = _read_binding(runtime_root)
    if issues or binding is None:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    runtime_issues = validate_private_runtime(runtime_root)
    if runtime_issues:
        issue = runtime_issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    target = runtime_root / CORE_WORKSPACE / "releases" / release_id
    target_issues = _validate_release(runtime_root, target, binding, f"$.rollback_target[{release_id!r}]") if target.is_dir() else [ValidationIssue("ROLLBACK_TARGET_MISSING", "$.rollback_target", f"rollback target is missing: {release_id}")]
    if target_issues:
        issue = target_issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    result = rollback_release(runtime_root / CORE_WORKSPACE, release_id, reason, expected_current=expected_current, transaction_id=transaction_id, timestamp=timestamp)
    runtime_issues = validate_private_runtime(runtime_root)
    if runtime_issues:
        issue = runtime_issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    return {**result, "project_id": binding["project_id"], "adapter_contract_version": ADAPTER_CONTRACT_VERSION, "runtime": str(runtime_root)}


def recover_private_runtime(runtime: str | Path, *, force_lock: bool = False) -> dict[str, Any]:
    runtime_root = Path(runtime)
    binding, issues = _read_binding(runtime_root)
    if issues or binding is None:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    result = recover_workspace(runtime_root / CORE_WORKSPACE, force_lock=force_lock)
    runtime_issues = validate_private_runtime(runtime_root)
    if runtime_issues:
        issue = runtime_issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    return {**result, "project_id": binding["project_id"], "adapter_contract_version": ADAPTER_CONTRACT_VERSION, "runtime": str(runtime_root)}


def _validate_release(runtime_root: Path, release_path: Path, binding: dict[str, Any], prefix: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    receipt_path = release_path / RECEIPT_PATH
    receipt, current = load_json(receipt_path)
    issues.extend(_prefix(issue, f"{prefix}.receipt") for issue in current)
    if receipt is None:
        return issues
    issues.extend(_prefix(issue, f"{prefix}.receipt") for issue in validate_object("private_receipt", receipt))
    if receipt.get("project_id") != binding.get("project_id"):
        issues.append(ValidationIssue("PRIVATE_RUNTIME_PROJECT_CONFLICT", f"{prefix}.receipt.project_id", "release receipt project_id differs from runtime binding"))
    if receipt.get("release_id") != release_path.name:
        issues.append(ValidationIssue("PRIVATE_RUNTIME_RELEASE_ID_MISMATCH", f"{prefix}.receipt.release_id", "release receipt release_id differs from release directory"))

    documents: dict[str, dict[str, Any]] = {}
    for key, output in CONTROL_OUTPUTS.items():
        path = release_path / output
        document, current = load_json(path)
        issues.extend(_prefix(issue, f"{prefix}.control.{key}") for issue in current)
        if document is not None:
            documents[key] = document
            expected_hash = receipt.get("control_sha256", {}).get(key)
            if expected_hash and file_hash(path) != expected_hash:
                issues.append(ValidationIssue("PRIVATE_CONTROL_HASH_MISMATCH", f"{prefix}.receipt.control_sha256.{key}", "control file hash differs from receipt"))
    if len(documents) == 3:
        issues.extend(_prefix(issue, f"{prefix}.control.contract") for issue in validate_contract_objects(documents["state"], documents["lock"], documents["validation"]))
        if any(document.get("project_id") != binding.get("project_id") for document in documents.values()):
            issues.append(ValidationIssue("PRIVATE_RUNTIME_PROJECT_CONFLICT", f"{prefix}.control", "release control project_id differs from runtime binding"))
    for required in ("reader", "control"):
        path = release_path / "products" / required
        if not path.is_dir() or not any(item.is_file() for item in path.rglob("*")):
            issues.append(ValidationIssue("PRIVATE_RUNTIME_PRODUCT_MISSING", f"{prefix}.products.{required}", f"required runtime product root is missing or empty: {required}"))
    return sorted(set(issues))


def validate_private_runtime(runtime: str | Path) -> list[ValidationIssue]:
    runtime_root = Path(runtime)
    if not runtime_root.exists():
        return [ValidationIssue("PRIVATE_RUNTIME_ROOT_MISSING", "$.runtime", f"runtime root not found: {runtime_root}")]
    if not runtime_root.is_dir() or runtime_root.is_symlink():
        return [ValidationIssue("PRIVATE_RUNTIME_ROOT_INVALID", "$.runtime", "runtime root must be a non-symlink directory")]
    binding, issues = _read_binding(runtime_root)
    if binding is None:
        return sorted(set(issues))
    core = runtime_root / CORE_WORKSPACE
    issues.extend(_prefix(issue, "$.core") for issue in validate_workspace(core))
    releases = core / "releases"
    if releases.is_dir():
        for release_path in sorted(item for item in releases.iterdir() if item.is_dir() and not item.name.startswith(".staging-")):
            issues.extend(_validate_release(runtime_root, release_path, binding, f"$.releases[{release_path.name!r}]"))
    current = None
    if (core / "pointers/current.json").exists():
        try:
            current = read_json(core / "pointers/current.json")
        except PromotionError as exc:
            issues.append(_prefix(exc.issue, "$.current"))
    if current is not None:
        current_receipt = core / current["release_path"] / RECEIPT_PATH
        receipt, current_issues = load_json(current_receipt)
        issues.extend(_prefix(issue, "$.current.receipt") for issue in current_issues)
        if receipt is not None and receipt.get("release_id") != current.get("release_id"):
            issues.append(ValidationIssue("PRIVATE_RUNTIME_CURRENT_MISMATCH", "$.current", "current pointer and receipt release_id differ"))
    return sorted(set(issues))


def inspect_private_runtime(runtime: str | Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    runtime_root = Path(runtime)
    issues = validate_private_runtime(runtime_root)
    if issues:
        return None, issues
    binding, _ = _read_binding(runtime_root)
    assert binding is not None
    current = read_json(runtime_root / CORE_WORKSPACE / "pointers/current.json")
    archive = read_json(runtime_root / CORE_WORKSPACE / "pointers/archive.json") or {"entries": []}
    receipt = json.loads((runtime_root / CORE_WORKSPACE / current["release_path"] / RECEIPT_PATH).read_text(encoding="utf-8")) if current else None
    return {
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "project_id": binding["project_id"],
        "current_release": current["release_id"] if current else None,
        "archived_releases": [item["release_id"] for item in archive["entries"]],
        "accepted_product_class": receipt["accepted_product_class"] if receipt else None,
        "project_boundaries": receipt["project_boundaries"] if receipt else None,
        "product_summary": receipt["product_summary"] if receipt else [],
        "privacy": binding["privacy"],
    }, []
