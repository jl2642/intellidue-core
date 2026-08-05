from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path
from typing import Any

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
        for parent in product.get("parent_product_ids", []):
            if parent not in known:
                issues.append(f"{product_id}: missing parent {parent}")
        if product["lifecycle"] == "WITHDRAWN" and product["delivery_pack"] == "CLEAN_READER":
            issues.append(f"{product_id}: withdrawn product in Clean Reader")
        if product["lifecycle"] == "NOT_APPLICABLE" and product["delivery_pack"] != "EXCLUDED":
            issues.append(f"{product_id}: not-applicable product must be excluded")
        if (
            product["lifecycle"] in {"CURRENT", "ACCEPTED_PARENT"}
            and product["delivery_pack"] == "EXCLUDED"
            and not product.get("exclusion_reason")
        ):
            issues.append(f"{product_id}: accepted/current excluded without reason")
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
        if product["lifecycle"] not in {"WITHDRAWN", "ARCHIVED", "NOT_APPLICABLE"}
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
        elif not any(
            product["lifecycle"] in {"CURRENT", "ACCEPTED_PARENT", "SUPERSEDED"}
            for product in group_products
        ):
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
    return sorted(set(issues))


__all__ = [
    "validate_professional_document",
    "validate_catalog",
    "validate_master_delivery",
    "validate_source_review_coverage",
    "validate_system_recovery_receipt",
    "validate_professional_delivery_bundle",
]
