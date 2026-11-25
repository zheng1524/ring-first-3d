"""Export small evidence and render complete video groups after their runs finish."""
import csv,json,shutil,time,collections
from pathlib import Path
import numpy as np
from .route import W,T,B,GROUPS,MODEL_SHA,read,save,sha,head

def write_csv(path,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with Path(path).open('w',newline='')as f:
  w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False)if isinstance(v,(list,dict))else v for k,v in r.items()}for r in rows)

def export():
 from .evaluate import P12
 video=[];sources=[];gates=[];identities=[];unused=[]
 expected=[('BASELINE',g+'_'+v)for g in GROUPS for v in ['004','005']]+[('HIST',g+'_'+v)for g in GROUPS for v in ['004','005']]+[('GRAPH',c)for c in read(T/'config/PROTOCOL.json')['pilot_cases']]
 for variant,case in expected:
  O=B/'evaluation'/variant/case
  if not(O/'COMPLETE.json').exists():raise RuntimeError('Missing complete evaluation '+str(O))
  s=read(O/'SUMMARY.json');R=Path(s['run_path']);rows=read(O/'RESULTS.json');assert len(rows)==s['legal_combinations'];video.append({k:v for k,v in s.items()if not isinstance(v,(list,dict))})
  meta=read(B/'prepared'/case/'PREPARED.json')
  if variant=='BASELINE':
   actual={r['tag']for r in rows};run_records={x['tag']:x for x in read(R/'metrics/MVS005_supported_runs.json')}
   for c in read(R/'inputs/MVS_supported_cases.json'):
    if c['tag']not in actual:
     receipt=run_records.get(c['tag'],{});assert receipt.get('failure')=='ALTERNATE_NOT_NEEDED',receipt
     unused.append(dict(case=case,tag=c['tag'],status='ALTERNATE_NOT_NEEDED_NOT_EXECUTED',plan=c,execution_receipt=receipt))
  dest=T/'evidence/runs'/variant/case;dest.mkdir(parents=True,exist_ok=True)
  for n in ['SUMMARY.json','RESULTS.json','PAIR_DEPTH_CONSISTENCY.json','COMPLETE.json']:
   shutil.copy2(O/n,dest/n)
  for n in ['CAMERA_STARTED.json','CAMERA_COMPLETE.json','CAMERA_FAILURE.json','RUN_STATE.json','PLAN_FROZEN.json','HERO_STARTED.json','HERO_COMPLETE.json','CONTROLLER_FAILURE.json','config.json','inputs/ledger005.json','inputs/REFERENCE_RECEIPT.json','inputs/MVS_supported_cases.json','inputs/PACKAGE_ADAPTER.json','metrics/GATES.json','metrics/local_validation.json','metrics/local005_solver.json','metrics/track005.json','metrics/MVS005_supported_runs.json','metrics/surfaces005.json','predictions/local005_primary.json']:
   p=R/n
   if p.exists():d=dest/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
  for p in list((R/'predictions').glob('local005_camera_*.npz'))+list((R/'metrics').glob('freeze*protocol*.json')):
   d=dest/p.relative_to(R);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
  surfaces={x['tag']:x for x in read(R/'metrics/surfaces005.json')}if(R/'metrics/surfaces005.json').exists()else{}
  L=read(R/'inputs/ledger005.json');primary=read(R/'predictions/local005_primary.json')['primary_version'];camera=R/f'predictions/local005_camera_{primary}.npz';ch=sha(camera)
  for r in rows:
   p=r['plan'];inputs=[L[i]for i in [p['reference']]+p['sources']];sources.append(dict(raw_video_path=meta['raw_path'],raw_sha256=meta['raw_sha256'],official_model_sha256=MODEL_SHA,variant=variant,case=case,status=r['status'],tag=r['tag'],target_raw=L[p['reference']]['raw_frame'],support_raw=[L[i]['raw_frame']for i in p['sources']],rule=r.get('rule_version',p.get('rule_version','M2F10')),old_rule=r.get('old_rule_generated',p.get('old_rule_generated',True)),addition_reasons=p.get('addition_reasons',[]),target_own_old_pass=r.get('target_own_old_pass'),target_own_new_pass=r.get('target_own_new_pass'),input_sha256=p.get('input_sha256'),RGB_sha256=[x['RGB_SHA256']for x in inputs],Mask_sha256=[x['Mask_SHA256']for x in inputs],camera_path=str(camera),camera_sha256=ch,mesh_path=r.get('mesh_path'),mesh_sha256=r.get('mesh_sha256'),native_path=r.get('native_path'),native_sha256=r.get('native_sha256'),ring_evaluation_status='EVALUABLE'if r.get('ring',{}).get('MAE_mm')is not None else'NOT_EVALUABLE',ring_MAE_mm=r.get('ring',{}).get('MAE_mm'),ring_P95_mm=r.get('ring',{}).get('p95_mm'),ring_max_mm=r.get('ring',{}).get('max_mm'),ring_over5_fraction=r.get('ring',{}).get('over5_fraction'),ring_common_pixels=r.get('ring',{}).get('CAD_common_pixels'),sparse_held=r.get('sparse_held'),polyp_sparse_held=surfaces.get(r['tag'],{}).get('heldout_polyp'),noninput_B=r.get('noninput_B'),failure_reason=r.get('failure_reason')))
  for r in s['not_admitted_targets']:sources.append(dict(variant=variant,case=case,status='NO_LEGAL_COMBINATION',tag='',target_raw=r['raw_target'],support_raw=r['raw_support'],rule='Q1',old_rule=False,camera_path=str(camera),camera_sha256=ch,failure_reason=r['failure_reason']))
  if(R/'metrics/GATES.json').exists():
   for g in read(R/'metrics/GATES.json'):gates.append(dict(variant=variant,case=case,**g))
  for p in [R/'RUN_STATE.json',camera,O/'COMPLETE.json']:identities.append(dict(variant=variant,case=case,path=str(p),sha256=sha(p)))
 for case in sorted({c for _,c in expected}):
  dest=T/'evidence/prepared'/case;dest.mkdir(parents=True,exist_ok=True)
  for n in ['PREPARED.json','SELECTION.json']:shutil.copy2(B/'prepared'/case/n,dest/n)
 write_csv(T/'BASELINE_UNUSED_CANDIDATES.csv',unused)
 write_csv(T/'VIDEO_COMPARISON.csv',video);write_csv(T/'SOURCE_MANIFEST.csv',sources);write_csv(T/'CAMERA_GATES.csv',gates);save(T/'evidence/LOCAL_IDENTITIES.json',identities)
 for p in (B/'protocols').glob('*.json'):
  d=T/'evidence/protocols'/p.name;d.parent.mkdir(exist_ok=True);shutil.copy2(p,d)
 shutil.copy2(B/'INFERENCE_STARTS.jsonl',T/'evidence/INFERENCE_STARTS.jsonl')
 for p in B.glob('*.log'):
  if p.name in ['local_viewer.log']or p.name.startswith('publish'):continue
  d=T/'logs'/p.name;d.parent.mkdir(exist_ok=True);shutil.copy2(p,d)
 save(T/'evidence/DELIVERY_COUNTS.json',dict(evaluation_run_rows=len(video),unique_videos=len({x['case']for x in video}),physical_groups=len({x['case'].rsplit('_',1)[0]for x in video}),baseline_unused_alternates=len(unused),sources_including_rejections=len(sources),actual_inference_starts=len((B/'INFERENCE_STARTS.jsonl').read_text().splitlines()),native_success=sum(x['inference_success']for x in video if x['variant']!='BASELINE'),candidate_10video_success=sum(x['inference_success']for x in video if x['variant']=='HIST'),baseline_formal_success=sum(x['inference_success']for x in video if x['variant']=='BASELINE'),commit_at_export=head()))

def render_groups(wait=False):
 from .visualize import geometry,render_run,index
 for group in GROUPS:
  cases=[group+'_'+v for v in ['004','005']]
  while not all((B/'evaluation/HIST'/c/'COMPLETE.json').exists()for c in cases):
   if not wait:raise RuntimeError('Group incomplete '+group)
   if (B/'full_controller.log').exists()and 'FULL_CONTROLLER_DONE'in(B/'full_controller.log').read_text():raise RuntimeError('Full controller ended with missing case '+group)
   time.sleep(5)
  outs=[B/'evaluation'/v/c for v in ['BASELINE','HIST','GRAPH']for c in cases if(B/'evaluation'/v/c/'COMPLETE.json').exists()]
  cad=np.load(W/'runs/m2f5_unified/cad'/('R5.npz'if '_R5_'in group else'R10.npz'));bounds=[cad['V']]
  for o in outs:bounds.extend(v[0]for v in geometry(read(o/'RESULTS.json')).values())
  bounds=np.concatenate(bounds)
  for o in outs:render_run(o,bounds);index()
  print('GROUP_VISUALS_COMPLETE',group,flush=True)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');p.add_argument('--wait',action='store_true');p.add_argument('--export',action='store_true');a=p.parse_args()
 if a.render:render_groups(a.wait)
 if a.export:export()
