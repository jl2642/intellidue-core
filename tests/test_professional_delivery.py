from __future__ import annotations

import json
from pathlib import Path

from intellidue_core.professional_delivery import (
    validate_professional_delivery_bundle,
    validate_professional_document,
)

SHA = "0" * 64


def _product(product_id, role, lifecycle, pack, parents=()):
    return {
        "product_id": product_id,
        "title": product_id.replace("_", " ").title(),
        "role": role,
        "lifecycle": lifecycle,
        "reader_status": "READER" if pack == "CLEAN_READER" else ("CONTROL" if pack == "WORKPAPER" else "AUDIT"),
        "delivery_pack": pack,
        "authority_level": "PRIMARY" if role == "INTEGRATED_DD" else "PARENT",
        "path": f"{pack.lower()}/{product_id.lower()}.json",
        "size_bytes": 1,
        "sha256": SHA,
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

    catalog = {
        "schema_version": "1.0.0",
        "project_id": "FIXTURE_PROJECT",
        "release_id": "fixture-release",
        "products": products,
    }
    ids_by_pack = {
        key: [p["product_id"] for p in products if p["delivery_pack"] == pack]
        for key, pack in (
            ("clean_reader", "CLEAN_READER"),
            ("workpaper", "WORKPAPER"),
            ("internal_audit", "INTERNAL_AUDIT"),
        )
    }
    master = {
        "schema_version": "1.0.0",
        "project_id": "FIXTURE_PROJECT",
        "release_id": "fixture-release",
        "status": "PASS" if complete else "CANDIDATE",
        "product_catalog_path": "product_catalog.json",
        "packs": {
            name: {
                "package_path": f"{name}.zip",
                "sha256": SHA,
                "file_count": max(1, len(product_ids)),
                "product_ids": product_ids or [f"MISSING_{name.upper()}"],
            }
            for name, product_ids in ids_by_pack.items()
        },
        "authority_files": {
            "guide": "guide.md",
            "manifest": "manifest.json",
            "acceptance": "acceptance.json",
            "receipt": "receipt.json",
        },
        "decision_boundaries": {
            "decision_ready": False,
            "transaction_authority": "NONE",
            "restricted_outputs": ["POINT_VALUATION"],
        },
    }
    coverage = {
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
    }
    recovery = {
        "schema_version": "1.0.0",
        "system_package": "fixture-system.zip",
        "expected_sha256": SHA,
        "actual_sha256": SHA,
        "authority_status": "RECOVERY_PARENT",
        "required_contracts_verified": ["SOURCE_TO_REPORT", "RP_FINAL"],
        "gate": "RECOVERY_PASS",
        "notes": [],
    }
    for name, obj in (
        ("product_catalog.json", catalog),
        ("rp_master_delivery.json", master),
        ("source_review_coverage.json", coverage),
        ("system_recovery_receipt.json", recovery),
    ):
        (root / name).write_text(json.dumps(obj), encoding="utf-8")


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
        "hashes": {"package_sha256": SHA},
        "storage": {
            "staging_status": "READY",
            "drive_status": "READY",
            "file_library_status": "READY",
        },
        "exceptions": [],
    }
    issues = validate_professional_document("local_intake", receipt)
    assert issues
