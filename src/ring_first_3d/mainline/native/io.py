"""Small portable IO helpers; never infer paths from an old experiment tree."""
import hashlib
import json
from pathlib import Path
import numpy as np

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def serial(value):
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [serial(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return serial(value.tolist())
    if isinstance(value, np.generic):
        return serial(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value

def save_json(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(serial(value), indent=2, ensure_ascii=False, allow_nan=False) + "\n")

def read_json(path):
    return json.loads(Path(path).read_text())

def check_assets(root, manifest):
    root = Path(root).resolve()
    for item in manifest["files"]:
        p = (root / item["path"]).resolve()
        if not p.is_relative_to(root):
            raise ValueError("Asset path escapes the data root")
        if sha256(p) != item["sha256"]:
            raise ValueError("Asset checksum mismatch: " + item["path"])
