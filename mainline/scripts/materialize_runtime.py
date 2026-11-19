"""Restore exact local runtime files; never install packages or copy model weights."""
import json,hashlib,argparse,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--source-prefix',action='append',default=[],help='OLD=NEW relocation of provisioned dependency roots');a=p.parse_args();maps=[s.split('=',1)for s in a.source_prefix]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
missing=[];verified=0
for x in json.loads((R/'mainline/manifests/RUNTIME_FILES.json').read_text()):
 dst=R/x['new_path'];src=Path(x['original_path'])
 for old,new in maps:
  if str(src).startswith(old):src=Path(new+str(src)[len(old):]);break
 if dst.is_file():assert sha(dst)==x['sha256'];verified+=1;continue
 if not src.is_file():missing.append(str(src));continue
 assert sha(src)==x['sha256'];dst.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(src,dst);assert sha(dst)==x['sha256'];verified+=1
print(json.dumps(dict(status='PASS'if not missing else'NOT_EVALUABLE_EXTERNAL_DEPENDENCY',verified=verified,missing=missing),indent=2));sys.exit(0 if not missing else 1)
