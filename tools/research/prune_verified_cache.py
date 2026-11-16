"""Unlink only immutable, revalidated file candidates; no recursive directory deletion."""
from pathlib import Path
import csv
import json
import os
import shutil
import stat
import tarfile
import time
from audit_storage import OUT, ASSET, PROTECTED, digest, project_processes, git


def main():
    freeze=json.loads((OUT/"PHASE0_FREEZE.json").read_text())
    phase2=json.loads((OUT/"PHASE2_FREEZE.json").read_text())
    for p,h in phase2["results"].items():
        if digest(p)!=h or json.loads(Path(p).read_text())["status"]!="PASS":
            raise ValueError("Phase-2 result changed or did not pass")
    for name,h in freeze["manifests"].items():
        if digest(OUT/name)!=h:raise ValueError("Frozen manifest changed: "+name)
    logpath=OUT/"DELETION_LOG.csv"
    if logpath.exists():raise FileExistsError("Deletion log exists; audit partial run, never blindly repeat")
    recovery=json.loads((OUT/"CACHE_RECOVERY_PROOF.json").read_text())
    backup=json.loads((OUT/"CACHE_BACKUP_MANIFEST.json").read_text())
    if digest(backup["archive"])!=backup["sha256"]:raise ValueError("Historical cache backup changed")
    backed={r["path"] for r in backup["members"]}
    with tarfile.open(backup["archive"],"r:gz") as archive:
        import hashlib
        for r in backup["members"]:
            stream=archive.extractfile(r["member"]);h=hashlib.sha256()
            for block in iter(lambda:stream.read(1<<20),b""):h.update(block)
            if h.hexdigest()!=r["sha256"]:raise ValueError("Backup member hash mismatch")
    if digest(OUT/"DELETE_MANIFEST.csv")!=recovery["manifest_SHA256"]:raise ValueError("Recovery manifest mismatch")
    for p,r in recovery["preserved_sources"].items():
        if digest(p)!=r["sha256"] or Path(p).stat().st_size!=r["bytes"]:raise ValueError("Preserved HTTP source changed")
    for row in csv.DictReader((OUT/"PRESERVED_ASSETS.csv").open()):
        if digest(row["PATH"])!=row["SHA256"]:raise ValueError("Preserved asset changed")
    rows=list(csv.DictReader((OUT/"DELETE_MANIFEST.csv").open()))
    proof={r["cache"]:r for r in recovery["files"]}
    # Revalidate every candidate BEFORE deleting any candidate.
    for r in rows:
        p=Path(r["PATH"])
        if p.resolve()!=p or any(p==q or q in p.parents for q in PROTECTED):raise ValueError("Protected/symlink path")
        rel=p.relative_to(ASSET/"runtime")
        if not (len(rel.parts)>=5 and rel.parts[0].startswith("chrome") and rel.parts[1:4]==("Default","Cache","Cache_Data")):
            raise ValueError("Outside bounded HTTP cache scope")
        s=p.lstat()
        if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or r["CLASSIFICATION"]!="VERIFIED_REDUNDANT":raise ValueError("Nonregular/shared candidate")
        if (s.st_ino,s.st_dev,s.st_mtime_ns,s.st_size)!=(int(r["INODE"]),int(r["DEVICE"]),int(r["MTIME_NS"]),int(r["BYTES"])) or digest(p)!=r["SHA256"]:
            raise ValueError("Candidate changed since audit: "+str(p))
        profile=ASSET/"runtime"/rel.parts[0]
        if project_processes(profile):raise ValueError("Active browser profile: "+str(profile))
    before=shutil.disk_usage(ASSET);t=time.time();deleted=logical=allocated=0
    with logpath.open("x",newline="") as f:
        writer=csv.DictWriter(f,["PATH","SHA256","BYTES","ALLOCATED_BYTES","STATUS","EPOCH","REASON"]);writer.writeheader()
        for r in rows:
            p=Path(r["PATH"]);status="PRESERVED";reason=proof[r["PATH"]].get("reason","")
            if proof[r["PATH"]]["eligible"] or r["PATH"] in backed:
                # Per-file second check closes the time gap after the all-file audit.
                s=p.lstat()
                if p.resolve()!=p or s.st_ino!=int(r["INODE"]) or s.st_mtime_ns!=int(r["MTIME_NS"]) or digest(p)!=r["SHA256"]:
                    raise ValueError("Candidate changed at unlink")
                p.unlink();status="DELETED";reason="SHA-verified exact compressed backup" if r["PATH"] in backed else "Frozen, no active browser dependency; preserved/recoverable HTTP source"
                deleted+=1;logical+=int(r["BYTES"]);allocated+=int(r["ALLOCATED_BYTES"])
            writer.writerow({**{k:r[k]for k in ["PATH","SHA256","BYTES","ALLOCATED_BYTES"]},"STATUS":status,"EPOCH":time.time(),"REASON":reason})
            f.flush();os.fsync(f.fileno())
    os.sync();after=shutil.disk_usage(ASSET)
    result=dict(epoch=t,deleted_files=deleted,deleted_directories=0,logical_bytes=logical,allocated_bytes=allocated,
                backup_bytes=backup["bytes"],backup_allocated_bytes=backup["allocated_bytes"],
                net_logical_reduction=logical-backup["bytes"],net_allocated_reduction=allocated-backup["allocated_bytes"],
                before=dict(zip(["total","used","free"],before)),after=dict(zip(["total","used","free"],after)),
                measured_free_delta=after.free-before.free,
                caveat="df delta includes other system activity; stat allocated bytes identify removed file blocks. Empty cache directories intentionally retained.",
                remaining_uncertain_files=len(rows)-deleted,protected_modified=False,remote_branches_deleted=0)
    (OUT/"DELETION_RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
