import json,hashlib,pathlib,pandas as pd,numpy as np
from pathlib import Path
WS=Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f5_unified';h=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');a=pd.read_csv(O/'evaluation/A_TO_B_METRICS.csv')
def sha(p):
 p=Path(p);return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def jl(g,v,rec):
 p=O/'RUN_TRACE'/f'{g}_{v}.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a') as f:f.write(json.dumps(rec,sort_keys=True,default=str)+'\n')
for f in (O/'RUN_TRACE').glob('*.jsonl'): f.unlink()
for p in sorted((O/'prepared').glob('*/PREPARED.json')):
 g,v=p.parent.name.rsplit('_',1);w=O/'w0'/p.parent.name;ss=O/'selection'/f'{g}_{v}.csv';meta=json.loads(p.read_text());clean=O/'clean_labels'/p.parent.name
 jl(g,v,dict(run_id='M2F5-UNIFIED-001',stage='prepare',route_id='rf-m2f5-input-fresh',input=[meta['video_path']],input_sha256=meta['video_sha256'],output=str(p),output_sha256=sha(p),status='PASS',frames=len(meta['views']),sample_rule='12_uniform_plus_4_largest_gap_midpoints'))
 jl(g,v,dict(run_id='M2F5-UNIFIED-001',stage='mask_clean',route_id='rf-m2f5-mask-clean-2d',input=str(p),input_sha256=sha(p),output=str(clean),status='PASS',frames=len(meta['views']),rule='DXY ring_holes.run ring_enclosed_small_background_v1'))
 if (w/'camera_result.npz').exists():
  jl(g,v,dict(run_id='M2F5-UNIFIED-001',stage='w0',route_id='rf-w0-camera@2',input=[str(p),str(clean)],output=str(w),output_sha256=sha(w/'camera_result.npz'),status='PASS',tracks_source=(O/'work'/p.parent.name/'tracks_source.txt').read_text().strip()))
 else:
  jl(g,v,dict(run_id='M2F5-UNIFIED-001',stage='w0',route_id='rf-w0-camera@2',input=[str(p),str(clean)],output=str(w),status='FAIL',reason='NO_CAMERA_RESULT'))
 if ss.exists():
  s=pd.read_csv(ss);jl(g,v,dict(run_id='M2F5-UNIFIED-001',stage='select',route_id='rf-m2f5-t10+t13',input=str(w/'camera_result.npz'),output=str(ss),output_sha256=sha(ss),status='PASS',targets=len(s),ready=int(s.ready.sum())))
 for _,r in h[(h.group_id==g)&(h.video_id.astype(str).str.zfill(3)==v)&(h.status=='PASS')].iterrows():
  out=Path(r.output_dir);jl(g,v,dict(run_id='M2F5-UNIFIED-001',stage='hero',route_id='rf-m2f5-hero-native',input=str(ss),input_sha256=sha(ss),target=r.target_id,supports=str(r.support_ids).split(';'),output=str(out),output_sha256=sha(out/'HERO_native.npz'),status='PASS'))
  for _,x in a[(a.group_id==g)&(a.video_id.astype(str).str.zfill(3)==v)&(a.target_id==r.target_id)].iterrows():
   jl(g,v,dict(run_id='M2F5-UNIFIED-001',stage='a_to_b',route_id='rf-m2f5-a-to-b',input=str(out/'RAW_NATIVE_MESH.npz'),target_B_id=x.support_id,output='evaluation/A_TO_B_METRICS.csv',status='PASS',coverage=x.target_coverage))
print('trace files',len(list((O/'RUN_TRACE').glob('*.jsonl'))))
