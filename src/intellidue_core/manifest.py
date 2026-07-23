from __future__ import annotations
from pathlib import Path
import hashlib, json

def file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def build_manifest(root: str | Path) -> dict:
    root=Path(root)
    files=[]
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        files.append({'path':p.relative_to(root).as_posix(),'size_bytes':p.stat().st_size,'sha256':file_hash(p)})
    return {'root':root.name,'files':files}

def save_manifest(root: str | Path, output: str | Path):
    Path(output).write_text(json.dumps(build_manifest(root),indent=2),encoding='utf-8')
