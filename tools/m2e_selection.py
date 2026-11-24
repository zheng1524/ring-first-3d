#!/usr/bin/env python3
"""M2E: FRAME_REGISTRY + T10/T11 target selection + T13 real support selection."""
import sys,json,pathlib,hashlib
import numpy as np,pandas as pd,cv2
from pathlib import Path
WS=Path('/home/liu/ring_first_3d_workspace');sys.path.insert(0,str(WS/'src'))
from ring_first_3d.views.selection import quality_features,select_views
O=WS/'runs/m2e_historical_method_integration'; O.mkdir(parents=True,exist_ok=True)
D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv'); CAM=pd.read_csv(WS/'runs/m2c_corrective_completion/CAMERA_ROLE_ADMISSION.csv'); cmap={(r.group_id,f'{int(r.video_id):03d}',r.view):r for _,r in CAM.iterrows()}
PREP=WS/'runs/m1_final_39/prepared'; CLEAN=WS/'runs/m2c_trajectory_admission/clean_labels'
roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
def views_for(g,v,row):
 p=Path(row.output_path);cr=np.load(p/'camera_result.npz');ids=[str(x) for x in cr['ids']];cams=np.asarray(cr['c2w'],float);by={}
 for root in roots:
  fp=root/f'{g}_{v}'/'PREPARED.json'
  if fp.exists():
   for x in json.loads(fp.read_text())['views']:
    if x['view'] not in by: by[x['view']]=x
 out=[];feats={}
 for cid,C in zip(ids,cams):
  if cid not in by: continue
  a=dict(np.load(by[cid]['cache']));lab=a['labels'];cp=CLEAN/f'{g}_{v}'/(cid+'.npz')
  if cp.exists():lab=np.load(cp)['labels']
  q=quality_features(dict(RGB=a['RGB'],labels=lab,T=C,K=a['K']),C[:3,3]);q['direction']=C[:3,3]/np.linalg.norm(C[:3,3])
  out.append(dict(id=cid,view=cid,video=v,role='FIT',C=C,raw_frame=int(cmap[(g,v,cid)].raw_frame),K=a['K'],RGB=a['RGB'],labels=lab,**q))
  kp,des=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01).detectAndCompute(cv2.cvtColor(a['RGB'],cv2.COLOR_RGB2GRAY),None)
  feats[cid]=dict(des=des,xy=np.asarray([k.pt for k in kp],np.float32),N=len(kp)) if des is not None and len(kp)>=12 else dict(des=np.zeros((0,128),np.float32),xy=np.zeros((0,2),np.float32),N=0)
 return out,feats
def feat(v): return feats_all[v['id']]
def block(C):
 c=C[:3,3];az=np.mod(np.degrees(np.arctan2(c[1],c[0])),360);el=np.degrees(np.arcsin(c[2]/max(1e-12,np.linalg.norm(c))));return int(az//30)*6+int(np.clip((el+90)//30,0,5))
frame_rows=[];targets=[];supports=[];cands=[];t11=[]
for n,(_,r) in enumerate(D.iterrows(),1):
 g,v=str(r.group_id),f'{int(r.video_id):03d}'
 views,feats_all=views_for(g,v,r)
 if not views: continue
 # FRAME_REGISTRY
 for x in views:
  c=cmap.get((g,v,x['id'])); ps='VERIFIED_POSE' if (c is not None and c.s0_eligible) else 'CONDITIONAL_POSE' if (c is not None and c.s1_eligible) else 'INSUFFICIENT_EVIDENCE'
  if c is not None and c.trajectory_class in ('T2_ISOLATED_BRANCH','T3_CONSECUTIVE_BRANCH'): ps='BRANCH_UNRESOLVED'
  frame_rows.append(dict(group_id=g,video_id=v,view_id=x['id'],raw_frame=x['raw_frame'],RGB_hash=hashlib.sha256(x['RGB'].tobytes()).hexdigest(),raw_mask_hash=hashlib.sha256(x['labels'].tobytes()).hexdigest(),clean_mask_hash=hashlib.sha256(x['labels'].tobytes()).hexdigest(),K=json.dumps(np.asarray(x['K']).tolist()),c2w=json.dumps(np.asarray(x['C']).tolist()),camera_version='A1_M2C',prepared_source='M1/M2A/M2C view cache',pose_status=ps,trajectory_segment_id=c.trajectory_class if c is not None else 'UNKNOWN',source_video_hash='NOT_AVAILABLE_LOCAL'))
 # T10
 baseline=sorted(views,key=lambda x:(x['sharpness']+x['mask_complete_proxy']),reverse=True)[0]['id']
 try: t10=select_views(views,strategy='quality_diversity',max_views=8,baseline_ids=[baseline])
 except Exception as e: t10={'ids':[],'error':repr(e)}
 # T11
 for x in views: x['direction_block']=block(x['C'])
 try: t11o=select_views(views,strategy='direction_quota',max_views=8,mandatory_ids=[baseline],direction_block=True)
 except Exception as e: t11o={'ids':[],'error':repr(e)}
 t11.append(dict(group_id=g,video_id=v,T10_ids=';'.join(t10.get('ids',[])),T11_ids=';'.join(t11o.get('ids',[])),T11_status='PASS' if t11o.get('ids') else 'FAIL',T11_error=t11o.get('error','')))
 for rank,tid in enumerate(t10.get('ids',[])[:8],1):
  tv=next(x for x in views if x['id']==tid); targets.append(dict(group_id=g,video_id=v,target_id=tid,rank=rank,strategy='quality_diversity',direction=tv['direction'].tolist(),sharpness=tv['sharpness'],mask_complete=tv['mask_complete_proxy'],thin=tv['thin_structure_visibility_proxy'],ring_free=tv['Ring_free_fraction'],role='HERO_TARGET'))
  if rank>4: continue
  try:
   root=O/'evidence/t13_cache'/f'{g}_{v}';out=select_views(views,strategy='hero_support',max_views=3,target=tv,features=lambda x:feats_all[x['id']],K=np.asarray(tv['K']),cache_root=root)
   ids=out.get('ids',[]); cs=out.get('candidates',[]); status='READY' if len(ids)==3 else 'INSUFFICIENT_SUPPORTS'
   supports.append(dict(group_id=g,video_id=v,target_id=tid,selection_strategy='T13',support_ids=';'.join(ids),n_supports=len(ids),status=status,candidate_scores=json.dumps(cs)))
   for c in cs: cands.append(dict(group_id=g,video_id=v,target_id=tid,**c,selected=c['id'] in ids))
  except Exception as e:
   supports.append(dict(group_id=g,video_id=v,target_id=tid,selection_strategy='T13',support_ids='',n_supports=0,status='ERROR',candidate_scores=json.dumps(dict(error=repr(e)))))
 print(n,'/',len(D),g,v,'views',len(views),'T10',len(t10.get('ids',[])),'T13ready',sum(1 for s in supports if s['group_id']==g and s['video_id']==v and s['status']=='READY'),flush=True)
pd.DataFrame(frame_rows).to_csv(O/'camera/FRAME_REGISTRY.csv',index=False)
pd.DataFrame(targets).to_csv(O/'target/TARGET_SELECTION_RESULTS.csv',index=False)
pd.DataFrame(t11).to_csv(O/'target/T11_DIRECTION_QUOTA.csv',index=False)
pd.DataFrame(supports).to_csv(O/'support/SUPPORT_SELECTION_RESULTS.csv',index=False)
pd.DataFrame(cands).to_csv(O/'support/SUPPORT_CANDIDATES.csv',index=False)
print('FRAMES',len(frame_rows),'TARGETS',len(targets),'SUPPORT_READY',sum(s['status']=='READY' for s in supports),'SUPPORT_ROWS',len(supports))
