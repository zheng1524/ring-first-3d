"""Review only staged additions/modifications; never upload large research payloads."""
import json
import hashlib
from pathlib import Path
import subprocess


def main():
    rows=[];bad=[];total=0
    names=subprocess.check_output(["git","diff","--cached","--name-only","--diff-filter=ACM","-z"]).split(b"\0")
    forbidden={".npz",".npy",".pt",".pth",".ckpt",".safetensors",".mp4",".avi",".mov",".glb",".zip",".gz",".blend",".so"}
    for raw in names:
        if not raw:continue
        name=raw.decode();data=subprocess.check_output(["git","show",":"+name]);n=len(data);total+=n
        r=dict(path=name,bytes=n);rows.append(r)
        # Required per-checkpoint audit manifest, not experiment output. Bound
        # this single exception by its immutable phase-0 hash and a 2 MB cap.
        frozen_manifest = False
        if name == "maintenance/storage/PRESERVED_ASSETS.csv" and n < 2_000_000:
            freeze=json.loads(Path("maintenance/storage/PHASE0_FREEZE.json").read_text())
            frozen_manifest=hashlib.sha256(data).hexdigest()==freeze["manifests"]["PRESERVED_ASSETS.csv"]
        if (n>1_000_000 and not frozen_manifest) or Path(name).suffix in forbidden or "/local_only/" in name or "/runtime/" in name:
            bad.append(r)
        if any(b"-----BEGIN "+label+b"-----" in data for label in [b"PRIVATE KEY",b"OPENSSH PRIVATE KEY"]):
            bad.append(dict(path=name,reason="private key"))
    print(json.dumps(dict(status="PASS" if not bad else "FAIL",files=len(rows),bytes=total,largest=sorted(rows,key=lambda r:-r["bytes"])[:5],violations=bad),indent=2))
    raise SystemExit(bool(bad))


if __name__=="__main__":main()
