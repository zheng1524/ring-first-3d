"""Supplement frozen candidates with source-payload proof, never expand scope."""
from pathlib import Path
import csv
import hashlib
import json
import re
from audit_storage import OUT, ASSET, digest


def main():
    output=OUT/"CACHE_RECOVERY_PROOF.json"
    if output.exists():raise FileExistsError("Recovery proof is immutable")
    rows=list(csv.DictReader((OUT/"DELETE_MANIFEST.csv").open()))
    proof=[];sources={}
    for row in rows:
        p=Path(row["PATH"]);data=p.read_bytes();assert digest(p)==row["SHA256"]
        paths=re.findall(rb"http://127\.0\.0\.1:\d+/([A-Za-z0-9_./-]+?\.(?:glb|html|jpg|json))",data[:4096])
        rec=dict(cache=row["PATH"],kind="browser index or regenerable external browser resource",eligible=True)
        if paths:
            source=(ASSET/paths[-1].decode()).resolve()
            if ASSET not in source.parents or not source.is_file():
                rec.update(eligible=False,reason="Local response source not recoverable")
            else:
                raw=source.read_bytes();match=data.find(raw)
                rec.update(source=str(source),source_SHA256=hashlib.sha256(raw).hexdigest(),
                           source_bytes=len(raw),payload_byte_identical=match>=0,payload_offset=match)
                sources[str(source)]={"sha256":rec["source_SHA256"],"bytes":len(raw)}
                if match<0:
                    rec.update(eligible=False,reason="Historical HTTP payload differs; preserve cache pending review")
                else:rec["kind"]="byte-identical HTTP copy of preserved local source"
        elif p.stat().st_size>1_000_000:
            rec.update(eligible=False,reason="Large cache response without proven source")
        proof.append(rec)
    value=dict(manifest_SHA256=digest(OUT/"DELETE_MANIFEST.csv"),files=proof,preserved_sources=sources,
               scope="Only frozen HTTP caches. Exact source-body proof for local research responses; retain any changed payload.")
    output.write_text(json.dumps(value,indent=2)+"\n")
    print(json.dumps(dict(eligible=sum(r["eligible"]for r in proof),retained=[r for r in proof if not r["eligible"]],sources=len(sources))))


if __name__=="__main__":main()
