from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.resources import files
import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

SCHEMA_VERSION = "1.0.0"
SUPPORTED_SCHEMA_VERSIONS = {SCHEMA_VERSION}
SCHEMA_FILES = {
    "state": "current_project_state.schema.json",
    "lock": "release_lock.schema.json",
    "validation": "package_validation.schema.json",
    "manifest": "product_manifest.schema.json",
}


@dataclass(frozen=True, order=True)
class ValidationIssue:
    code: str
    path: str
    message: str
    severity: str = "error"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _json_path(parts: Iterable[Any]) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def load_json(path: str | Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [ValidationIssue("FILE_NOT_FOUND", "$", f"file not found: {path}")]
    except UnicodeDecodeError as exc:
        return None, [ValidationIssue("TEXT_DECODE_ERROR", "$", str(exc))]
    except json.JSONDecodeError as exc:
        return None, [ValidationIssue("JSON_INVALID", f"$@{exc.lineno}:{exc.colno}", exc.msg)]
    if not isinstance(value, dict):
        return None, [ValidationIssue("DOCUMENT_NOT_OBJECT", "$", "top-level JSON value must be an object")]
    return value, []


def schema_for(kind: str) -> dict[str, Any]:
    try:
        name = SCHEMA_FILES[kind]
    except KeyError as exc:
        raise ValueError(f"unsupported document kind: {kind}") from exc
    resource = files("intellidue_core.schemas").joinpath(name)
    return json.loads(resource.read_text(encoding="utf-8"))


def validate_object(kind: str, obj: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    version = obj.get("schema_version")
    if version is None:
        issues.append(ValidationIssue("SCHEMA_VERSION_MISSING", "$.schema_version", "schema_version is required"))
    elif version not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            ValidationIssue(
                "SCHEMA_VERSION_UNSUPPORTED",
                "$.schema_version",
                f"unsupported schema_version {version!r}; supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            )
        )
        return issues

    validator = Draft202012Validator(schema_for(kind))
    for error in sorted(validator.iter_errors(obj), key=lambda item: (list(item.absolute_path), item.message)):
        issues.append(
            ValidationIssue(
                "SCHEMA_VIOLATION",
                _json_path(error.absolute_path),
                error.message,
            )
        )

    if not issues and kind in {"state", "lock", "validation"}:
        boundary_key = {"state": "project_boundaries", "lock": "hard_controls", "validation": "non_regression"}[kind]
        boundaries = obj[boundary_key]
        if boundaries["decision_ready"] and boundaries["critical_gates_open"] != 0:
            issues.append(ValidationIssue("DECISION_READY_OPEN_GATES", f"$.{boundary_key}.critical_gates_open", "decision_ready=true requires zero open critical gates"))
        if boundaries["decision_ready"] and boundaries["restricted_outputs"]:
            issues.append(ValidationIssue("DECISION_READY_RESTRICTED_OUTPUTS", f"$.{boundary_key}.restricted_outputs", "decision_ready=true requires no restricted outputs"))

    if kind == "manifest" and not issues:
        paths = [item["path"] for item in obj["files"]]
        if len(paths) != len(set(paths)):
            issues.append(ValidationIssue("MANIFEST_DUPLICATE_PATH", "$.files", "manifest paths must be unique"))
        if paths != sorted(paths):
            issues.append(ValidationIssue("MANIFEST_PATH_ORDER", "$.files", "manifest paths must be sorted"))
    return sorted(set(issues))


def validate_document(kind: str, path: str | Path) -> list[ValidationIssue]:
    obj, issues = load_json(path)
    if issues or obj is None:
        return issues
    return validate_object(kind, obj)


def validate_contract_objects(
    state: dict[str, Any],
    lock: dict[str, Any],
    validation: dict[str, Any],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for kind, obj in (("state", state), ("lock", lock), ("validation", validation)):
        issues.extend(validate_object(kind, obj))
    structural_codes = {"SCHEMA_VERSION_MISSING", "SCHEMA_VERSION_UNSUPPORTED", "SCHEMA_VIOLATION"}
    if any(issue.code in structural_codes for issue in issues):
        return sorted(set(issues))

    if state["project_id"] != lock["project_id"] or state["project_id"] != validation["project_id"]:
        issues.append(ValidationIssue("CONTRACT_PROJECT_ID_MISMATCH", "$", "project_id must match across state, lock and validation"))
    if state["status"] != lock["status"]:
        issues.append(ValidationIssue("CONTRACT_STATUS_MISMATCH", "$", "status must match between state and lock"))
    if state["accepted_product_class"] != lock["accepted_product_class"]:
        issues.append(ValidationIssue("CONTRACT_PRODUCT_CLASS_MISMATCH", "$", "accepted_product_class must match between state and lock"))
    if state["next"] != lock["next"]:
        issues.append(ValidationIssue("CONTRACT_NEXT_MISMATCH", "$", "next must match between state and lock"))

    boundaries = state["project_boundaries"]
    hard_controls = lock["hard_controls"]
    non_regression = validation["non_regression"]
    for key, code in (
        ("critical_gates_open", "CONTRACT_GATE_COUNT_MISMATCH"),
        ("restricted_outputs", "CONTRACT_RESTRICTED_OUTPUTS_MISMATCH"),
        ("decision_ready", "CONTRACT_DECISION_READY_MISMATCH"),
    ):
        values = (boundaries[key], hard_controls[key], non_regression[key])
        if key == "restricted_outputs":
            values = tuple(sorted(value) for value in values)
        if not (values[0] == values[1] == values[2]):
            issues.append(ValidationIssue(code, "$", f"{key} must match across state, lock and validation"))

    if state["accepted_product_class"] == "FINAL_FULL_DD":
        if boundaries["critical_gates_open"] != 0:
            issues.append(ValidationIssue("FINAL_DD_OPEN_GATES", "$.project_boundaries.critical_gates_open", "FINAL_FULL_DD requires zero open critical gates"))
        if boundaries["restricted_outputs"]:
            issues.append(ValidationIssue("FINAL_DD_RESTRICTED_OUTPUTS", "$.project_boundaries.restricted_outputs", "FINAL_FULL_DD requires no restricted outputs"))
        if not boundaries["decision_ready"]:
            issues.append(ValidationIssue("FINAL_DD_NOT_DECISION_READY", "$.project_boundaries.decision_ready", "FINAL_FULL_DD requires decision_ready=true"))

    return sorted(set(issues))


def validate_contract_files(
    state_path: str | Path,
    lock_path: str | Path,
    validation_path: str | Path,
) -> list[ValidationIssue]:
    documents: list[dict[str, Any]] = []
    issues: list[ValidationIssue] = []
    for path in (state_path, lock_path, validation_path):
        obj, current = load_json(path)
        issues.extend(current)
        if obj is not None:
            documents.append(obj)
    if issues:
        return sorted(set(issues))
    return validate_contract_objects(*documents)
