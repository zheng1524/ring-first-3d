#!/usr/bin/env python3
import sys,json,pathlib,hashlib
import numpy as np,pandas as pd
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f_metric_depth_diagnosis';M=WS/'runs/m2e_historical_method_integration'
# Frame registry with distinct raw/clean mask hashes
D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()};CAM=pd.read_csv(WS/'runs/m2c_corrective_completion/CAMERA_ROLE_ADMISSION.csv');cmap={(r.group_id,f'{int(r.video_id):03d}',r.view):r for _,r in CAM.iterrows()}
PREP=WS/'runs/m1_final_39/prepared';CLEAN=WS/'runs/m2c_trajectory_admission/clean_labels';roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
rows=[]
for _,r in D.iterrows():
 g,v=str(r.group_id),f'{int(r.video_id):03d}';cr=np.load(pathlib.Path(r.output_path)/'camera_result.npz');ids=[str(x) for x in cr['ids']];cams=np.asarray(cr['c2w'],float);by={}
 for root in roots:
  p=root/f'{g}_{v}'/'PREPARED.json'
  if p.exists():
   for x in json.loads(p.read_text())['views']:
    if x['view'] not in by:by[x['view']]=x
 for cid,C in zip(ids,cams):
  a=dict(np.load(by[cid]['cache']));cp=CLEAN/f'{g}_{v}'/(cid+'.npz');labclean=np.load(cp)['labels'] if cp.exists() else a['labels'];c=cmap.get((g,v,cid));ps='VERIFIED_POSE' if c is not None and c.s0_eligible else 'CONDITIONAL_POSE' if c is not None and c.s1_eligible else 'INSUFFICIENT_EVIDENCE'
  if c is not None and c.trajectory_class in ('T2_ISOLATED_BRANCH','T3_CONSECUTIVE_BRANCH'):ps='BRANCH_UNRESOLVED'
  rows.append(dict(group_id=g,video_id=v,view_id=cid,raw_frame=int(c.raw_frame) if c is not None else None,timestamp=None,source_video_path='NOT_AVAILABLE_LOCAL',source_video_hash='NOT_AVAILABLE_LOCAL',RGB_hash=hashlib.sha256(np.asarray(a['RGB']).tobytes()).hexdigest(),raw_mask_hash=hashlib.sha256(np.asarray(a['labels']).tobytes()).hexdigest(),clean_mask_hash=hashlib.sha256(np.asarray(labclean).tobytes()).hexdigest(),K=json.dumps(np.asarray(a['K']).tolist()),c2w=json.dumps(C.tolist()),camera_version='A1_M2C',prepared_source=by[cid].get('cache',''),track_source='M2C_tracks005',trajectory_segment_id=c.trajectory_class if c is not None else 'UNKNOWN',pose_status=ps))
fr=pd.DataFrame(rows);fr.to_csv(O/'engineering/FRAME_REGISTRY.csv',index=False)
pd.DataFrame([dict(metric='rows',value=len(fr)),dict(metric='raw_clean_hash_distinct',value=int((fr.raw_mask_hash!=fr.clean_mask_hash).sum())),dict(metric='source_video_hash_missing',value=int((fr.source_video_hash=='NOT_AVAILABLE_LOCAL').sum())),dict(metric='verified_pose',value=int((fr.pose_status=='VERIFIED_POSE').sum())),dict(metric='conditional_pose',value=int((fr.pose_status=='CONDITIONAL_POSE').sum())),dict(metric='branch_unresolved',value=int((fr.pose_status=='BRANCH_UNRESOLVED').sum()))]).to_csv(O/'engineering/INPUT_IDENTITY_VALIDATION.csv',index=False)
# camera admission copy + tuple validation
c=pd.read_csv(WS/'runs/m2c_corrective_completion/CAMERA_ROLE_ADMISSION.csv');c.to_csv(O/'camera/CAMERA_ROLE_ADMISSION.csv',index=False)
import shutil;shutil.copyfile(WS/'runs/m2c_corrective_completion/TRAJECTORY_REPAIR_RESULTS.csv',O/'camera/TRAJECTORY_REPAIR_RESULTS.csv')
cmap2={(r.group_id,f'{int(r.video_id):03d}',r.view):r for _,r in c.iterrows()};e=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');s=pd.read_csv(O/'selection/T13_SUPPORT_SELECTION_M2E.csv');s['video_id']=s.video_id.astype(int).map(lambda x:f'{x:03d}');si=s.set_index(['group_id','video_id','target_id']);val=[]
for _,x in e.iterrows():
 g,v,target=str(x.group_id),f'{int(x.video_id):03d}',x.target_id;ids=str(si.loc[(g,v,target)].support_ids).split(';');te=cmap2.get((g,v,target));tok=te is not None and (te.s0_eligible or te.s1_eligible);sok=all(cmap2.get((g,v,q)) is not None and (cmap2[(g,v,q)].s0_eligible or cmap2[(g,v,q)].s1_eligible) for q in ids);val.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(ids),target_eligible=bool(tok),supports_eligible=bool(sok),three_supports=len(ids)==3,target_not_support=target not in ids,ready=bool(tok and sok and len(ids)==3 and target not in ids),source='M2E actual HERO; eligibility post-check'))
pd.DataFrame(val).to_csv(O/'selection/HERO_TUPLE_VALIDATION.csv',index=False)
# target final selection copies + explicit T11 status
shutil.copyfile(M/'target/TARGET_SELECTION_RESULTS.csv',O/'selection/T10_TARGET_SELECTION.csv');shutil.copyfile(M/'target/T11_DIRECTION_QUOTA.csv',O/'selection/T11_DIRECTION_SELECTION.csv');shutil.copyfile(M/'target/TARGET_SELECTION_RESULTS.csv',O/'selection/FINAL_TARGET_SELECTION.csv');shutil.copyfile(M/'support/SUPPORT_CANDIDATES.csv',O/'selection/T13_SUPPORT_CANDIDATES.csv')
# A2B corrected copies
shutil.copyfile(O/'evaluation/M2F_A_TO_B.csv',O/'evaluation/M2E_CORRECTED_A_TO_B.csv')
# status for not executed controlled experiments
pd.DataFrame([dict(status='NOT_EXECUTED',reason='support replacement requires new HERO runs; not completed in M2F execution window')]).to_csv(O/'depth_diagnosis/SUPPORT_SENSITIVITY.csv',index=False)
pd.DataFrame([dict(status='NOT_EXECUTED',reason='A2 camera repair not completed; no A2-vs-A1 HERO tuple')]).to_csv(O/'depth_diagnosis/CAMERA_ONLY_COMPARISON.csv',index=False)
pd.DataFrame([dict(status='NOT_EXECUTED',reason='independent B pre-freeze and B->A not completed')]).to_csv(O/'evaluation/INDEPENDENT_VIEW_METRICS.csv',index=False)
pd.DataFrame([dict(status='NOT_EVALUATED',reason='multisurface numerical consistency not computed; only visual overlay')]).to_csv(O/'evaluation/MULTISURFACE_CONSISTENCY.csv',index=False)
pd.DataFrame([dict(status='NOT_EXECUTED',reason='no verified A2 repair')]).to_csv(O/'camera/TRAJECTORY_REPAIR_RESULTS.csv',index=False) if False else None
print('frames',len(fr),'tuples',len(val),'ready',sum(x['ready'] for x in val),'rawclean',int((fr.raw_mask_hash!=fr.clean_mask_hash).sum()))
