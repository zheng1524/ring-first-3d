"""Preserve older HTTP payloads exactly before making them deletion-eligible."""
import csv
import hashlib
import json
from pathlib import Path
import tarfile
from audit_storage import OUT, digest, REPO


def main():
    proof=json.loads((OUT/"CACHE_RECOVERY_PROOF.json").read_text())
    rows={r["PATH"]:r for r in csv.DictReader((OUT/"DELETE_MANIFEST.csv").open())}
    uncertain=[r for r in proof["files"] if not r["eligible"]]
    folder=REPO/"experiments/TASK-RESEARCH-HARNESS-STORAGE-001/local_only"
    folder.mkdir(parents=True,exist_ok=True)
    backup=folder/"historical_http_cache.tar.gz"
    if backup.exists() or (OUT/"CACHE_BACKUP_MANIFEST.json").exists():raise FileExistsError("Backup is immutable")
    records=[]
    with tarfile.open(backup,"x:gz",compresslevel=6) as archive:
        for i,rec in enumerate(uncertain):
            p=Path(rec["cache"]);assert digest(p)==rows[str(p)]["SHA256"]
            name=f"{i:02d}/{p.name}"
            archive.add(p,arcname=name,recursive=False)
            records.append(dict(path=str(p),member=name,sha256=rows[str(p)]["SHA256"],bytes=p.stat().st_size))
    # Complete read-back hashes, not just a successful tar exit code.
    with tarfile.open(backup,"r:gz") as archive:
        for rec in records:
            h=hashlib.sha256();n=0
            stream=archive.extractfile(rec["member"])
            for block in iter(lambda:stream.read(1<<20),b""):
                h.update(block);n+=len(block)
            if h.hexdigest()!=rec["sha256"] or n!=rec["bytes"]:raise ValueError("Backup read-back mismatch")
    data=dict(archive=str(backup),sha256=digest(backup),bytes=backup.stat().st_size,
              allocated_bytes=backup.stat().st_blocks*512,members=records,
              verified="Every archived cache file read back and SHA256-identical",
              restore="Use tarfile.extractfile(member) to write the recorded original path after verifying archive and member hashes; restore only inside the frozen cache scope.",
              policy="LOCAL_ONLY exact backup, never upload full cache/GLB to GitHub; retain archive until asset retention is reviewed")
    (OUT/"CACHE_BACKUP_MANIFEST.json").write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({k:v for k,v in data.items()if k!="members"},indent=2))


if __name__=="__main__":main()
