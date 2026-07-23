from __future__ import annotations
from pathlib import Path
import hashlib, json, zipfile

STATE_REQUIRED = {"system","project_id","project_name","status","accepted_product_class","project_boundaries","next"}
LOCK_REQUIRED = {"release","status","release_class","hard_controls","next"}

def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def validate_state(path: str | Path) -> list[str]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = [f"missing:{k}" for k in sorted(STATE_REQUIRED - set(obj))]
    pb = obj.get("project_boundaries", {})
    for k in ("critical_gates_open","restricted_outputs","decision_ready"):
        if k not in pb: errors.append(f"missing:project_boundaries.{k}")
    return errors

def validate_release_lock(path: str | Path) -> list[str]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    return [f"missing:{k}" for k in sorted(LOCK_REQUIRED - set(obj))]

def validate_zip(path: str | Path) -> list[str]:
    errors=[]
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad: errors.append(f"corrupt:{bad}")
        names=z.namelist()
        roots={n.split('/',1)[0] for n in names if n}
        if len(roots)!=1: errors.append("not_single_root")
        for n in names:
            if n.startswith('/') or '..' in Path(n).parts: errors.append(f"unsafe_path:{n}")
    return errors
