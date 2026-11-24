#!/usr/bin/env python3
"""M2F5 unified: raw video -> fresh sampling -> INIT/DXY clean -> W0 -> T10/T13 -> HERO -> Raw Mesh -> A-to-B."""
import argparse, hashlib, json, subprocess, sys, time
from pathlib import Path
import cv2, numpy as np, pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path[:0] = [str(WS/'src'), str(WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/code'),
                str(WS/'src/ring_first_3d/mainline/frozen_registry'),
                str(WS/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code')]
from prepare import prepare_view
from ring_first_3d.views.selection import quality_features, select_views
from ring_first_3d.views.pipeline_adapter import admission_tiers, direction_blocks, validate_t13
from ring_first_3d.mainline.input_identity import verify_w0_packet
from ring_first_3d.mainline.native.hero import load_official, infer
from ring_first_3d.mainline.native.geometry import native_rgb_labels
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
import reprojection as rp
import open3d as o3d

GROUPS = [
 'GP_Ip_12.0mm_closed_R10_single_refY','GP_Ip_20.0mm_closed_R10_single_refY','GP_IIa_14.0mm_closed_R10_single_refY',
 'GP_IIa_5.2mm_closed_R10_single_refY','GP_IIa_9.5mm_closed_R5_single_refY','GP_IIa_22.0mm_closed_R5_single_refY',
 'GP_Ip_4.0mm_closed_R5_single_refY','GP_Ip_6.2mm_closed_R10_single_refY','GP_Ip_8.8mm_closed_R5_single_refY',
 'GP_Ip_12.0mm_closed_R5_single_refY','GP_Is_10.5mm_closed_R10_single_refY','GP_Is_14.0mm_closed_R5_single_refY',
 'GP_Is_18.0mm_closed_R5_single_refY']
RAW = WS/'smart_endoscope_20260805 (1)'/'raw'; INIT = Path('/home/liu/polyp_research/experiments/dxy_remeasurement_20260917/02_segmentation/model/model.safetensors')
INIT_SHA='981aa596e8906edc4457219581c606d4a5a22bfc6f7e4924d3d9a4b9aff64464'; K=np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1.]])
O = WS/'runs/m2f5_unified'; PY = json.loads((WS/'mainline/configs/SITE.local.json').read_text())['python']

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=1,sort_keys=True,default=str)+'\n')
def trace(g,v,stage,route,entry,inputs,outputs,status,extra=None):
 p=O/'RUN_TRACE'/f'{g}_{v}.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
 rec=dict(run_id='M2F5-UNIFIED-001',group_id=g,video_id=v,stage=stage,route_id=route,route_version='1',entrypoint=entry,inputs=inputs,outputs=outputs,status=status,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WS,text=True).strip(),config_hash=hashlib.sha256((WS/'mainline/configs/SITE.local.json').read_bytes()).hexdigest());
 if extra:rec.update(extra)
 with p.open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')

def video_paths(g):
 return sorted(RAW.glob(f'{g}_*.mp4'))
def ring_mm(g): return 5.0 if '_R5_' in g else 10.0

def sample_frames(path):
 cap=cv2.VideoCapture(str(path));n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));cap.release()
 if n<20: raise ValueError('VIDEO_TOO_SHORT')
 base=sorted(set(int(x) for x in np.linspace(20,n-21,12)))
 # real midpoints of four largest gaps, same recovery rule as M2F3 G06
 gaps=sorted([(base[i+1]-base[i],base[i],base[i+1]) for i in range(len(base)-1)],reverse=True)[:4]
 extra=[(a+b)//2 for _,a,b in gaps if (a+b)//2 not in base]
 return sorted(set(base+extra))

def prepare(g,v):
 vp=video_paths(g)[0] if False else None
 # path selected by caller
def prepare_one(g,path):
 vid=path.stem.split('_')[-1]; root=O/'prepared'/f'{g}_{vid}'; root.mkdir(parents=True,exist_ok=True); frames=sample_frames(path); views=[]
 for idx in frames:
  cache=root/f'{g}_{vid}-raw{idx:05d}.npz'; r=prepare_view(path,idx,cache); a=np.load(cache)
  if a['labels'].shape!=(360,640): raise ValueError('MASK_SHAPE')
  views.append(dict(view=cache.stem,raw_frame=int(idx),cache=str(cache),rgb_sha256=r.get('rgb_sha256'),label_counts=r.get('label_counts')))
 meta=dict(group=g,video_id=vid,video=path.name,video_path=str(path),video_sha256=h(path),init_weights=str(INIT),init_weight_sha256=INIT_SHA,math='PIL bilinear 256 /255; bilinear logits upsample; argmax',ring_mm=ring_mm(g),K=K.tolist(),views=views,source='M2F5_REAL_RAW_FRAMES')
 write_json(root/'PREPARED.json',meta); trace(g,vid,'prepare','rf-m2f5-input-fresh','prepare_m1_inputs.py::prepare_view',[str(path)],[str(root/'PREPARED.json')],'PASS',{'frames':len(views),'sample_rule':'12_uniform_plus_4_largest_gap_midpoints'})
 # DXY clean all frames
 import importlib.util
 sp=importlib.util.spec_from_file_location('dxy_ring_holes', '/home/liu/new-polyp-dxy/src/dxy_mid/_engine/ring_holes.py'); mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
 croot=O/'clean_labels'/f'{g}_{vid}';croot.mkdir(parents=True,exist_ok=True);cleanrows=[]
 for q in views:
  a=np.load(q['cache']);raw=a['labels'];clean,fill,info=mod.run(raw);assert np.array_equal(clean==1,raw==1);np.savez_compressed(croot/(q['view']+'.npz'),labels=clean)
  cleanrows.append(dict(group_id=g,video_id=vid,view_id=q['view'],raw_frame=q['raw_frame'],raw_ring=int((raw==2).sum()),clean_ring=int((clean==2).sum()),changed=int((clean!=raw).sum()),filled=int(fill.sum()),clean_sha=h(croot/(q['view']+'.npz')),rule=info.get('rule',{}).get('version','')))
 pd.DataFrame(cleanrows).to_csv(O/'w0'/f'MASK_CLEAN_{g}_{vid}.csv',index=False);trace(g,vid,'mask_clean','rf-dxy-ring-clean','tools/m2c_prepare_clean.py::dxy_ring_holes.run',[q['cache'] for q in views],[str(croot)],'PASS',{'frames':len(cleanrows),'changed':int(sum(x['changed']>0 for x in cleanrows))})
 return root,croot,meta

def run_w0(g,vid,root,croot):
 out=O/'w0'/f'{g}_{vid}';log=O/'logs'/f'w0_{g}_{vid}.log';log.parent.mkdir(parents=True,exist_ok=True);meta=json.loads((root/'PREPARED.json').read_text());n=len(meta['views']);off=','.join(map(str,range(1,n)))
 cmd=[PY,str(WS/'tools/run_w0_camera.py'),'--group',g,'--video',vid,'--stage','all','--output',str(out),'--workdir',str(O/'work'/f'{g}_{vid}'),'--prepared-root',str(O/'prepared'),'--clean-labels-root',str(O/'clean_labels'),'--ring-mode','all','--pair-offsets',off]
 with log.open('w') as f:r=subprocess.run(cmd,cwd=WS,stdout=f,stderr=subprocess.STDOUT)
 trace(g,vid,'w0','rf-w0-camera@2','tools/run_w0_camera.py',[str(root/'PREPARED.json'),str(croot)],[str(out)],'PASS' if r.returncode==0 else 'FAIL',{'returncode':r.returncode,'frames':n})
 return out if r.returncode==0 else None

def graph_counts(packet):
 p=Path(packet['manifest']['tracks']['path']).with_name('pairs005.npz');d=np.load(p);ids=list(packet['views']);c={x:set() for x in ids}
 for k,(i,j) in enumerate(d['ij']):
  if len(d[f'pair{k}'])>=12:c[ids[int(i)]].add(ids[int(j)]);c[ids[int(j)]].add(ids[int(i)])
 return {x:len(y) for x,y in c.items()}

def build_views(packet):
 adm=pd.read_csv(Path(packet['w0_path']).parent/'admission.csv').set_index('view');center=np.asarray(packet['points'],float).mean(axis=0);poses=list(packet['cameras'].values());blocks=direction_blocks(poses,center);graph=graph_counts(packet);views=[]
 for i,(vid,e) in enumerate(packet['views'].items()):
  with np.load(e['cache']) as z:RGB=z['RGB'];Kv=z['K'];raw=z['labels']
  cp=O/'clean_labels'/f"{packet['group']}_{packet['video']}"/f'{vid}.npz';labels=np.load(cp)['labels']
  C=packet['cameras'][vid];q=quality_features(dict(RGB=RGB,labels=labels,T=C,K=Kv),center);row=adm.loc[vid].to_dict();s0,s1,s2=admission_tiers(row,graph[vid],'CURRENT_RUN')
  views.append(dict(id=vid,view=vid,video=packet['video'],role='FIT',C=C,K=Kv,RGB=RGB,labels=labels,raw_frame=int(e['raw_frame']),direction_block=blocks[i],s2=s2,graph_support_count=graph[vid],legacy_status=row['admission_status'],**q))
 return views,center

def select(g,vid,packet):
 views,center=build_views(packet);pool=[v for v in views if v['s2']]
 if len(pool)<4:return [],center,len(pool)
 def central(v):
  d=np.asarray(v['direction']);return float(np.median(np.degrees(np.arccos(np.clip(np.asarray([x['direction'] for x in pool])@d,-1,1)))))
 anchor=min(pool,key=central);res=select_views(pool,strategy='quality_diversity',max_views=min(8,len(pool)),baseline_ids=[anchor['id']]);rows=[]
 feats={};sift=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01)
 for v in pool:
  kp,d=sift.detectAndCompute(cv2.cvtColor(v['RGB'],cv2.COLOR_RGB2GRAY),None);feats[v['id']]=dict(des=d if d is not None else np.zeros((0,128),np.float32),xy=np.asarray([x.pt for x in kp],np.float32),N=len(kp))
 for rank,tid in enumerate(res['ids'],1):
  target=next(v for v in pool if v['id']==tid)
  try:r=select_views(pool,strategy='hero_support',max_views=3,target=target,features=lambda v:feats[v['id']],K=target['K'],cache_root=O/'cache'/f'{g}_{vid}/{tid}')
  except Exception as e:r={'ids':[],'candidates':[]}
  sids=r.get('ids',[]);sups=[v for v in pool if v['id'] in sids];ok=len(sids)==3 and target['id'] not in sids
  if ok:ok,reason=validate_t13(target,sups,r.get('candidates',[]))
  else:reason='TUPLE_MEMBERSHIP'
  if ok:ok=all(x['s2'] for x in sups)
  rows.append(dict(group_id=g,video_id=vid,arm='LOCAL',method='T10',target_id=tid,support_ids=';'.join(sids),n_support=len(sids),ready=bool(ok),reason=reason,anchor_id=anchor['id'],candidate_scores=json.dumps(r.get('candidates',[]))))
 trace(g,vid,'select','rf-m2f5-t10+t13','selection.py::select_views',[str(packet['w0_path'])],[str(O/'selection'/'FINAL_HERO_TUPLES.csv')],'PASS',{'pool':len(pool),'targets':len(res['ids']),'ready':sum(x['ready'] for x in rows)})
 return rows,center,len(pool)

def tuple_frames(packet,target,supports):
 out=[]
 for vid in [target]+supports:
  e=packet['views'][vid];z=np.load(e['cache']);cp=O/'clean_labels'/f"{packet['group']}_{packet['video']}"/f'{vid}.npz';out.append(dict(id=vid,RGB=z['RGB'],labels=np.load(cp)['labels'],K=np.asarray(z['K'],float),c2w_mm=packet['cameras'][vid]))
 return out

def run_hero(g,vid,packet,row,model):
 out=O/'hero'/f'{g}_{vid}'/row['target_id'];out.mkdir(parents=True,exist_ok=True);rec=infer(model,tuple_frames(packet,row['target_id'],row['support_ids'].split(';')),out)
 return dict(group_id=g,video_id=vid,target_id=row['target_id'],support_ids=row['support_ids'],status='PASS',output_dir=str(out),seconds=rec.get('seconds'),raw_faces=rec.get('raw_faces'),tuple_sha=hashlib.sha256((g+'|'+vid+'|'+row['target_id']+'|'+row['support_ids']).encode()).hexdigest()[:16])

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['prepare','w0','all'],default='all');ap.add_argument('--groups',default=','.join(GROUPS));ap.add_argument('--limit',type=int,default=0);a=ap.parse_args();groups=[x for x in a.groups.split(',') if x]
 for g in groups:
  for path in video_paths(g):
   vid=path.stem.split('_')[-1]
   if a.stage in ('prepare','all'): root,croot,meta=prepare_one(g,path)
   if a.stage in ('w0','all'):
    root=O/'prepared'/f'{g}_{vid}';croot=O/'clean_labels'/f'{g}_{vid}';out=run_w0(g,vid,root,croot)
    if out is None: print('W0FAIL',g,vid,flush=True);continue
    try:
     packet=verify_w0_packet(out,WS);rows,center,pool=select(g,vid,packet)
     pd.DataFrame(rows).to_csv(O/'selection'/f'{g}_{vid}.csv',index=False);print('SELECT',g,vid,'pool',pool,'ready',sum(x['ready'] for x in rows),flush=True)
    except Exception as e:
     print('SELECTFAIL',g,vid,repr(e),flush=True);continue
   if a.limit and len(list((O/'selection').glob('*.csv')))>=a.limit: break
 print('DONE')
if __name__=='__main__':main()
