#!/usr/bin/env python3
"""M2F5 unified: raw video -> fresh sampling -> INIT/DXY clean -> W0 -> T10/T13 -> HERO -> Raw Mesh -> A-to-B."""
import argparse, hashlib, json, subprocess, sys, time, traceback
from pathlib import Path
import cv2, numpy as np, pandas as pd

WS = Path('/home/liu/ring_first_3d_workspace')
sys.path[:0] = [str(WS), str(WS/'src'), str(WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/code'),
                str(WS/'src/ring_first_3d/mainline/frozen_registry'),
                str(WS/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code')]
from prepare import prepare_view
from ring_first_3d.views.selection import quality_features, select_views
from ring_first_3d.views.pipeline_adapter import admission_tiers, direction_blocks, validate_t13
from ring_first_3d.mainline.input_identity import verify_w0_packet
from ring_first_3d.mainline.native.hero import load_official, infer
from ring_first_3d.mainline.native.geometry import native_rgb_labels
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
from ring_first_3d.mainline.native.camera import observe
from tools.m2f6_observations import (quality_2d, appearance_2d, candidate_frames,
                                    select_observations, choose_real_supplements,
                                    bounded_recovery, render_observation_evidence,
                                    recovery_reason_from_evidence)
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
M2F6 = False

def h(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=1,sort_keys=True,default=str)+'\n')
def trace(g,v,stage,route,entry,inputs,outputs,status,extra=None):
 p=O/'RUN_TRACE'/f'{g}_{v}.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
 rec=dict(run_id='M2F6-UNIFIED-OBSERVATION-001' if M2F6 else 'M2F5-UNIFIED-001',group_id=g,video_id=v,stage=stage,route_id=route,route_version='1',entrypoint=entry,inputs=inputs,outputs=outputs,status=status,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WS,text=True).strip(),config_hash=hashlib.sha256((WS/'mainline/configs/SITE.local.json').read_bytes()).hexdigest());
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


def prepare_real_candidate(g,vid,path,idx,root,cleaner):
 """The same raw-video INIT and DXY path for initial and recovery frames."""
 cache=root/f'{g}_{vid}-raw{idx:05d}.npz';r=prepare_view(path,idx,cache)
 with np.load(cache) as a:RGB=a['RGB'];raw=a['labels'];Kv=a['K']
 if raw.shape!=(360,640):raise ValueError('MASK_SHAPE')
 clean,fill,info=cleaner.run(raw)
 if not np.array_equal(clean==1,raw==1):raise ValueError('DXY_CHANGED_POLYP_MASK')
 cp=O/'clean_labels'/f'{g}_{vid}'/(cache.stem+'.npz');cp.parent.mkdir(parents=True,exist_ok=True)
 np.savez_compressed(cp,labels=clean)
 mc=O/'observation_matches'/f'{g}_{vid}'/'clean_cache'/(cache.stem+'.npz');mc.parent.mkdir(parents=True,exist_ok=True)
 np.savez_compressed(mc,RGB=RGB,labels=clean,K=Kv)
 q=quality_2d(dict(RGB=RGB,labels=clean));proxy=appearance_2d(clean)
 count=len(observe(clean,'all')['q_train'])
 quality=float(np.log1p(q['sharpness'])+q['mask_complete_proxy']+
               q['thin_structure_visibility_proxy']+q['Ring_free_fraction'])
 array_hash=lambda value:hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()
 rec=dict(view=cache.stem,frame=int(idx),raw_frame=int(idx),cache=str(cache),clean_labels=str(cp),
          RGB_sha256=array_hash(RGB),raw_mask_sha256=array_hash(raw),clean_mask_sha256=array_hash(clean),
          K_sha256=array_hash(Kv),cache_sha256=h(cache),clean_labels_sha256=h(cp),
          ring_train_points=count,quality=quality,quality_features=q,proxy=proxy,
          dxy_rule=info.get('rule',{}).get('version',''),filled=int(fill.sum()),
          label_counts=r.get('label_counts'))
 match_view=dict(id=cache.stem,cache=str(mc),raw_frame=int(idx),K=Kv.tolist(),
                 RGB_SHA256=rec['RGB_sha256'])
 cleanrow=dict(group_id=g,video_id=vid,view_id=cache.stem,raw_frame=int(idx),
               raw_ring=int((raw==2).sum()),clean_ring=int((clean==2).sum()),
               changed=int((clean!=raw).sum()),filled=int(fill.sum()),
               clean_sha=h(cp),rule=rec['dxy_rule'])
 return rec,match_view,cleanrow


def prepare_one_m2f6(g,path,supplement_frames=()):
 supplement_frames=tuple(int(x) for x in supplement_frames)
 if len(supplement_frames)>4 or len(set(supplement_frames))!=len(supplement_frames):
  raise ValueError('SUPPLEMENT_BUDGET')
 vid=path.stem.split('_')[-1]; root=O/'prepared'/f'{g}_{vid}'; root.mkdir(parents=True,exist_ok=True)
 cap=cv2.VideoCapture(str(path)); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
 frames=candidate_frames(n)
 import importlib.util
 sp=importlib.util.spec_from_file_location('dxy_ring_holes', '/home/liu/new-polyp-dxy/src/dxy_mid/_engine/ring_holes.py'); mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
 replay=WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'
 if str(replay) not in sys.path:sys.path.insert(0,str(replay))
 import features019 as F19
 F19.R=O/'observation_matches'/f'{g}_{vid}';F19.R.mkdir(parents=True,exist_ok=True)
 candidates=[]; match_views=[]; cleanrows=[]
 for idx in frames:
  rec,mv,cr=prepare_real_candidate(g,vid,path,idx,root,mod)
  candidates.append(rec);match_views.append(mv);cleanrows.append(cr)
 edges={};edge_rows=[]
 for i in range(len(match_views)):
  for j in range(i+1,min(len(match_views),i+4)):
   m=F19.matches(match_views[i],match_views[j]);hits=int(np.asarray(m['RGB_RANSAC']).sum())
   edges[(i,j)]=hits;edge_rows.append(dict(first=i,second=j,RGB_RANSAC_N=hits,
                                           first_frame=frames[i],second_frame=frames[j]))
 selected,selection=select_observations(candidates,edges)
 if supplement_frames:
  by_frame={int(row['raw_frame']):row for row in candidates}
  if any(frame not in by_frame for frame in supplement_frames):
   raise ValueError('SUPPLEMENT_NOT_CURRENT_RAW_CANDIDATE')
  selected_by_frame={int(row['raw_frame']):row for row in selected}
  selected_by_frame.update({frame:by_frame[frame] for frame in supplement_frames})
  selected=[selected_by_frame[frame] for frame in sorted(selected_by_frame)]
  selection=dict(selection,supplemental_raw_frames=list(supplement_frames),
                 final_selected_raw_frames=[int(row['raw_frame']) for row in selected],
                 supplement_rule='CURRENT_REAL_CANDIDATE_REPREPARED_FROM_RAW')
 candidate_manifest=dict(group=g,video=vid,source_video=str(path),source_video_sha256=h(path),
                         frame_count=n,policy='M2F6_2D_CANDIDATES',candidates=candidates,
                         edges=edge_rows,source='raw_video_current_run')
 write_json(root/'CANDIDATE_MANIFEST.json',candidate_manifest)
 write_json(root/'OBSERVATION_SELECTION.json',selection)
 views=[dict(view=q['view'],raw_frame=q['raw_frame'],cache=q['cache'],
             rgb_sha256=q['RGB_sha256'],label_counts=q['label_counts']) for q in selected]
 meta=dict(group=g,video_id=vid,video=path.name,video_path=str(path),
           video_sha256=candidate_manifest['source_video_sha256'],init_weights=str(INIT),
           init_weight_sha256=INIT_SHA,math='PIL bilinear 256 /255; bilinear logits upsample; argmax',
           ring_mm=ring_mm(g),K=K.tolist(),views=views,
           source='M2F6_REAL_RAW_FRAMES_RECOVERY' if supplement_frames else 'M2F6_REAL_RAW_FRAMES',
           candidate_manifest=str(root/'CANDIDATE_MANIFEST.json'),
           candidate_manifest_sha256=h(root/'CANDIDATE_MANIFEST.json'),
           observation_selection=str(root/'OBSERVATION_SELECTION.json'),
           observation_selection_sha256=h(root/'OBSERVATION_SELECTION.json'))
 write_json(root/'PREPARED.json',meta)
 (O/'w0').mkdir(parents=True,exist_ok=True)
 pd.DataFrame(cleanrows).to_csv(O/'w0'/f'MASK_CLEAN_{g}_{vid}.csv',index=False)
 trace(g,vid,'prepare','rf-m2f6-2d-observation','tools/m2f5_unified.py::prepare_one_m2f6',
       [str(path)],[str(root/'CANDIDATE_MANIFEST.json'),str(root/'PREPARED.json')],
       'PASS',{'candidates':len(candidates),'selected':len(views),'graph_edges':selection['edge_count'],
               'candidate_manifest_sha256':meta['candidate_manifest_sha256']})
 return root,O/'clean_labels'/f'{g}_{vid}',meta

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

def attempt_root(attempt):
 return O if attempt==0 else O/'recovery'/f'round{attempt}'


def run_w0(g,vid,root,croot,attempt=0):
 base=attempt_root(attempt);out=base/'w0'/f'{g}_{vid}';log=base/'logs'/f'w0_{g}_{vid}.log';log.parent.mkdir(parents=True,exist_ok=True);meta=json.loads((root/'PREPARED.json').read_text());n=len(meta['views']);off=','.join(map(str,range(1,n)))
 cmd=[PY,str(WS/'tools/run_w0_camera.py'),'--group',g,'--video',vid,'--stage','all','--output',str(out),'--workdir',str(base/'work'/f'{g}_{vid}'),'--prepared-root',str(root.parent),'--clean-labels-root',str(O/'clean_labels'),'--ring-mode','all','--pair-offsets',off]
 if M2F6:cmd+=['--reference-policy','current','--initialization-policy','trained_versions']
 with log.open('w') as f:r=subprocess.run(cmd,cwd=WS,stdout=f,stderr=subprocess.STDOUT)
 trace(g,vid,'w0','rf-w0-camera@2','tools/run_w0_camera.py',[str(root/'PREPARED.json'),str(croot)],[str(out)],'PASS' if r.returncode==0 else 'FAIL',{'returncode':r.returncode,'frames':n,'attempt':attempt,'log':str(log),'prepared_sha256':h(root/'PREPARED.json')})
 return out if r.returncode==0 else None

def graph_counts(packet):
 p=Path(packet['manifest']['tracks']['path']).with_name('pairs005.npz');d=np.load(p);ids=list(packet['views']);c={x:set() for x in ids}
 for k,(i,j) in enumerate(d['ij']):
  if len(d[f'pair{k}'])>=12:c[ids[int(i)]].add(ids[int(j)]);c[ids[int(j)]].add(ids[int(i)])
 return {x:len(y) for x,y in c.items()}

def resolve_center(packet,mode):
 if mode=='ring':return np.zeros(3,float)
 if mode=='scene':return np.asarray(packet['points'],float).mean(axis=0)
 raise ValueError('UNKNOWN_CENTER_MODE '+str(mode))


def build_views(packet,center_mode='scene'):
 adm=pd.read_csv(Path(packet['w0_path']).parent/'admission.csv').set_index('view');center=resolve_center(packet,center_mode);poses=list(packet['cameras'].values());blocks=direction_blocks(poses,center);graph=graph_counts(packet);views=[]
 for i,(vid,e) in enumerate(packet['views'].items()):
  with np.load(e['cache']) as z:RGB=z['RGB'];Kv=z['K'];raw=z['labels']
  cp=O/'clean_labels'/f"{packet['group']}_{packet['video']}"/f'{vid}.npz';labels=np.load(cp)['labels']
  C=packet['cameras'][vid];q=quality_features(dict(RGB=RGB,labels=labels,T=C,K=Kv),center);row=adm.loc[vid].to_dict();s0,s1,s2=admission_tiers(row,graph[vid],'CURRENT_RUN')
  views.append(dict(id=vid,view=vid,video=packet['video'],role='FIT',C=C,K=Kv,RGB=RGB,labels=labels,raw_frame=int(e['raw_frame']),direction_block=blocks[i],s2=s2,graph_support_count=graph[vid],legacy_status=row['admission_status'],**q))
 return views,center

def select(g,vid,packet,attempt=0,center_mode='scene',with_receipt=False):
 views,center=build_views(packet,center_mode);pool=[v for v in views if v['s2']]
 array_sha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
 scene=resolve_center(packet,'scene');ring=resolve_center(packet,'ring')
 cams=np.asarray([v['C'][:3,3] for v in views]);av=cams-scene;bv=cams-ring
 av=av/np.linalg.norm(av,axis=1)[:,None];bv=bv/np.linalg.norm(bv,axis=1)[:,None]
 center_angles=np.degrees(np.arccos(np.clip(np.sum(av*bv,axis=1),-1.,1.)))
 receipt=dict(
  CENTER=dict(definition=center_mode,center_mm=center.tolist(),ring_cad_center_mm=ring.tolist(),
              scene_proxy_mm=scene.tolist(),scene_to_ring_mm=float(np.linalg.norm(scene-ring)),
              camera_direction_difference_median_deg=float(np.median(center_angles)),
              camera_direction_difference_max_deg=float(np.max(center_angles))),
  POOL=dict(source='CURRENT_W0_ALL_CAMERAS',local_admission_route='rf-m2f5-local-admission@1',
            input_count=len(views),s2_count=len(pool),
            current_admission_status_counts={name:sum(v['legacy_status']==name for v in views)
                                             for name in set(v['legacy_status'] for v in views)},
            members=[dict(id=v['id'],raw_frame=v['raw_frame'],s2=v['s2'],
                          current_w0_status=v['legacy_status'],direction_block=v['direction_block'],
                          graph_support_count=v['graph_support_count'],
                          RGB_sha256=array_sha(v['RGB']),Mask_sha256=array_sha(v['labels']),
                          K_sha256=array_sha(v['K']),c2w_sha256=array_sha(v['C'])) for v in views]))
 if len(pool)<4:
  receipt.update(ANCHOR=dict(status='INSUFFICIENT_LOCAL_POOL'),
                 T10=dict(status='NOT_RUN'),T13=dict(status='NOT_RUN'))
  return ([],center,len(pool),receipt) if with_receipt else ([],center,len(pool))
 def central(v):
  d=np.asarray(v['direction']);return float(np.median(np.degrees(np.arccos(np.clip(np.asarray([x['direction'] for x in pool])@d,-1,1)))))
 anchor=min(pool,key=central);res=select_views(pool,strategy='quality_diversity',max_views=min(8,len(pool)),baseline_ids=[anchor['id']]);rows=[]
 receipt['ANCHOR']=dict(id=anchor['id'],center_mode=center_mode,direction=anchor['direction'],
                        sharpness=anchor['sharpness'],
                        mask_complete_proxy=anchor['mask_complete_proxy'],
                        thin_structure_visibility_proxy=anchor['thin_structure_visibility_proxy'],
                        Ring_free_fraction=anchor['Ring_free_fraction'],
                        angular_centrality_median_deg=central(anchor))
 receipt['T10']=dict(strategy='quality_diversity',baseline_id=anchor['id'],
                     selected_ids=res['ids'],input_pool_ids=[v['id'] for v in pool])
 feats={};sift=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01)
 for v in pool:
  kp,d=sift.detectAndCompute(cv2.cvtColor(v['RGB'],cv2.COLOR_RGB2GRAY),None);feats[v['id']]=dict(des=d if d is not None else np.zeros((0,128),np.float32),xy=np.asarray([x.pt for x in kp],np.float32),N=len(kp))
 for rank,tid in enumerate(res['ids'],1):
  target=next(v for v in pool if v['id']==tid)
  try:r=select_views(pool,strategy='hero_support',max_views=3,target=target,features=lambda v:feats[v['id']],K=target['K'],cache_root=O/'cache'/f'round{attempt}'/center_mode/f'{g}_{vid}/{tid}')
  except Exception as e:r={'ids':[],'candidates':[]}
  sids=r.get('ids',[]);sups=[v for v in pool if v['id'] in sids];ok=len(sids)==3 and target['id'] not in sids
  if ok:ok,reason=validate_t13(target,sups,r.get('candidates',[]))
  else:reason='TUPLE_MEMBERSHIP'
  if ok:ok=all(x['s2'] for x in sups)
  rows.append(dict(group_id=g,video_id=vid,arm='LOCAL',method='T10',target_id=tid,support_ids=';'.join(sids),n_support=len(sids),ready=bool(ok),reason=reason,anchor_id=anchor['id'],candidate_scores=json.dumps(r.get('candidates',[]))))
 receipt['T13']=dict(strategy='hero_support',target_support=[dict(target_id=row['target_id'],
                       support_ids=row['support_ids'].split(';') if row['support_ids'] else [],
                       ready=row['ready'],reason=row['reason'],
                       candidates=json.loads(row['candidate_scores'])) for row in rows])
 return (rows,center,len(pool),receipt) if with_receipt else (rows,center,len(pool))

def tuple_frames(packet,target,supports):
 out=[]
 for vid in [target]+supports:
  e=packet['views'][vid];z=np.load(e['cache']);cp=O/'clean_labels'/f"{packet['group']}_{packet['video']}"/f'{vid}.npz';out.append(dict(id=vid,RGB=z['RGB'],labels=np.load(cp)['labels'],K=np.asarray(z['K'],float),c2w_mm=packet['cameras'][vid]))
 return out

def run_hero(g,vid,packet,row,model):
 out=O/'hero'/f'{g}_{vid}'/row['target_id'];out.mkdir(parents=True,exist_ok=True);rec=infer(model,tuple_frames(packet,row['target_id'],row['support_ids'].split(';')),out)
 return dict(group_id=g,video_id=vid,target_id=row['target_id'],support_ids=row['support_ids'],status='PASS',output_dir=str(out),seconds=rec.get('seconds'),raw_faces=rec.get('raw_faces'),tuple_sha=hashlib.sha256((g+'|'+vid+'|'+row['target_id']+'|'+row['support_ids']).encode()).hexdigest()[:16])


def run_m2f6_recovery(g,vid,initial_root,croot):
 """One bounded real-frame loop; every attempt calls the same W0 and T10/T13."""
 from tools.m2a_c3 import pair_graph
 import shutil
 candidate_path=O/'prepared'/f'{g}_{vid}'/'CANDIDATE_MANIFEST.json'
 candidates=json.loads(candidate_path.read_text())['candidates']
 replay=WS/'experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/replay'
 if str(replay) not in sys.path:sys.path.insert(0,str(replay))
 import features019 as F19
 F19.R=O/'observation_matches'/f'{g}_{vid}'

 def attempt(prepared,number):
  base=attempt_root(number);out=base/'w0'/f'{g}_{vid}'
  packet_path=run_w0(g,vid,prepared,croot,number)
  if packet_path is None:
   status=json.loads((out/'STATUS.json').read_text()) if (out/'STATUS.json').exists() else {}
   code=status.get('error_type') or status.get('reason') or 'W0_RUN_FAILED'
   reason=recovery_reason_from_evidence(error_type=code)
   return dict(status=status.get('status','W0_RUN_FAILED'),recovery_reason=reason,
               error_type=code,packet_path=str(out))
  try:
   packet=verify_w0_packet(out,WS)
   rows,center,pool,selection_receipt=select(g,vid,packet,number,'ring',True)
  except Exception as exc:
   trace(g,vid,'select','rf-m2f5-t10+t13','selection.py::select_views',
         [str(out)],[str(base/'selection'/f'{g}_{vid}.csv')],'FAIL',
         {'attempt':number,'error_type':type(exc).__name__,'reason':str(exc)})
   return dict(status='SELECTION_FAILED',recovery_reason=None,error_type=type(exc).__name__)
  selection_path=base/'selection'/f'{g}_{vid}.csv';selection_path.parent.mkdir(parents=True,exist_ok=True)
  pd.DataFrame(rows).to_csv(selection_path,index=False)
  receipt_root=base/'selection_receipts'/f'{g}_{vid}';receipt_paths=[]
  for label,value in selection_receipt.items():
   path=receipt_root/f'{label}.json';write_json(path,value);receipt_paths.append(str(path))
  ready=sum(x['ready'] for x in rows)
  trace(g,vid,'select','rf-m2f5-t10+t13','selection.py::select_views',
        [str(out)],[str(selection_path)]+receipt_paths,'PASS' if ready else 'INSUFFICIENT_SUPPORT',
        {'attempt':number,'pool':pool,'targets':len(rows),'ready':ready,
         'selection_sha256':h(selection_path),'center_mode':'ring',
         'receipt_sha256':{Path(p).name:h(p) for p in receipt_paths}})
  visual=O/'visualization'/f'{g}_{vid}'/f'round{number}'
  images=render_observation_evidence(prepared/'PREPARED.json',croot,out/'W0.npz',visual)
  trace(g,vid,'observation_visual','rf-m2f6-2d-observation',
        'm2f6_observations.py::render_observation_evidence',
        [str(prepared/'PREPARED.json'),str(out/'W0.npz')],list(images.values()),'PASS',
        {'attempt':number,'image_sha256':{k:h(v) for k,v in images.items()}})
  quality=json.loads((out/'quality_summary.json').read_text())
  reason=recovery_reason_from_evidence(quality=quality,rows=rows)
  return dict(status='OBSERVATION_READY' if reason is None else 'RECOVERY_NEEDED',
              recovery_reason=reason,packet_path=str(out),selection_path=str(selection_path),
              n_accept=quality['n_accept'],ready=ready)

 def add(prepared,reason,number):
  current=json.loads((prepared/'PREPARED.json').read_text());existing={x['view'] for x in current['views']}
  prior=number-1;work=attempt_root(prior)/'work'/f'{g}_{vid}'
  if (work/'observations/tracks005.npz').exists():
   tr,edges,comps=pair_graph(work)
   components=[[str(tr['ids'][i]) for i in comp] for comp in comps]
  else:components=[sorted(existing)]
  if not components:components=[sorted(existing)]
  # C2 uses one representative from each disconnected component.  For a
  # connected but poor W0, query four time-spread observations.
  if len(components)==1 and len(components[0])>4:
   part=components[0];reps=[part[i] for i in np.linspace(0,len(part)-1,4,dtype=int)]
  else:reps=[part[len(part)//2] for part in components if part]
  match_counts={}
  def measure(rows):
   for row in rows:
    if row['view'] in existing or row['ring_train_points']<20:continue
    av=dict(id=row['view'],cache=str(F19.R/'clean_cache'/(row['view']+'.npz')),
            RGB_SHA256=row['RGB_sha256'])
    for rep in reps:
     brow=next((x for x in candidates if x['view']==rep),None)
     if brow is None:continue
     bv=dict(id=rep,cache=str(F19.R/'clean_cache'/(rep+'.npz')),
             RGB_SHA256=brow['RGB_sha256'])
     m=F19.matches(av,bv);match_counts[(row['view'],rep)]=int(np.asarray(m['RGB_RANSAC']).sum())
  measure(candidates)
  added,receipt=choose_real_supplements(candidates,list(existing),components,
                                        match_counts,reason,budget=4)
  fresh=[]
  if not added:
   # C2/B1R also searched real frames outside their initial prepared set.
   # Use at most twelve mid-gap frames and the exact same INIT + DXY adapter.
   import importlib.util
   sp=importlib.util.spec_from_file_location('dxy_ring_holes',
       '/home/liu/new-polyp-dxy/src/dxy_mid/_engine/ring_holes.py')
   cleaner=importlib.util.module_from_spec(sp);sp.loader.exec_module(cleaner)
   known=sorted({int(row['frame']) for row in candidates})
   gaps=sorted(((b-a,(a+b)//2) for a,b in zip(known,known[1:])),reverse=True)
   extra=[mid for gap,mid in gaps if gap>=12 and mid not in known][:12]
   raw_path=Path(current['video_path'])
   freshroot=attempt_root(number)/'raw_candidates'/f'{g}_{vid}';freshroot.mkdir(parents=True,exist_ok=True)
   for frame in extra:
    rec,_,_=prepare_real_candidate(g,vid,raw_path,frame,freshroot,cleaner)
    fresh.append(rec);candidates.append(rec)
   measure(fresh)
   added,receipt=choose_real_supplements(candidates,list(existing),components,
                                         match_counts,reason,budget=4)
  receipt.update(round=number,added=[x['view'] for x in added],
                 parent_prepared_sha256=h(prepared/'PREPARED.json'),
                 fresh_real_candidates=fresh)
  nextroot=attempt_root(number)/'prepared'/f'{g}_{vid}';nextroot.mkdir(parents=True,exist_ok=True)
  write_json(nextroot/'SUPPLEMENT_RECEIPT.json',receipt)
  if not added:
   trace(g,vid,'supplement','rf-m2f6-real-observation',
         'm2f6_observations.py::choose_real_supplements',
         [str(prepared/'PREPARED.json'),str(candidate_path)],
         [str(nextroot/'SUPPLEMENT_RECEIPT.json')],'FAIL',
         {'attempt':number,'reason':reason,'added':0})
   return prepared,receipt
  views=current['views']+[dict(view=x['view'],raw_frame=x['raw_frame'],cache=x['cache'],
                               rgb_sha256=x['RGB_sha256'],label_counts=x['label_counts']) for x in added]
  nextmeta=dict(current,views=sorted(views,key=lambda x:(x['raw_frame'],x['view'])),
                source='M2F6_REAL_RAW_FRAMES_RECOVERY',recovery_round=number,
                parent_prepared_sha256=receipt['parent_prepared_sha256'],
                supplement_receipt=str(nextroot/'SUPPLEMENT_RECEIPT.json'))
  write_json(nextroot/'PREPARED.json',nextmeta)
  trace(g,vid,'supplement','rf-m2f6-real-observation',
        'm2f6_observations.py::choose_real_supplements',
        [str(prepared/'PREPARED.json'),str(candidate_path)],
        [str(nextroot/'PREPARED.json'),str(nextroot/'SUPPLEMENT_RECEIPT.json')],'PASS',
        {'attempt':number,'reason':reason,'added':receipt['added'],
         'prepared_sha256':h(nextroot/'PREPARED.json')})
  return nextroot,receipt

 result=bounded_recovery(initial_root,attempt,add,max_rounds=2)
 final_attempt=result['final_attempt'];final_selection=attempt_root(final_attempt)/'selection'/f'{g}_{vid}.csv'
 final_w0=attempt_root(final_attempt)/'w0'/f'{g}_{vid}'
 result.update(final_w0_path=str(final_w0),final_selection_path=str(final_selection),
               final_prepared_path=str(result['final_prepared']/'PREPARED.json'),
               final_prepared_sha256=h(result['final_prepared']/'PREPARED.json'))
 status_path=O/'recovery'/f'{g}_{vid}_RESULT.json';write_json(status_path,result)
 if result['status']=='OBSERVATION_READY' and final_selection.exists():
  dest=O/'selection'/f'{g}_{vid}.csv';dest.parent.mkdir(parents=True,exist_ok=True)
  if final_selection.resolve()!=dest.resolve():shutil.copy2(final_selection,dest)
  trace(g,vid,'final_selection','rf-m2f6-real-observation','tools/m2f5_unified.py::run_m2f6_recovery',
        [str(final_selection)],[str(dest),str(status_path)],'PASS',
        {'attempt':final_attempt,'selection_sha256':h(dest)})
 else:
  trace(g,vid,'final_selection','rf-m2f6-real-observation','tools/m2f5_unified.py::run_m2f6_recovery',
        [str(status_path)],[],'FAIL',{'attempt':final_attempt,'reason':result.get('failure_reason',result['status'])})
 return result

def main():
 global O,M2F6
 ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['prepare','w0','all'],default='all');ap.add_argument('--groups',default=','.join(GROUPS));ap.add_argument('--videos',default='');ap.add_argument('--limit',type=int,default=0);ap.add_argument('--m2f6',action='store_true');ap.add_argument('--output-root',default=None);a=ap.parse_args();groups=[x for x in a.groups.split(',') if x]
 M2F6=bool(a.m2f6)
 if a.output_root:O=Path(a.output_root).resolve()
 elif M2F6:O=WS/'runs/m2f6_unified/final'
 wanted={x.zfill(3) for x in a.videos.split(',') if x}
 for g in groups:
  paths=[path for path in video_paths(g) if not wanted or path.stem.split('_')[-1] in wanted]
  if M2F6:
   found={path.stem.split('_')[-1] for path in paths}
   for vid in sorted(wanted-found):
    fail=dict(status='MISSING_RAW_VIDEO',group=g,video=vid,reason='NO_MATCHING_SOURCE_VIDEO')
    p=O/'recovery'/f'{g}_{vid}_RESULT.json';write_json(p,fail)
    trace(g,vid,'source_video','rf-m2f6-real-observation','tools/m2f5_unified.py::video_paths',
          [str(RAW)],[str(p)],'FAIL',{'reason':fail['reason']})
  for path in paths:
   vid=path.stem.split('_')[-1]
   active_stage='prepare'
   try:
    if a.stage in ('prepare','all'): root,croot,meta=(prepare_one_m2f6(g,path) if M2F6 else prepare_one(g,path))
    if a.stage in ('w0','all'):
     active_stage='w0_and_select'
     root=O/'prepared'/f'{g}_{vid}';croot=O/'clean_labels'/f'{g}_{vid}'
     if M2F6:
      result=run_m2f6_recovery(g,vid,root,croot)
      print('RECOVERY',g,vid,result['status'],'final_attempt',result['final_attempt'],flush=True)
      continue
     out=run_w0(g,vid,root,croot)
     if out is None: print('W0FAIL',g,vid,flush=True);continue
     try:
      packet=verify_w0_packet(out,WS);rows,center,pool=select(g,vid,packet)
      (O/'selection').mkdir(parents=True,exist_ok=True)
      selection_path=O/'selection'/f'{g}_{vid}.csv'
      pd.DataFrame(rows).to_csv(selection_path,index=False)
      trace(g,vid,'select','rf-m2f5-t10+t13','selection.py::select_views',
            [str(packet['w0_path'])],[str(selection_path)],'PASS',
            {'pool':pool,'targets':len(rows),'ready':sum(x['ready'] for x in rows),
             'selection_sha256':h(selection_path)})
      print('SELECT',g,vid,'pool',pool,'ready',sum(x['ready'] for x in rows),flush=True)
     except Exception as e:
      print('SELECTFAIL',g,vid,repr(e),flush=True);continue
   except Exception as exc:
    if not M2F6:raise
    fail=dict(status='PIPELINE_EXCEPTION',group=g,video=vid,stage=active_stage,
              error_type=type(exc).__name__,reason=str(exc),traceback=traceback.format_exc())
    p=O/'recovery'/f'{g}_{vid}_RESULT.json';write_json(p,fail)
    trace(g,vid,active_stage,'rf-m2f6-unified','tools/m2f5_unified.py::main',
          [str(path)],[str(p)],'FAIL',{'error_type':fail['error_type'],'reason':fail['reason']})
    print('PIPELINE_EXCEPTION',g,vid,fail['stage'],fail['reason'],flush=True)
   if a.limit and len(list((O/'selection').glob('*.csv')))>=a.limit: break
 print('DONE')
if __name__=='__main__':main()
