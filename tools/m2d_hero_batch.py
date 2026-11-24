#!/usr/bin/env python3
"""M2D: real HERO batch over validated unique tuples + immediate A-to-B metrics."""
import json,os,sys,time,pathlib,hashlib,traceback
import numpy as np,pandas as pd,torch
WS=pathlib.Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2d_w0_mvs_validation'; H=OUT/'hero'; H.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(WS/'src'),str(WS/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/code')]
cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text()); sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
from ring_first_3d.mainline.native.hero import load_official,infer
from ring_first_3d.mainline.native.io import save_json,sha256
D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv'); dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
PREP=WS/'runs/m1_final_39/prepared'; CLEAN=WS/'runs/m2c_trajectory_admission/clean_labels'; TUP=pd.read_csv(OUT/'admission/TUPLE_VALIDATION.csv')
# stable tuple id
TUP['tuple_id']=[hashlib.sha256(f"{r.group_id}|{r.video_id}|{r.target_view}|{r.support_views}".encode()).hexdigest()[:12] for _,r in TUP.iterrows()]
TUP.to_csv(OUT/'admission/TUPLE_VALIDATION.csv',index=False)
def load_frames(g,v,target,supports):
 r=dmap[(g,v)]; p=pathlib.Path(r.output_path); cr=np.load(p/'camera_result.npz'); ids=[str(x) for x in cr['ids']]; cams=np.asarray(cr['c2w'],float)
 # Search all prepared roots (M1, bridge, C3, C3B) for the actual view.
 roots=[PREP,WS/'runs/m2a_w0_recovery/prepared_c2b',WS/'runs/m2a_w0_recovery/prepared_c2',WS/'runs/m2a_w0_recovery/prepared_b1r',WS/'runs/m2a_w0_recovery/prepared_c3',WS/'runs/m2a_w0_recovery/prepared_c3b',WS/'runs/m2c_trajectory_admission/A_correctness/prepared_c3',WS/'runs/m1_final_39/prepared']
 by={}
 for root in roots:
  fp=root/f'{g}_{v}'/'PREPARED.json'
  if fp.exists():
   for x in json.loads(fp.read_text())['views']: by[x['view']]=x
 frames=[]
 for cid in [target]+supports:
  q=by[cid]; a=np.load(q['cache']); lab=a['labels']
  cp=CLEAN/f'{g}_{v}'/(cid+'.npz')
  if cp.exists(): lab=np.load(cp)['labels']
  frames.append(dict(id=cid,RGB=a['RGB'],labels=lab,K=np.asarray(a['K'],float),c2w_mm=cams[ids.index(cid)]))
 return frames,cams,ids
def project_metrics(V,cA,cB,KB,imgB,labelsB,imgA,uvA):
 zB=(V-cB[:3,3])@cB[:3,:3]; good=zB[:,2]>0; uv=np.full((len(V),2),np.nan); uv[good]=(zB[good,:2]/zB[good,2:3])@KB[:2,:2].T+KB[:2,2]
 h,w=labelsB.shape; inside=good&(uv[:,0]>=0)&(uv[:,0]<w)&(uv[:,1]>=0)&(uv[:,1]<h)
 pix=np.rint(uv[inside]).astype(int); pix[:,0]=np.clip(pix[:,0],0,w-1); pix[:,1]=np.clip(pix[:,1],0,h-1); uniq=len(set(map(tuple,pix))) if len(pix) else 0
 # target mesh uv is native 352x640; use nearest source RGB color
 uA=np.clip(uvA[:,0],0,639); vA=np.clip(uvA[:,1],0,351); a_pix=imgA[np.rint(vA*359/351).astype(int),np.rint(uA).astype(int)]
 b_pix=imgB[pix[:,1],pix[:,0]] if len(pix) else np.zeros((0,3),np.uint8)
 col=float(np.median(np.abs(a_pix[inside].astype(float)-b_pix.astype(float)))) if len(b_pix) else None
 poly=float((labelsB[pix[:,1],pix[:,0]]==1).mean()) if len(pix) else None
 return dict(projected_vertices=int(inside.sum()),coverage_fraction=float(inside.mean()),unique_target_pixels=uniq,inside_polyp_fraction=poly,color_median_abs=col,positive_depth_fraction=float(good.mean()))
# model once
print('LOADING HERO',flush=True); model,receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text())); save_json(H/'MODEL_RECEIPT.json',receipt)
rows=[]; metrics=[]; pairs=[]; visdir=OUT/'visualization/all_group_mvs_contact_sheets'; visdir.mkdir(parents=True,exist_ok=True)
for n,(_,t) in enumerate(TUP.iterrows(),1):
 g,v,target=str(t.group_id),f'{int(t.video_id):03d}',str(t.target_view); sup=str(t.support_views).split(';'); out=H/g/v/t.tuple_id
 if (out/'HERO_native.npz').exists():
  status='REUSED'; rec=json.loads((out/'INFERENCE.json').read_text()) if (out/'INFERENCE.json').exists() else {}
 else:
  try:
   frames,cams,ids=load_frames(g,v,target,sup); out.mkdir(parents=True,exist_ok=True); rec=infer(model,frames,out); status='PASS'
   raw=dict(np.load(out/'RAW_NATIVE_MESH.npz')); np.savez_compressed(out/'CLEANED_NATIVE_MESH.npz',V=raw['V'],F=raw['F'],uv=raw['uv'],native_pixel_id=raw['native_pixel_id'],cleaning='identity_no_points_removed',retention=1.0)
   save_json(out/'INPUT_MANIFEST.json',dict(group=g,video=v,target=target,supports=sup,ids=[target]+sup,rgb_hashes=[hashlib.sha256(np.load(PREP/f'{g}_{v}'/'x').tobytes()).hexdigest() if False else None for _ in [0]],camera_source=str(dmap[(g,v)].output_path),checkpoint=cfg['checkpoint'],checkpoint_sha256=sha256(cfg['checkpoint'])))
  except Exception as e:
   status='FAIL'; (out).mkdir(parents=True,exist_ok=True); save_json(out/'FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc())); rec={}
 print(n, '/',len(TUP),g,v,target,status,flush=True)
 rows.append(dict(tuple_id=t.tuple_id,group_id=g,video_id=v,arm=t.arms,target_view=target,support_views=str(t.support_views),status=status,inference_seconds=rec.get('seconds'),peak_gpu_bytes=rec.get('peak_GPU_bytes'),raw_faces=rec.get('raw_faces'),output_dir=str(out)))
 if status in ('PASS','REUSED'):
  d=np.load(out/'HERO_native.npz')['depth_mm']; valid=np.isfinite(d)&(d>0); nat=np.load(out/'NATIVE_RGB_LABELS.npz'); labels=nat['labels']; poly=labels==1
  metrics.append(dict(tuple_id=t.tuple_id,group_id=g,video_id=v,arm=t.arms,target_view=target,depth_valid_fraction=float(valid.mean()),polyp_depth_coverage=float((valid&poly).sum()/max(1,poly.sum())),raw_faces=rec.get('raw_faces'),cleaned_retention=1.0))
  frames,cams,ids=load_frames(g,v,target,sup); V=np.asarray(np.load(out/'RAW_NATIVE_MESH.npz')['V']); uv=np.asarray(np.load(out/'RAW_NATIVE_MESH.npz')['uv']); target_img=frames[0]['RGB']
  for j,s in enumerate(sup):
   sb=frames[j+1]; m=project_metrics(V,cams[ids.index(target)],cams[ids.index(s)],np.asarray(sb['K'],float),sb['RGB'],sb['labels'],target_img,uv)
   metrics[-1][f'A2B_{j}_coverage']=m['coverage_fraction']; metrics[-1][f'A2B_{j}_inside_polyp']=m['inside_polyp_fraction']; metrics[-1][f'A2B_{j}_color']=m['color_median_abs']
   pairs.append(dict(tuple_id=t.tuple_id,group_id=g,video_id=v,source_A=target,target_B=s,arm=t.arms,**m))
  # simple 2x2 visualization
  import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
  fig,ax=plt.subplots(1,3,figsize=(12,3)); ax[0].imshow(frames[0]['RGB']); ax[0].set_title('target RGB'); ax[0].axis('off'); im=ax[1].imshow(d,cmap='turbo'); ax[1].set_title('HERO depth mm'); ax[1].axis('off'); ax[2].imshow(frames[0]['RGB']); ax[2].set_title('target + support IDs'); ax[2].axis('off'); fig.suptitle(f'{g}/{v} {target} supports {",".join(sup)}'); fig.tight_layout(); fig.savefig(visdir/f'{g}_{v}_{t.tuple_id}.png',dpi=90); plt.close(fig)
pd.DataFrame(rows).to_csv(H/'HERO_EXECUTION_RESULTS.csv',index=False)
pd.DataFrame(metrics).to_csv(H/'HERO_SURFACE_METRICS.csv',index=False)
pd.DataFrame(pairs).to_csv(OUT/'a_to_b/A_TO_B_METRICS.csv',index=False)
save_json(H/'HERO_ASSET_MANIFEST.json',dict(rows=rows,metrics_rows=len(metrics),pair_rows=len(pairs),model_receipt='MODEL_RECEIPT.json'))
print('DONE',len(rows),len(metrics),len(pairs))
