"""Small reproducible evidence package, exact index for larger local artifacts."""
import json,hashlib,tarfile,shutil,sys,subprocess,datetime
from pathlib import Path
from historical_io import W,sha
T=Path(__file__).resolve().parent.parent;B=W/'runs/m2f12_historical004'
def read(p):return json.loads(Path(p).read_text())
def freeze_baseline():
 p=B/'BASELINE_FROZEN.json'
 assert not p.exists(),'Baseline freeze is immutable'
 rows=[]
 for reg in read(T/'evidence/INPUT_REGISTRY.json'):
  R=B/'H004_RAW_BASELINE'/reg['case'];stages={s:read(R/f'STAGE_{s}.json')['status']if(R/f'STAGE_{s}.json').exists()else'NOT_RUN'for s in ['prepare','seed','recover']}
  assert stages['recover']=='COMPLETED'or'FAILED'in stages.values(),(reg['case'],stages)
  for f in sorted(R.rglob('*')):
   if f.is_file()and'__pycache__'not in f.parts:rows.append(dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f)))
 p.write_text(json.dumps(dict(epoch=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows,groups=5,videos=10,optimization_decision='No H004_PLUS: no certified common independent outcome for causal optimization; baseline and failure mechanisms retained'),indent=2));print('BASELINE_FROZEN',len(rows))
def package():
 frozen=read(B/'BASELINE_FROZEN.json');changed=[x['path']for x in frozen['files']if sha(x['path'])!=x['sha256']];assert not changed,changed
 E=T/'evidence/run';E.mkdir(parents=True,exist_ok=True);members=[];index=[]
 for f in sorted(B.rglob('*')):
  if not f.is_file()or'__pycache__'in f.parts:continue
  rel=f.relative_to(B);index.append(dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f)))
  # Metadata, exact configuration, stage logs, and complete landmark audit are compact.
  if f.suffix in ['.json','.jsonl','.log','.csv','.txt']and 'runtime'not in str(rel)and'cache'not in str(rel).lower():members.append(f)
  if f.name=='INDEPENDENT_VIDEO.npz':members.append(f)
 archive=T/'archive/RESTORATION_EVIDENCE.tar.gz'
 with tarfile.open(archive,'w:gz')as tar:
  for f in members:tar.add(f,arcname=str(f.relative_to(B)),recursive=False)
 with tarfile.open(archive,'r:gz')as tar:
  for f in members:
   data=tar.extractfile(str(f.relative_to(B))).read();assert hashlib.sha256(data).hexdigest()==sha(f)
 (T/'evidence/LOCAL_ARTIFACT_INDEX.json').write_text(json.dumps(index,indent=2))
 for name in ['BASELINE_FROZEN.json','BATCH_COMMANDS.json','HERO_PLANS_FROZEN.json']:
  if(B/name).exists():shutil.copyfile(B/name,E/name)
 for name in ['RESULTS.json','MODEL_RECEIPT.json']:
  if(B/'HERO_LIMITED'/name).exists():shutil.copyfile(B/'HERO_LIMITED'/name,E/('HERO_'+name))
 receipt=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),verified_members=len(members),local_artifacts=len(index),local_total_bytes=sum(x['bytes']for x in index),raw_and_weights_not_uploaded=True)
 source_archive=T/'archive/HISTORICAL_SOURCE_SNAPSHOT.tar.gz';source_files=[Path(p)for p in read(T/'evidence/RESTORATION_SOURCE_LOCK_R3.json')['files']if'/new-polyp-dxy/'not in p and'/freeze/model/'not in p]
 with tarfile.open(source_archive,'w:gz')as tar:
  for p in source_files:tar.add(p,arcname=str(p.relative_to('/home/liu')),recursive=False)
 with tarfile.open(source_archive,'r:gz')as tar:
  for p in source_files:assert hashlib.sha256(tar.extractfile(str(p.relative_to('/home/liu'))).read()).hexdigest()==sha(p)
 receipt['source_snapshot']=dict(path=str(source_archive),bytes=source_archive.stat().st_size,sha256=sha(source_archive),verified_files=len(source_files),DXY_and_model='external read-only dependencies; per-file hashes in R3 lock, model SHA in preparation provenance')
 (T/'evidence/RESTORATION_ARCHIVE_RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(receipt)
if __name__=='__main__':{'freeze':freeze_baseline,'package':package}[sys.argv[1]]()
