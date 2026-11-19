"""Restore exact large flat audit tables from their small Git-distributed packs."""
import argparse,json,gzip,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];T=R/'maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001'
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=T);a=p.parse_args();a.output.mkdir(exist_ok=True,parents=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
for x in json.loads((T/'INVENTORY_PACK_MANIFEST.json').read_text())['files']:
 src=T/x['packed_path'];dst=a.output/x['flat_path'];assert sha(src)==x['packed_sha256']
 if dst.exists():assert sha(dst)==x['flat_sha256'];continue
 with gzip.open(src,'rb')as f,dst.open('xb')as g:shutil.copyfileobj(f,g)
 assert sha(dst)==x['flat_sha256']
print('Complete inventories restored/verified without changing any scientific asset.')
