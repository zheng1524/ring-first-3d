"""Final artifact checks; no scientific recomputation or mutation of run outputs."""
from pathlib import Path
import json,time,shutil,csv
import numpy as np
import trimesh
from ring_first_3d.v6_raw.full_run import read,atomic_json,hash_file,table
W=Path('/home/liu/ring_first_3d_workspace');WT=Path(__file__).resolve().parents[1];TASK='TASK-V6-FRONTEND-RECOVERY-AND-PHOTO-PILOT-001';T=WT/'experiments'/TASK;O=W/'runs/v6_frontend_photo_pilot_001'
def main():
 snapshot=read(O/'SNAPSHOT.json');assert snapshot['execution_commit']=='dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e'
 for p,h in snapshot['files'].items():assert hash_file(Path(snapshot['snapshot'])/p)==h,('SNAPSHOT_DRIFT',p)
 old={x['case']:x for x in read(T/'evidence/R0_IDENTITIES.json')['videos']};old_count=0;source_count=0;tuples=0;track_rows=0;view_rows=0;clean_faces=0;receipts=[];initrows=[];pair_files=[]
 for case,x in old.items():
  for p,h in x['files'].items():assert hash_file(p)==h;old_count+=1
  for a in x['outputs']:assert hash_file(a['path'])==a['sha256'];old_count+=1
  BR=Path(x['state']['run_path']);fr=read(BR/'metrics/freeze_tracks.json')['files']
  for name in ['tracks005.npz','pairs005.npz']:
   p=BR/'observations'/name;assert hash_file(p)==fr[str(p.resolve())];pair_files.append(dict(path=str(p),sha256=hash_file(p)))
 for var in ['R1','R2']:
  clean={ (x['case'],x['tag']):x for x in read(O/var/'CLEAN_RESULTS.json')};journal=[json.loads(x) for x in (O/var/'INFERENCE_STARTS.jsonl').read_text().splitlines()];budgets=0
  for case,x in old.items():
   st=read(O/var/'states'/(case+'.json'));assert st['status']=='DONE' or st['status'].endswith('_FAILED'),(var,case,st['status']);R=Path(st['run_path']);run=read(R/'RUN_STATE.json');assert run['execution_commit']==snapshot['execution_commit'];meta=read(R/'inputs/INPUT_IDENTITY.json');assert len(meta['original_video_frames'])-1==x['original_target_count']
   info=dict(case=case,variant=var,state=st,files={str(p):hash_file(p) for p in R.glob('*.json')});receipts.append(info)
   if (R/'COMPONENT.json').exists():
    comp=read(R/'COMPONENT.json');full=read(R/'ORIGINAL_VIEW_POOL.json');keep=comp['retained_indices'];assert comp['original_reference']['reference_index'] in keep
    oldtr=np.load(Path(x['state']['run_path'])/'observations/tracks005.npz');tr=np.load(R/'observations/tracks005.npz');n=len(oldtr['held']);nv=len(oldtr['ids']);columns=[(j,k) for j,k in enumerate(keep if 'component_original_indices' in meta else range(len(full))) if k<nv]
    assert np.array_equal(tr['held'][:n],oldtr['held']) and np.array_equal(tr['category'][:n],oldtr['category'])
    for j,k in columns:assert np.array_equal(tr['xy'][:n,j],oldtr['xy'][:,k],equal_nan=True)
    for i,j in comp['temporal_edges']:assert keep[j]==keep[i]+1 and full[keep[i]]['media_type']==full[keep[j]]['media_type']=='video'
    pack=np.load(R/'observations/pairs005.npz')
    for k,(i,j) in enumerate(pack['ij']):
     for row in pack['pair'+str(k)]:assert np.array_equal(tr['xy'][int(row[0]),[i,j]].ravel(),row[1:]);track_rows+=1
    view_rows+=len(full)
   if not (R/'PLAN_FROZEN.json').exists():continue
   camreceipt=read(R/'CAMERA_COMPLETE.json')
   for p,h in camreceipt['outputs'].items():assert hash_file(p)==h
   plan=read(R/'PLAN_FROZEN.json');selection=read(R/'INITIALIZATION_SELECTION.json');gates=read(R/'metrics/GATES.json');L=read(R/'inputs/ledger005.json');held=read(R/'inputs/REFERENCE_RECEIPT.json')['heldout_index'];primary=plan['selected_version'];cam=R/f'predictions/local005_camera_{primary}.npz';assert hash_file(cam)==plan['cameras_sha256'];assert read(R/'predictions/local005_primary.json')['primary_version']==primary
   vals=read(R/'metrics/local_validation.json');evaluated={a['version']:a for a in selection['plans']}
   from ring_first_3d.v6_raw.policy import admit_camera
   for v in vals['versions']:
    checks=[admit_camera(a) for a in v['per_frame']];initrows.append(dict(case=case,variant=var,version=v['version'],numeric_cameras=len(checks),q0=sum(a[0] for a in checks),q1=sum(a[1] for a in checks),legal_tuples=evaluated.get(v['version'],{}).get('legal_tuples'),plan_status='EVALUATED' if v['version'] in evaluated else 'NOT_EVALUATED_DEFAULT_ALREADY_LEGAL',selected=v['version']==primary))
   if evaluated[selection['default_version']]['legal_tuples']>0:assert selection['selected_version']==selection['default_version']
   assert plan['budget']==len(plan['legal']);budgets+=plan['budget']
   for c in plan['legal']:
    ix=[c['reference']]+c['sources'];assert len(c['sources'])==3 and len(set(ix))==4 and held not in ix and len({L[i]['physical_view_id'] for i in ix})==4
    assert all(gates[i]['new_pass'] for i in c['sources']);di={d['i']:d for d in c['source_diagnostics']};assert all(di[i]['overlap']>=15 for i in c['sources']);tuples+=1
    for i in ix:
     for key in ['RGB','Mask']:assert hash_file(L[i][key+'_path'])==L[i][key+'_SHA256']
   if (R/'HERO_COMPLETE.json').exists():
    hero=read(R/'HERO_COMPLETE.json');assert hero['execution_commit']==snapshot['execution_commit']
    for p,h in hero['outputs'].items():assert hash_file(p)==h;source_count+=1
   out=O/var/'display'/case/'RESULTS.json'
   if out.exists():
    for row in read(out):
     if row['status']!='RENDERABLE':continue
     c=clean[(case,row['tag'])];assert c['protocol']['protocol_sha256']=='99c00fe52effa2589c21ad93c2f06a3b1c4d9c86c4c0c37b9bf5a2db33495b56';dest=O/var/'clean'/case/row['tag'];e=np.load(dest/'FACE_EVIDENCE.npz');mesh=trimesh.load(row['mesh_path'],process=False);assert np.array_equal(e['V'],mesh.vertices) and np.array_equal(e['F'],mesh.faces);faces=e['F'][e['state']==0];assert len(faces)==c['trusted_faces'];clean_faces+=len(e['F'])
     for p,h in c['retained_hashes'].items():assert hash_file(p)==h
     if len(faces):
      trust=trimesh.load(dest/'Trusted_visible_mesh.ply',process=False);assert np.array_equal(trust.vertices,mesh.vertices) and np.array_equal(trust.faces,faces)
  assert len(journal)==budgets,('inference accounting requires retry review',var,len(journal),budgets)
 atomic_json(T/'evidence/RUN_IDENTITIES.json',receipts);table(T/'INITIALIZATION_COMPARISON.csv',initrows);atomic_json(T/'evidence/BASELINE_TRACK_IDENTITIES.json',pair_files)
 comparisons=list(csv.DictReader((T/'VIDEO_COMPARISON.csv').open()));common=list(csv.DictReader((T/'COMMON_105_TARGETS.csv').open()));expected_keys=set()
 for case,x in old.items():
  R=Path(x['state']['run_path'])
  if x['state'].get('renderable'):expected_keys.update((case,str(c['raw_target'])) for c in read(R/'PLAN_FROZEN.json')['legal'])
 assert len(expected_keys)==105
 for var in ['R0','R1','R2']:
  vv=[x for x in comparisons if x['variant']==var];assert len(vv)==12 and {x['case'] for x in vv}==set(old) and sum(int(x['original_video_targets']) for x in vv)==252
  pp=list(csv.DictReader((T/('PAIRS_'+var+'.csv')).open()));got={(x['case'],x['A_raw'],x['B_raw']) for x in pp if x['pair_identity']=='R0_FIXED_TARGET_PAIR'};expected=set()
  for case in old:
   target=sorted(int(t) for c,t in expected_keys if c==case)
   expected.update((case,str(a),str(b)) for a,b in zip(target,target[1:]+target[:1]) if a!=b)
  assert got==expected,(var,'FIXED_PAIR_DENOMINATOR_DRIFT',len(got),len(expected))
  if var!='R0':
   cc=[x for x in common if x['variant']==var];assert len(cc)==105 and {(x['case'],x['target']) for x in cc}==expected_keys and all(x['new_status']!='PENDING' for x in cc)
 result=dict(status='PASS',execution_commit=snapshot['execution_commit'],baseline_files_reverified=old_count,baseline_track_pair_files=len(pair_files),new_raw_mesh_hashes_checked=source_count,legal_tuples_checked=tuples,pair_rows_checked=track_rows,input_views_checked=view_rows,classified_original_faces_checked=clean_faces,original_video_denominator=252,post_evaluation_no_admission_changes=True,df=dict(zip(['total','used','free'],shutil.disk_usage(O))),epoch=time.time())
 atomic_json(T/'evidence/FINAL_ARTIFACT_AUDIT.json',result);print(result)
if __name__=='__main__':main()
