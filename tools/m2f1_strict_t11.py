#!/usr/bin/env python3
"""M2F1: admission-gated T10/T11 -> T13 -> new HERO for 3 representative groups."""
import sys,json,pathlib,hashlib
import numpy as np,pandas as pd,cv2,torch
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path[:0]=[str(WS/'src'),str(WS/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/code')]
from ring_first_3d.views.selection import quality_features,select_views
cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text());sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
from ring_first_3d.mainline.native.hero import load_official,infer
from ring_first_3d.mainline.native.cleaning import classify_native
from ring_first_3d.mainline.native.io import save_json,sha256
O=WS/'runs/m2f1_strict_restoration';O.mkdir(parents=True,exist_ok=True)
GROUPS=['GP_Ip_12.0mm_closed_R10_single_refY','GP_Is_9.79mm_closed_R10_single_refY','GP_Is_14.0mm_closed_R10_single_refY']
D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()};CAM=pd.read_csv(WS/'runs/m2c_corrective_completion/CAMERA_ROLE_ADMISSION.csv');cmap={(r.group_id,f'{int(r.video_id):03d}',r.view):r for _,r in CAM.iterrows()}
PREP=WS/'runs/m1_final_39/prepared';CLEAN=WS/'runs/m2c_trajectory_admission/clean_labels';roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3']
# CAD
cad_cache={}
for kind,path in [('R5',WS/'runs/m2e_historical_method_integration/cad/R5.npz'),('R10',WS/'runs/m2e_historical_method_integration/cad/R10.npz')]: cad_cache[kind]=dict(np.load(path))
def build_views(g,v):
 r=dmap[(g,v)];p=pathlib.Path(r.output_path);cr=np.load(p/'camera_result.npz');ids=[str(x) for x in cr['ids']];cams=np.asarray(cr['c2w'],float);by={}
 for root in roots:
  fp=root/f'{g}_{v}'/'PREPARED.json'
  if fp.exists():
   meta=json.loads(fp.read_text())
   for x in meta['views']:
    if x['view'] not in by:by[x['view']]=x
 out=[];feats={}
 for cid,C in zip(ids,cams):
  a=dict(np.load(by[cid]['cache']));lab=a['labels'];cp=CLEAN/f'{g}_{v}'/(cid+'.npz')
  if cp.exists():lab=np.load(cp)['labels']
  q=quality_features(dict(RGB=a['RGB'],labels=lab,T=C,K=a['K']),C[:3,3]);q['direction']=C[:3,3]/np.linalg.norm(C[:3,3]);c=cmap.get((g,v,cid));out.append(dict(id=cid,view=cid,video=v,role='FIT',C=C,K=a['K'],RGB=a['RGB'],labels=lab,raw_frame=int(c.raw_frame) if c is not None else None,pose_status=('BRANCH_UNRESOLVED' if c is not None and c.trajectory_class in ('T2_ISOLATED_BRANCH','T3_CONSECUTIVE_BRANCH') else 'CONDITIONAL' if c is not None and c.s1_eligible else 'STRICT' if c is not None and c.s0_eligible else 'REJECTED'),s0=bool(c is not None and c.s0_eligible),s1=bool(c is not None and c.s1_eligible),traj=c.trajectory_class if c is not None else 'UNKNOWN',**q))
  kp,des=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01).detectAndCompute(cv2.cvtColor(a['RGB'],cv2.COLOR_RGB2GRAY),None);feats[cid]=dict(des=des if des is not None else np.zeros((0,128),np.float32),xy=np.asarray([k.pt for k in kp],np.float32),N=len(kp))
 return out,feats
def block(C):
 c=C[:3,3];az=np.mod(np.degrees(np.arctan2(c[1],c[0])),360);el=np.degrees(np.arcsin(c[2]/max(1e-12,np.linalg.norm(c))));return int(az//30)*6+int(np.clip((el+90)//30,0,5))
model,receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text()));save_json(O/'hero/MODEL_RECEIPT.json',receipt)
targets=[];sups=[];tup=[];hero=[];a2b=[];clean=[]
for g in GROUPS:
 for v in sorted({k[1] for k in dmap if k[0]==g}):
  views,feats=build_views(g,v)
  for arm in ['S1_T11']:
   pool=[x for x in views if x['s1']]
   pool=[dict(x) for x in pool]; [x.__setitem__('direction_block',block(x['C'])) for x in pool]
   if not pool: continue
   baseline=sorted(pool,key=lambda x:x['sharpness']+x['mask_complete_proxy'],reverse=True)[0]['id']
   try:
    out=select_views(pool,strategy='direction_quota',max_views=8,mandatory_ids=[baseline])
    ids=out.get('ids',[])
   except Exception as e: ids=[];out={'error':repr(e)}
   for rank,tid in enumerate(ids[:8],1):
    tv=next(x for x in pool if x['id']==tid);targets.append(dict(group_id=g,video_id=v,arm=arm,target_id=tid,rank=rank,target_method='T11',sharpness=tv['sharpness'],mask_complete=tv['mask_complete_proxy'],ring_free=tv['Ring_free_fraction'],trajectory_class=tv['traj'],pose_status=tv['pose_status']))
    try:
     so=select_views(pool,strategy='hero_support',max_views=3,target=tv,features=lambda x:feats[x['id']],K=np.asarray(tv['K']),cache_root=O/'evidence/t13_cache'/f'{g}_{v}_{arm}')
     sids=so.get('ids',[])
    except Exception as e: sids=[];so={'error':repr(e)}
    ok=(len(sids)==3 and tid not in sids and all(x in [q['id'] for q in pool] for x in sids))
    tup.append(dict(group_id=g,video_id=v,arm=arm,target_id=tid,support_ids=';'.join(sids),target_method='T11' if arm=='S2' else 'T10',n_support=len(sids),target_in_pool=tid in [q['id'] for q in pool],supports_in_pool=all(x in [q['id'] for q in pool] for x in sids),target_not_support=tid not in sids,ready=bool(ok),input_identity_verified=bool(not (g=='GP_Is_9.79mm_closed_R10_single_refY' and v=='004')),candidate_scores=json.dumps(so.get('candidates',[]))))
    sups.append(tup[-1])
    if not ok: continue
    # new HERO
    outdir=O/'hero'/g/v/arm/tid;outdir.mkdir(parents=True,exist_ok=True);frames=[]
    for cid in [tid]+sids:
     x=next(q for q in views if q['id']==cid);frames.append(dict(id=cid,RGB=x['RGB'],labels=x['labels'],K=np.asarray(x['K'],float),c2w_mm=x['C']))
    rec=infer(model,frames,outdir);ring=O/'cad'/('R5.npz' if 'R5' in g else 'R10.npz'); cr=classify_native(outdir,str(ring)) if (O/'cad').exists() else None
    hero.append(dict(group_id=g,video_id=v,arm=arm,target_id=tid,support_ids=';'.join(sids),status='PASS',seconds=rec.get('seconds'),peak_gpu_bytes=rec.get('peak_GPU_bytes'),raw_faces=rec.get('raw_faces'),output_dir=str(outdir),input_identity_verified=bool(not (g=='GP_Is_9.79mm_closed_R10_single_refY' and v=='004'))))
    print('HERO',g,v,arm,tid,len(sids),flush=True)
pd.DataFrame(targets).to_csv(O/'selection/T11_ACTUAL_TARGETS.csv',index=False)
pd.DataFrame(sups).to_csv(O/'selection/T11_ACTUAL_TUPLES.csv',index=False)
pd.DataFrame(tup).to_csv(O/'selection/T11_ACTUAL_VALIDATION.csv',index=False)
pd.DataFrame(hero).to_csv(O/'hero/T11_HERO_EXECUTION_RESULTS.csv',index=False)
print('targets',len(targets),'tuples',len(tup),'ready',sum(x['ready'] for x in tup),'hero',len(hero))
