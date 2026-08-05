from __future__ import annotations

from importlib.resources import files
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

from jsonschema import Draft202012Validator

ROLE_REQUIRED = {
    "INTEGRATED_DD",
    "INVESTMENT_MEMO",
    "ACTION_BOOK",
    "READER_GUIDE",
    "ACCEPTANCE",
}
PARENT_ROLE_GROUPS = {
    "BASE_DD": {"BASE_DD"},
    "SPECIALIST": {
        "SPECIALIST_FULL_REPORT",
        "SPECIALIST_ISSUE_MEMO",
        "SPECIALIST_ADVISER_PACK",
        "FORMAL_NOT_READY",
    },
    "SUPPLEMENTAL": {"SUPPLEMENTAL_RESEARCH", "CURRENT_UPDATE"},
}
ACTIVE_ROLE_PACK = {
    "READER_GUIDE": "CLEAN_READER",
    "BASE_DD": "CLEAN_READER",
    "SPECIALIST_FULL_REPORT": "CLEAN_READER",
    "SPECIALIST_ISSUE_MEMO": "CLEAN_READER",
    "SPECIALIST_ADVISER_PACK": "CLEAN_READER",
    "FORMAL_NOT_READY": "CLEAN_READER",
    "SUPPLEMENTAL_RESEARCH": "CLEAN_READER",
    "CURRENT_UPDATE": "CLEAN_READER",
    "INTEGRATED_DD": "CLEAN_READER",
    "TRANSACTION_STRATEGY": "CLEAN_READER",
    "INVESTMENT_MEMO": "CLEAN_READER",
    "ACTION_BOOK": "CLEAN_READER",
    "SOURCE_CONTROL": "WORKPAPER",
    "FACT_PACK": "WORKPAPER",
    "CALCULATION_MODEL": "WORKPAPER",
    "PROFESSIONAL_WORKPAPER": "WORKPAPER",
    "ACCEPTANCE": "INTERNAL_AUDIT",
    "AUDIT_ARCHIVE": "INTERNAL_AUDIT",
}
PACK_READER_STATUS = {
    "CLEAN_READER": {"READER", "SUPPORT"},
    "WORKPAPER": {"CONTROL"},
    "INTERNAL_AUDIT": {"AUDIT"},
}
SCHEMA_FILES = {
    "local_intake": "local_intake_receipt.schema.json",
    "product_catalog": "product_catalog.schema.json",
    "rp_master_delivery": "rp_master_delivery.schema.json",
    "source_review_coverage": "source_review_coverage.schema.json",
    "system_recovery_receipt": "system_recovery_receipt.schema.json",
}


def _load(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _schema(kind: str) -> dict[str, Any]:
    try:
        filename = SCHEMA_FILES[kind]
    except KeyError as exc:
        raise ValueError(f"unsupported professional-delivery schema kind: {kind}") from exc
    resource = files("intellidue_core.schemas").joinpath(filename)
    return json.loads(resource.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(root: Path, value: str, label: str) -> tuple[Path | None, list[str]]:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None, [f"{label}: unsafe relative path: {value}"]
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return None, [f"{label}: path escapes delivery root: {value}"]
    return resolved, []


def validate_professional_document(kind: str, obj_or_path: dict[str, Any] | str | Path) -> list[str]:
    obj = obj_or_path if isinstance(obj_or_path, dict) else _load(obj_or_path)
    errors = Draft202012Validator(_schema(kind)).iter_errors(obj)
    return sorted(f"{list(error.absolute_path)}: {error.message}" for error in errors)


def validate_catalog(catalog: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    products = catalog["products"]
    ids = [product["product_id"] for product in products]
    paths = [product["path"] for product in products]
    if len(ids) != len(set(ids)):
        issues.append("duplicate product_id")
    if len(paths) != len(set(paths)):
        issues.append("duplicate product path")

    known = set(ids)
    for product in products:
        product_id = product["product_id"]
        lifecycle = product["lifecycle"]
        pack = product["delivery_pack"]
        role = product["role"]
        reader_status = product["reader_status"]
        for parent in product.get("parent_product_ids", []):
            if parent not in known:
                issues.append(f"{product_id}: missing parent {parent}")
        if lifecycle == "WITHDRAWN" and pack == "CLEAN_READER":
            issues.append(f"{product_id}: withdrawn product in Clean Reader")
        if lifecycle == "SUPERSEDED" and pack == "CLEAN_READER":
            issues.append(f"{product_id}: superseded product in Clean Reader")
        if lifecycle == "NOT_APPLICABLE" and pack != "EXCLUDED":
            issues.append(f"{product_id}: not-applicable product must be excluded")
        if lifecycle in {"CURRENT", "ACCEPTED_PARENT"} and pack == "EXCLUDED" and not product.get("exclusion_reason"):
            issues.append(f"{product_id}: accepted/current excluded without reason")
        if lifecycle in {"CURRENT", "ACCEPTED_PARENT"}:
            required_pack = ACTIVE_ROLE_PACK.get(role)
            if required_pack and pack != required_pack:
                issues.append(f"{product_id}: active role {role} must be in {required_pack}")
            allowed_status = PACK_READER_STATUS.get(pack)
            if allowed_status and reader_status not in allowed_status:
                issues.append(f"{product_id}: reader_status {reader_status} incompatible with {pack}")
    return issues


def validate_master_delivery(master: dict[str, Any], catalog: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    products = {product["product_id"]: product for product in catalog["products"]}
    all_pack_ids: set[str] = set()

    for pack_name, pack in master["packs"].items():
        for product_id in pack["product_ids"]:
            if product_id not in products:
                issues.append(f"{pack_name}: unknown product {product_id}")
            if product_id in all_pack_ids:
                issues.append(f"product appears in multiple packs: {product_id}")
            all_pack_ids.add(product_id)

    roles_present = {
        product["role"]
        for product in products.values()
        if product["lifecycle"] not in {"WITHDRAWN", "ARCHIVED", "NOT_APPLICABLE", "SUPERSEDED"}
    }
    for role in ROLE_REQUIRED:
        if role not in roles_present:
            issues.append(f"missing required role: {role}")

    for group, roles in PARENT_ROLE_GROUPS.items():
        group_products = [product for product in products.values() if product["role"] in roles]
        if not group_products:
            issues.append(f"missing required parent group: {group}")
        elif all(product["lifecycle"] == "NOT_APPLICABLE" for product in group_products):
            continue
        elif not any(product["lifecycle"] in {"CURRENT", "ACCEPTED_PARENT", "SUPERSEDED"} for product in group_products):
            issues.append(f"no accepted product in parent group: {group}")

    for product_id, product in products.items():
        expected_pack = product["delivery_pack"]
        if expected_pack == "EXCLUDED":
            if product_id in all_pack_ids:
                issues.append(f"excluded product included in a pack: {product_id}")
            continue

        if product_id not in all_pack_ids:
            issues.append(f"product missing from declared pack: {product_id}")
        expected_key = {
            "CLEAN_READER": "clean_reader",
            "WORKPAPER": "workpaper",
            "INTERNAL_AUDIT": "internal_audit",
        }[expected_pack]
        if product_id not in master["packs"][expected_key]["product_ids"]:
            issues.append(f"{expected_pack} placement mismatch: {product_id}")

    if master["status"] == "PASS" and issues:
        issues.append("status PASS is incompatible with validation issues")
    return issues


def validate_source_review_coverage(coverage: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    dispositions = coverage["dispositions"]
    disposition_total = sum(dispositions.values())
    if disposition_total != coverage["unique_source_count"]:
        issues.append("disposition total does not equal unique_source_count")

    p0_p1 = coverage["p0_p1"]
    if p0_p1["completed"] > p0_p1["total"]:
        issues.append("P0/P1 completed exceeds total")

    complete = (
        disposition_total == coverage["unique_source_count"]
        and p0_p1["completed"] == p0_p1["total"]
        and p0_p1["open_material_exceptions"] == 0
        and dispositions["deferred"] == 0
    )
    if coverage["coverage_complete"] != complete:
        issues.append("coverage_complete is inconsistent with counts")
    if coverage["professional_review_claim"] == "FULL" and (
        dispositions["unreadable"] > 0
        or dispositions["deferred"] > 0
        or p0_p1["open_material_exceptions"] > 0
    ):
        issues.append("FULL professional review claim is not supported")
    return issues


def validate_system_recovery_receipt(receipt: dict[str, Any]) -> list[str]:
    should_pass = (
        receipt["expected_sha256"] == receipt["actual_sha256"]
        and receipt["authority_status"] in {"CURRENT", "RECOVERY_PARENT"}
        and bool(receipt["required_contracts_verified"])
    )
    if (receipt["gate"] == "RECOVERY_PASS") != should_pass:
        return ["recovery gate inconsistent with authority/hash verification"]
    return []


def _validate_product_files(root: Path, catalog: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for product in catalog["products"]:
        if product["delivery_pack"] == "EXCLUDED" or product["lifecycle"] == "NOT_APPLICABLE":
            continue
        product_id = product["product_id"]
        product_path, path_issues = _relative_path(root, product["path"], product_id)
        issues.extend(path_issues)
        if product_path is None:
            continue
        if not product_path.is_file():
            issues.append(f"{product_id}: entity file missing: {product['path']}")
            continue
        if product_path.stat().st_size != product["size_bytes"]:
            issues.append(f"{product_id}: entity file size mismatch")
        if _sha256(product_path) != product["sha256"]:
            issues.append(f"{product_id}: entity file sha256 mismatch")
    return issues


def _validate_pack_files(root: Path, master: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for pack_name, pack in master["packs"].items():
        package_path, path_issues = _relative_path(root, pack["package_path"], f"{pack_name} package")
        issues.extend(path_issues)
        if package_path is None:
            continue
        if not package_path.is_file():
            issues.append(f"{pack_name}: package file missing: {pack['package_path']}")
            continue
        if _sha256(package_path) != pack["sha256"]:
            issues.append(f"{pack_name}: package sha256 mismatch")
        if not zipfile.is_zipfile(package_path):
            issues.append(f"{pack_name}: package is not a ZIP archive")
            continue
        try:
            with zipfile.ZipFile(package_path) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    issues.append(f"{pack_name}: ZIP CRC failure: {bad_member}")
                members = [item for item in archive.infolist() if not item.is_dir()]
                if len(members) != pack["file_count"]:
                    issues.append(f"{pack_name}: package file_count mismatch")
                names = [item.filename for item in members]
                if len(names) != len(set(names)):
                    issues.append(f"{pack_name}: duplicate ZIP member path")
                for name in names:
                    member = Path(name)
                    if member.is_absolute() or ".." in member.parts or "\\" in name:
                        issues.append(f"{pack_name}: unsafe ZIP member path: {name}")
        except (OSError, zipfile.BadZipFile) as exc:
            issues.append(f"{pack_name}: ZIP inspection failed: {exc}")
    return issues


def _validate_authority_files(root: Path, master: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for authority_name, value in master["authority_files"].items():
        path, path_issues = _relative_path(root, value, f"authority {authority_name}")
        issues.extend(path_issues)
        if path is not None and not path.is_file():
            issues.append(f"authority {authority_name}: file missing: {value}")
    return issues


def validate_professional_delivery_bundle(root: str | Path) -> list[str]:
    root = Path(root)
    catalog = _load(root / "product_catalog.json")
    master = _load(root / "rp_master_delivery.json")
    coverage = _load(root / "source_review_coverage.json")
    recovery = _load(root / "system_recovery_receipt.json")

    issues: list[str] = []
    for name, obj, kind in (
        ("catalog", catalog, "product_catalog"),
        ("master", master, "rp_master_delivery"),
        ("coverage", coverage, "source_review_coverage"),
        ("recovery", recovery, "system_recovery_receipt"),
    ):
        issues.extend(f"{name}: {issue}" for issue in validate_professional_document(kind, obj))

    issues.extend(validate_catalog(catalog))
    issues.extend(validate_master_delivery(master, catalog))
    issues.extend(validate_source_review_coverage(coverage))
    issues.extend(validate_system_recovery_receipt(recovery))
    issues.extend(_validate_product_files(root, catalog))
    issues.extend(_validate_pack_files(root, master))
    issues.extend(_validate_authority_files(root, master))
    return sorted(set(issues))


__all__ = [
    "validate_professional_document",
    "validate_catalog",
    "validate_master_delivery",
    "validate_source_review_coverage",
    "validate_system_recovery_receipt",
    "validate_professional_delivery_bundle",
]
