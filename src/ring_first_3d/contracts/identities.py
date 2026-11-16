import hashlib
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_assets(records):
    for path, rec in records.items():
        p = Path(path)
        if p.stat().st_size != rec["bytes"] or sha256(p) != rec["sha256"]:
            raise ValueError("Frozen asset mismatch: " + str(p))
    return len(records)


def validate_split(views, held=()):
    ids = [v["id"] for v in views]
    if len(set(ids)) != len(ids) or set(ids) & set(held):
        raise ValueError("Duplicate view identity or FIT/HOLDOUT leakage")
    if any(v.get("role") not in ("FIT", "candidateFIT") for v in views):
        raise ValueError("Selection accepts explicit FIT records only")
    return ids
