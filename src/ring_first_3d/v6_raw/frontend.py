"""Opt-in frontend integration; existing route stages remain authoritative."""
from pathlib import Path
import copy, hashlib, json, sys
import cv2
import numpy as np
from .frontend_policy import anchor_component,temporal_edges,unique_eligible,select_plan_version,extend_video_tracks

def enabled(r):return bool(r.FULL_CONFIG and r.FULL_CONFIG.get('frontend'))

def prepare_cached(r,case,root,raw_hash,signature):
 """Reuse only unchanged RAW selection/INIT results, never old cameras."""
 cfg=r.FULL_CONFIG['frontend'];base=Path(cfg['baseline_root']);state=r.read(base/'states'/(case+'.json'));old=Path(state['run_path'])/'inputs/INPUT_IDENTITY.json';meta=r.read(old)
 assert meta['raw_sha256']==raw_hash and np.array_equal(meta['K'],r.K)
 assert meta['original16']==r.frame_indices(meta['frame_count'])
 assert set(x['raw_frame'] for x in meta['frames'])==set(meta['original16']+meta['selected_extra'])
 assert meta['selection_source_sha256']==r.sha(r.V6/'scripts/setup_audit.py')
 assert all(r.sha(p)==h for p,h in meta['INIT_files'].items())
 for i,row in enumerate(meta['frames']):
  for key in ['RGB','Mask']:assert r.sha(row[key+'_path'])==row[key+'_SHA256']
  rgb=cv2.imread(row['RGB_path']);physical=hashlib.sha256(rgb.tobytes()).hexdigest()
  row.update(view_id=case+':raw:'+str(row['raw_frame']),physical_view_id=physical,media_type='video',video_id=case,original_index=i,video_raw_frame=row['raw_frame'],working_shape=[360,640],coordinate_system=case)
 root.mkdir(parents=True,exist_ok=True)
 meta.update(protocol_signature=signature,preprocessing_reuse=dict(source=str(old),sha256=r.sha(old),original_execution_commit=meta['execution_commit'],selection_and_INIT_semantics_unchanged=True),execution_commit=r.head(),original_video_frames=copy.deepcopy(meta['frames']))
 if cfg.get('include_photos'):
  from .frontend_photos import prepare_group
  meta['frames']+=prepare_group(r,case.rsplit('_',1)[0],case)
 meta['original_video_target_count']=len(meta['original_video_frames'])-1
 r.save(root/'PREPARED.json',meta);return meta

def component(r,R,meta,mods,ref,held):
 full=meta['frames'];preserve_video_tracks(r,R,meta)
 tr=dict(np.load(R/'observations/tracks005.npz'));pack=dict(np.load(R/'observations/pairs005.npz'));edges=mods['lba'].pair_data(tr,pack)
 keep=anchor_component(len(full),[(e['i'],e['j']) for e in edges],ref)
 eligible=unique_eligible(full,keep,held)
 original_reference=dict(reference_index=ref,heldout_index=held,reference_view_id=full[ref]['view_id'],diagnostic_view_id=full[held]['view_id'],reference_raw=full[ref]['raw_frame'],diagnostic_raw=full[held]['raw_frame'])
 receipt=dict(original_reference=original_reference,original_view_count=len(full),original_video_target_count=meta['original_video_target_count'],retained_indices=keep,excluded=[dict(index=i,view_id=x['view_id'],raw_frame=x['raw_frame'],media_type=x['media_type'],reason='NOT_IN_ORIGINAL_ANCHOR_COMPONENT') for i,x in enumerate(full) if i not in keep],eligible_distinct_without_B=len(eligible),graph_edges=[dict(i=e['i'],j=e['j'],inliers=len(e['rows'])) for e in edges],temporal_edges=temporal_edges(full,keep),diagnostic_available=held in keep,original_track_count=len(tr['held']),original_held_track_ids=np.flatnonzero(tr['held']).tolist())
 r.save(R/'ORIGINAL_VIEW_POOL.json',full);r.save(R/'COMPONENT.json',receipt)
 if len(eligible)<4:raise ValueError('NOT_ENOUGH_DISTINCT_ANCHOR_COMPONENT_VIEWS_EXCLUDING_B')
 index={old:new for new,old in enumerate(keep)}
 for name in ['tracks005.npz','pairs005.npz']:(R/'observations'/name).rename(R/'observations'/('FULL_'+name))
 reduced=dict(tr,xy=tr['xy'][:,keep],ids=tr['ids'][keep],frame_raw=tr['frame_raw'][keep],original_track_id=np.arange(len(tr['held'])),original_view_index=keep)
 np.savez_compressed(R/'observations/tracks005.npz',**reduced)
 new_pairs={};ij=[]
 for k,(i,j) in enumerate(pack['ij']):
  if int(i) in index and int(j) in index:
   new_pairs['pair'+str(len(ij))]=pack['pair'+str(k)];ij.append([index[int(i)],index[int(j)]])
 np.savez_compressed(R/'observations/pairs005.npz',ij=np.asarray(ij).reshape(-1,2),**new_pairs)
 rings=r.read(R/'predictions/ring_candidates005.json');r.save(R/'predictions/FULL_ring_candidates005.json',rings);r.save(R/'predictions/ring_candidates005.json',[rings[i] for i in keep])
 meta=copy.deepcopy(meta);meta['frames']=[full[i] for i in keep];meta['component_original_indices']=keep
 r.save(R/'inputs/ledger005.json',meta['frames']);r.save(R/'inputs/INPUT_IDENTITY.json',meta)
 v6=mods['v6'];v6.freeze('ring_inputs',[R/'inputs/ledger005.json',R/'inputs/INPUT_IDENTITY.json',R/'predictions/ring_candidates005.json']+list((R/'observations').glob('*_ring.npz')))
 v6.freeze('tracks',[R/'observations/tracks005.npz',R/'observations/pairs005.npz',R/'metrics/track005.json',R/'COMPONENT.json'])
 mods['lba']._FRONTEND_TEMPORAL=receipt['temporal_edges']
 return meta,index[ref],index.get(held,-1),original_reference

def preserve_video_tracks(r,R,meta):
 base=Path(meta['preprocessing_reuse']['source']).parents[1];old=dict(np.load(base/'observations/tracks005.npz'));op=dict(np.load(base/'observations/pairs005.npz'));tr=dict(np.load(R/'observations/tracks005.npz'));pack=dict(np.load(R/'observations/pairs005.npz'));n=len(old['ids'])
 assert list(old['ids'])==[a['id'] for a in meta['original_video_frames']]
 if len(meta['frames'])==n:
  assert np.array_equal(old['xy'],tr['xy'],equal_nan=True) and np.array_equal(old['held'],tr['held']) and np.array_equal(old['category'],tr['category']),'ORIGINAL_VIDEO_TRACK_DRIFT'
  r.save(R/'TRACK_EXTENSION.json',dict(original_tracks=len(old['held']),original_track_file=str(base/'observations/tracks005.npz'),original_track_sha256=r.sha(base/'observations/tracks005.npz'),video_only_recomputed_exactly=True));return
 xy,cat,held,mapping,receipt=extend_video_tracks(old['xy'],old['category'],old['held'],tr['xy'],tr['category'])
 ij=op['ij'].tolist();pairs={k:v for k,v in op.items() if k!='ij'};skipped=0
 for k,(i,j) in enumerate(pack['ij']):
  if i<n and j<n:continue
  rows=[]
  for row in pack['pair'+str(k)]:
   tid=mapping.get(int(row[0]))
   if tid is None or not np.array_equal(xy[tid,[i,j]].ravel(),row[1:]):skipped+=1;continue
   rows.append([tid,*row[1:]])
  pairs['pair'+str(len(ij))]=np.asarray(rows).reshape(-1,5);ij.append([int(i),int(j)])
 for name in ['tracks005.npz','pairs005.npz']:(R/'observations'/name).rename(R/'observations'/('MIXED_UNION_'+name))
 np.savez_compressed(R/'observations/tracks005.npz',**dict(tr,xy=xy,category=cat,held=held))
 np.savez_compressed(R/'observations/pairs005.npz',ij=np.asarray(ij),**pairs)
 receipt.update(original_track_file=str(base/'observations/tracks005.npz'),original_track_sha256=r.sha(base/'observations/tracks005.npz'),discarded_ambiguous_pair_rows=skipped,mixed_track_to_preserved_track=mapping,photo_connection='original SIFT matching; reject ambiguous original-track merges; old video pairs retained bitwise')
 r.save(R/'TRACK_EXTENSION.json',receipt)

def record_kernels(r,R,mods):
 from .frontend_kernels import RECEIPTS
 rows=dict(RECEIPTS)
 for name,module in mods.items():
  if isinstance(module,dict):
   rows['namespace:'+name]=dict(kind='function namespace',functions={k:dict(file=v.__code__.co_filename,line=v.__code__.co_firstlineno) for k,v in module.items() if hasattr(v,'__code__')});continue
  rows['module:'+name]=dict(module=module.__name__,module_file=module.__file__,sha256=r.sha(module.__file__))
 r.save(R/'FRONTEND_KERNELS.json',dict(execution_commit=r.head(),frontend_config=r.FULL_CONFIG['frontend'],functions=rows,external_sources_modified=False))

def select_complete_plan(r,case,variant,build):
 R=r.cameras(case,variant)
 if (R/'PLAN_FROZEN.json').exists() and (R/'INITIALIZATION_SELECTION.json').exists():return build(case,variant,R=R)
 val=r.read(R/'metrics/local_validation.json');primary=val['primary'];versions=[primary]+[v['version'] for v in val['versions'] if v['version']!=primary]
 assert len(versions)<=2
 plans={};snapshots={}
 for version in versions:
  if plans and plans[primary]['budget']>0:break
  if (R/'PLAN_FROZEN.json').exists():(R/'PLAN_FROZEN.json').unlink()
  plan=build(case,variant,R=R,primary_override=version);plans[version]=plan
  snapshots[version]={name:r.read(R/name) for name in ['metrics/GATES.json','inputs/MVS_supported_cases.json']}
  r.save(R/'initializations'/f'version{version}_PLAN.json',plan)
  r.save(R/'initializations'/f'version{version}_GATES.json',snapshots[version]['metrics/GATES.json'])
 chosen=select_plan_version(plans,primary);plan=plans[chosen]
 for name,data in snapshots[chosen].items():r.save(R/name,data)
 r.save(R/'PLAN_FROZEN.json',plan)
 m=r.legacy();mods=r.bind(m,R,r.read(R/'inputs/INPUT_IDENTITY.json'));mods['v6'].freeze('supported_view_selection',[R/'inputs/MVS_supported_cases.json'])
 r.save(R/'predictions/local005_primary.json',dict(primary_version=chosen,default_version=primary,selection='original legal plan first; alternate only when zero',camera_sha256=plan['cameras_sha256'],status='MODEL_PREDICTED',independent_004_alignment=False))
 r.save(R/'INITIALIZATION_SELECTION.json',dict(default_version=primary,selected_version=chosen,plans=[dict(version=v,numeric_cameras=p['numeric_cameras'],q0=p['old_cameras'],q1=p['new_cameras'],legal_tuples=p['budget'],camera_sha256=p['cameras_sha256']) for v,p in plans.items()],unused_versions=[v for v in versions if v not in plans],bounded_versions=2,held_metrics_are_selection_not_independent_test=True))
 return plan
