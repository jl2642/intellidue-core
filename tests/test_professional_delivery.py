from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from intellidue_core.professional_delivery import (
    validate_professional_delivery_bundle,
    validate_professional_document,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _product(product_id, role, lifecycle, pack, parents=()):
    payload = product_id.encode("utf-8")
    status = {
        "CLEAN_READER": "READER" if role not in {"SPECIALIST_ISSUE_MEMO", "CURRENT_UPDATE"} else "SUPPORT",
        "WORKPAPER": "CONTROL",
        "INTERNAL_AUDIT": "AUDIT",
    }[pack]
    return {
        "product_id": product_id,
        "title": product_id.replace("_", " ").title(),
        "role": role,
        "lifecycle": lifecycle,
        "reader_status": status,
        "delivery_pack": pack,
        "authority_level": "PRIMARY" if role == "INTEGRATED_DD" else "PARENT",
        "path": f"{pack.lower()}/{product_id.lower()}.txt",
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "parent_product_ids": list(parents),
    }


def _write_bundle(root: Path, *, complete: bool) -> None:
    root.mkdir()
    products = [
        _product("GUIDE", "READER_GUIDE", "CURRENT", "CLEAN_READER"),
        _product("BASE", "BASE_DD", "ACCEPTED_PARENT", "CLEAN_READER"),
        _product("SPECIALIST", "SPECIALIST_ISSUE_MEMO", "ACCEPTED_PARENT", "CLEAN_READER", ("BASE",)),
        _product("SUPPLEMENTAL", "CURRENT_UPDATE", "ACCEPTED_PARENT", "CLEAN_READER", ("BASE",)),
        _product("INTEGRATED", "INTEGRATED_DD", "CURRENT", "CLEAN_READER", ("BASE", "SPECIALIST", "SUPPLEMENTAL")),
        _product("MEMO", "INVESTMENT_MEMO", "CURRENT", "CLEAN_READER", ("INTEGRATED",)),
        _product("ACTION", "ACTION_BOOK", "CURRENT", "CLEAN_READER", ("INTEGRATED",)),
        _product("ACCEPTANCE", "ACCEPTANCE", "CURRENT", "INTERNAL_AUDIT"),
        _product("WORKPAPER", "PROFESSIONAL_WORKPAPER", "ACCEPTED_PARENT", "WORKPAPER"),
        _product("AUDIT", "AUDIT_ARCHIVE", "CURRENT", "INTERNAL_AUDIT"),
    ]
    if not complete:
        products = [p for p in products if p["product_id"] not in {"BASE", "SPECIALIST", "SUPPLEMENTAL", "WORKPAPER", "AUDIT"}]

    for product in products:
        path = root / product["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(product["product_id"].encode("utf-8"))

    catalog = {
        "schema_version": "1.0.0",
        "project_id": "FIXTURE_PROJECT",
        "release_id": "fixture-release",
        "products": products,
    }
    (root / "product_catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    (root / "source_review_coverage.json").write_text(json.dumps({
        "schema_version": "1.0.0",
        "project_id": "FIXTURE_PROJECT",
        "unique_source_count": 10,
        "dispositions": {
            "deep_reviewed": 6,
            "targeted_reviewed": 2,
            "duplicate": 1,
            "superseded": 1,
            "unreadable": 0,
            "out_of_scope": 0,
            "deferred": 0,
        },
        "p0_p1": {"total": 5, "completed": 5, "open_material_exceptions": 0},
        "professional_review_claim": "FULL",
        "coverage_complete": True,
        "reviewer_count": 2,
        "notes": [],
    }), encoding="utf-8")
    (root / "system_recovery_receipt.json").write_text(json.dumps({
        "schema_version": "1.0.0",
        "system_package": "fixture-system.zip",
        "expected_sha256": "0" * 64,
        "actual_sha256": "0" * 64,
        "authority_status": "RECOVERY_PARENT",
        "required_contracts_verified": ["SOURCE_TO_REPORT", "RP_FINAL"],
        "gate": "RECOVERY_PASS",
        "notes": [],
    }), encoding="utf-8")

    ids_by_pack = {
        key: [p["product_id"] for p in products if p["delivery_pack"] == pack]
        for key, pack in (
            ("clean_reader", "CLEAN_READER"),
            ("workpaper", "WORKPAPER"),
            ("internal_audit", "INTERNAL_AUDIT"),
        )
    }
    zip_info = {}
    for key, product_ids in ids_by_pack.items():
        package = root / f"{key}.zip"
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for product in products:
                if product["product_id"] in product_ids:
                    archive.write(root / product["path"], arcname=product["path"])
        with zipfile.ZipFile(package) as archive:
            count = sum(1 for member in archive.infolist() if not member.is_dir())
        zip_info[key] = {"package_path": package.name, "sha256": _sha(package), "file_count": count}

    for name, content in (
        ("guide.md", "guide"),
        ("manifest.json", "{}"),
        ("acceptance.json", "{}"),
    ):
        (root / name).write_text(content, encoding="utf-8")

    master = {
        "schema_version": "1.0.0",
        "project_id": "FIXTURE_PROJECT",
        "release_id": "fixture-release",
        "status": "PASS" if complete else "CANDIDATE",
        "product_catalog_path": "product_catalog.json",
        "packs": {
            name: {**zip_info[name], "product_ids": product_ids or [f"MISSING_{name.upper()}"]}
            for name, product_ids in ids_by_pack.items()
        },
        "authority_files": {
            "guide": "guide.md",
            "manifest": "manifest.json",
            "acceptance": "acceptance.json",
            "receipt": "rp_master_delivery.json",
        },
        "decision_boundaries": {
            "decision_ready": False,
            "transaction_authority": "NONE",
            "restricted_outputs": ["POINT_VALUATION"],
        },
    }
    (root / "rp_master_delivery.json").write_text(json.dumps(master), encoding="utf-8")


def test_complete_professional_delivery_passes(tmp_path):
    root = tmp_path / "complete"
    _write_bundle(root, complete=True)
    assert validate_professional_delivery_bundle(root) == []


def test_memo_only_delivery_fails(tmp_path):
    root = tmp_path / "memo_only"
    _write_bundle(root, complete=False)
    issues = validate_professional_delivery_bundle(root)
    assert any("missing required parent group: BASE_DD" in issue for issue in issues)
    assert any("missing required parent group: SPECIALIST" in issue for issue in issues)
    assert any("missing required parent group: SUPPLEMENTAL" in issue for issue in issues)


def test_wrong_role_pack_fails(tmp_path):
    root = tmp_path / "wrong_pack"
    _write_bundle(root, complete=True)
    catalog_path = root / "product_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    product = next(item for item in catalog["products"] if item["product_id"] == "INTEGRATED")
    product["delivery_pack"] = "WORKPAPER"
    product["reader_status"] = "CONTROL"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    issues = validate_professional_delivery_bundle(root)
    assert any("active role INTEGRATED_DD must be in CLEAN_READER" in issue for issue in issues)


def test_pack_hash_mismatch_fails(tmp_path):
    root = tmp_path / "bad_pack_hash"
    _write_bundle(root, complete=True)
    (root / "clean_reader.zip").write_bytes(b"corrupted")
    issues = validate_professional_delivery_bundle(root)
    assert any("clean_reader: package sha256 mismatch" in issue for issue in issues)
    assert any("clean_reader: package is not a ZIP archive" in issue for issue in issues)


def test_missing_authority_file_fails(tmp_path):
    root = tmp_path / "missing_authority"
    _write_bundle(root, complete=True)
    (root / "guide.md").unlink()
    issues = validate_professional_delivery_bundle(root)
    assert any("authority guide: file missing" in issue for issue in issues)


def test_local_intake_schema_blocks_analysis():
    receipt = {
        "schema_version": "1.0.0",
        "project_id": "FIXTURE_PROJECT",
        "transaction_id": "TX-1",
        "status": "READY_FOR_U_MINUS_1",
        "analysis_performed": True,
        "professional_conclusions_generated": False,
        "source_root_mutated": False,
        "counts": {
            "physical_entries": 1,
            "eligible_files": 1,
            "hash_success": 1,
            "hash_fail": 0,
            "unique_sources": 1,
            "duplicate_groups": 0,
            "unreadable_files": 0,
        },
        "hashes": {"package_sha256": "0" * 64},
        "storage": {
            "staging_status": "READY",
            "drive_status": "READY",
            "file_library_status": "READY",
        },
        "exceptions": [],
    }
    issues = validate_professional_document("local_intake", receipt)
    assert issues
