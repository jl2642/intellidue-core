from __future__ import annotations

from pathlib import Path
from typing import Any

from .promotion_support import remove_created
from .workspace import WorkspaceLock, ensure_layout, finish_journal, read_json, restore_previous


def recover_workspace(workspace: str | Path, *, force_lock: bool = False) -> dict[str, Any]:
    root = Path(workspace)
    if force_lock:
        (root / ".promotion.lock").unlink(missing_ok=True)
    with WorkspaceLock(root):
        paths = ensure_layout(root)
        if not paths["active"].exists():
            return {"recovered": False, "reason": "no active transaction"}
        journal = read_json(paths["active"])
        assert journal is not None
        if journal.get("status") in {"COMMITTED", "ROLLED_BACK", "RECOVERED"}:
            finish_journal(paths, journal, journal["status"], journal.get("detail"))
            return {"recovered": False, "reason": f"finalized {journal['status'].lower()} transaction", "transaction_id": journal["transaction_id"]}
        restore_previous(paths, journal)
        if journal.get("operation") == "PROMOTE":
            remove_created(journal)
        finish_journal(paths, journal, "RECOVERED", "recovered from unfinished transaction")
        return {"recovered": True, "transaction_id": journal["transaction_id"], "operation": journal["operation"]}
