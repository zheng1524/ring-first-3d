"""Read-only final evidence verification; no camera or HERO computation."""
import gzip,csv,ast,re,time,os,collections
from common import *
start=time.time();rows=read(B/'ALL_UNIQUE_SOURCES.json')+read(B/'ALL_ALIAS_RESULTS.json');assert len(rows)==204
assert len({r['combo_id']for r in rows})==174
for r in rows:
 for field in ['native','mesh']:assert sha(r[field+'_path'])==r[field+'_sha256'],r['source_id']+field
source=read(P12/'evidence/RESTORATION_SOURCE_LOCK_R3.json');source=source.get('files',source.get('sources',source))
if isinstance(source,dict):source=[dict(path=p,sha256=v if isinstance(v,str)else v['sha256'])for p,v in source.items()]
for r in source:assert sha(r['path'])==r['sha256'],r['path']
base=read(B12/'BASELINE_FROZEN.json')['files']
for r in base:assert sha(r['path'])==r['sha256'],r['path']
work=read(T/'evidence/START_CONTENT_STATE.json')['files']
for p,h in work.items():assert sha(p)==h,p
budget=read(T/'evidence/HERO_BUDGET_FROZEN.json');run=read(B/'HERO_RUN_RECEIPT.json');assert budget['new_inference_budget']==run['new_inference_started']==69 and run['completed']==76 and run['failed']==0
assert len(list((B/'H004').rglob('INFERENCE_STARTED.json')))==69
orig=read(B/'V6_SOURCES.json');assert len(orig)==128 and sum(r['formal']for r in orig)==66 and sum(r['formal']and r['target_qualified']for r in orig)==14
aliases=[r for r in rows if not r['canonical']];lookup={r['source_id']:r for r in rows};equal=[]
for r in aliases:
 a=np.load(r['native_path'])['depth_mm'];b=np.load(lookup[r['canonical_source_id']]['native_path'])['depth_mm'];assert np.array_equal(a,b),r['source_id'];equal.append(r['source_id'])
# Full gallery references, CSV structure, byte-preserved outputs and all-case denominators.
html=(T/'HERO_ALL_VIDEOS_INDEX.html').read_text();refs=re.findall(r'(?:src|href)="([^"#]+)"',html)
for ref in refs:
 if '://'not in ref:assert (T/ref).exists(),ref
manifest=list(csv.DictReader(open(T/'SOURCE_MANIFEST.csv')));assert len(manifest)==204 and len({r['source_id']for r in manifest})==204
summary=list(csv.DictReader(open(T/'VIDEO_SUMMARY.csv')));assert len(summary)==20 and len({r['case']for r in summary})==10
for row in manifest:
 assert row['camera_input_sha256'] and row['intrinsics_input_sha256'] and row['model_sha256'];assert len(json.loads(row['input_identity']))==4
for p in (T/'code').glob('*.py'):ast.parse(p.read_text())
stat=os.statvfs(W);receipt=dict(seconds=time.time()-start,output_native_and_mesh_hashes=len(rows)*2,unique_combinations=174,total_original_outputs=204,aliases_depth_bitwise_equal=len(equal),scientific_source_hashes=len(source),frozen_M2F12_hashes=len(base),existing_work_content_hashes=len(work),new_inference=69,reused=7,failures=0,resource_retries=0,html_references=len(refs),video_route_rows=len(summary),V6_original_members=66,V6_member_target_qualified=14,V6_member_target_not_qualified=52,final_available_bytes=stat.f_bavail*stat.f_frsize,mount_device=os.stat(W).st_dev)
save(T/'evidence/FINAL_VERIFICATION.json',receipt);print(receipt)
