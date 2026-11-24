#!/usr/bin/env python3
"""M2F5: HERO, Raw metric mesh, B-camera A-to-B and six-view for fresh 13-group selections."""
import sys,json,pathlib,hashlib,time,argparse,shutil,subprocess
import numpy as np,pandas as pd
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');O=WS/'runs/m2f5_unified';M2F6=False
sys.path[:0]=[str(WS/'src'),str(WS/'src/ring_first_3d/mainline/frozen_registry'),str(WS/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code')]
from ring_first_3d.mainline.input_identity import verify_w0_packet,tuple_receipt
from ring_first_3d.mainline.native.hero import load_official,infer
from ring_first_3d.mainline.native.geometry import native_rgb_labels
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
import reprojection as rp, open3d as o3d
from matplotlib import pyplot as plt
from matplotlib import colors

def write_json(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=1,default=str)+'\n')
def array_sha(value):return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()
def trace(g,v,stage,route,entry,inputs,outputs,status,extra=None):
 p=O/'RUN_TRACE'/f'{g}_{v}.jsonl';p.parent.mkdir(parents=True,exist_ok=True);rec=dict(run_id='M2F6-UNIFIED-OBSERVATION-001' if M2F6 else 'M2F5-UNIFIED-001',group_id=g,video_id=v,stage=stage,route_id=route,route_version='1',entrypoint=entry,inputs=inputs,outputs=outputs,status=status,code_commit=__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=WS,text=True).strip(),config_hash=hashlib.sha256((WS/'mainline/configs/SITE.local.json').read_bytes()).hexdigest());
 if extra:rec.update(extra)
 with p.open('a') as f:f.write(json.dumps(rec,sort_keys=True)+'\n')
def final_packet_path(root,g,v):
 result=pathlib.Path(root)/'recovery'/f'{g}_{v}_RESULT.json'
 if not result.exists():raise ValueError(f'OBSERVATION_NOT_READY {g}/{v}: missing recovery result')
 status=json.loads(result.read_text())
 if status.get('status')!='OBSERVATION_READY':
  raise ValueError(f'OBSERVATION_NOT_READY {g}/{v}: {status.get("status")}')
 packet=pathlib.Path(status['final_w0_path']).resolve()
 if not packet.is_relative_to(pathlib.Path(root).resolve()) or not (packet/'W0.npz').is_file():
  raise ValueError(f'FINAL_W0_IDENTITY_ERROR {packet}')
 return packet
def infer_with_receipt(model,actual_frames,out,run_id,code_version,g,v,identity_verified=True):
 """Record the exact four arrays before the real frozen HERO call."""
 out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
 receipt=tuple_receipt(identity_verified,actual_frames,run_id,code_version)
 receipt_path=out/'TUPLE_INPUT_RECEIPT.json';write_json(receipt_path,receipt)
 trace(g,v,'hero_input','rf-m2f6-tuple-identity','input_identity.py::tuple_receipt',
       [x['id'] for x in actual_frames],[str(receipt_path)],'VERIFIED',
       {'tuple_sha256':receipt['tuple_sha256'],'receipt_sha256':hashlib.sha256(receipt_path.read_bytes()).hexdigest()})
 result=infer(model,actual_frames,out)
 return result,receipt
def load_clean(g,v,vid):
 return np.load(O/'clean_labels'/f'{g}_{v}'/(vid+'.npz'))['labels']
def frames(packet,target,supports):
 out=[]
 for vid in [target]+supports:
  e=packet['views'][vid];z=np.load(e['cache']);out.append(dict(id=vid,RGB=z['RGB'],labels=load_clean(packet['group'],packet['video'],vid),K=np.asarray(z['K'],float),c2w_mm=packet['cameras'][vid]))
 return out
def verified_m2f6_frames(packet,target,supports,root):
 """Close the current clean-mask and RGB identity chain before HERO."""
 actual=frames(packet,target,supports)
 manifest=packet['manifest'];prepared=pathlib.Path(manifest['prepared']['path'])
 if not prepared.is_absolute():prepared=WS/prepared
 meta=json.loads(prepared.read_text());candidate=pathlib.Path(meta['candidate_manifest'])
 if hashlib.sha256(candidate.read_bytes()).hexdigest()!=meta['candidate_manifest_sha256']:
  raise ValueError('CANDIDATE_MANIFEST_HASH')
 candidates={r['view']:r for r in json.loads(candidate.read_text())['candidates']}
 for number in range(1,int(meta.get('recovery_round',0))+1):
  supplement=pathlib.Path(root)/'recovery'/f'round{number}'/'prepared'/f"{packet['group']}_{packet['video']}"/'SUPPLEMENT_RECEIPT.json'
  receipt=json.loads(supplement.read_text())
  parent=(pathlib.Path(root)/'prepared'/f"{packet['group']}_{packet['video']}"/'PREPARED.json'
          if number==1 else pathlib.Path(root)/'recovery'/f'round{number-1}'/'prepared'/f"{packet['group']}_{packet['video']}"/'PREPARED.json')
  if hashlib.sha256(parent.read_bytes()).hexdigest()!=receipt['parent_prepared_sha256']:
   raise ValueError('SUPPLEMENT_PARENT_HASH')
  for row in receipt.get('fresh_real_candidates',[]):
   if row['view'] in candidates:raise ValueError('DUPLICATE_CANDIDATE_ID')
   candidates[row['view']]=row
 for frame in actual:
  vid=frame['id'];entry=candidates.get(vid)
  if entry is None:raise ValueError(f'MISSING_REAL_CANDIDATE {vid}')
  cp=pathlib.Path(root)/'clean_labels'/f"{packet['group']}_{packet['video']}"/f'{vid}.npz'
  if hashlib.sha256(cp.read_bytes()).hexdigest()!=entry['clean_labels_sha256']:
   raise ValueError(f'CLEAN_LABEL_FILE_HASH {vid}')
  expected={'RGB':entry['RGB_sha256'],'labels':entry['clean_mask_sha256'],
            'K':entry['K_sha256']}
  for name,sha in expected.items():
   if array_sha(frame[name])!=sha:raise ValueError(f'CURRENT_{name}_HASH {vid}')
  if not np.allclose(frame['K'],packet['K'],atol=1e-8) or not np.array_equal(
      frame['c2w_mm'],packet['cameras'][vid]):
   raise ValueError(f'CURRENT_CAMERA_GEOMETRY {vid}')
 return actual
def scene(kind):
 d=dict(np.load(O/'cad'/f'{kind}.npz'));s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(d['V'].astype(np.float32)),o3d.core.Tensor(d['F'].astype(np.uint32)));return s
rp.cad_scene=scene

def render_existing_video(input_root, output_root, group, video):
 """Render every retained raw target surface in its measured world position."""
 source=pathlib.Path(input_root);dest=pathlib.Path(output_root);video=str(video).zfill(3)
 table=pd.read_csv(source/'hero/HERO_EXECUTION_RESULTS.csv')
 rows=table[(table.group_id==group)&(table.video_id.astype(str).str.zfill(3)==video)&
            (table.status.isin(['PASS','REUSED']))].to_dict('records')
 if not rows:raise ValueError(f'NO_HERO_SURFACES {group}/{video}')
 kind='R5' if '_R5' in group else 'R10';cad_path=source/'cad'/f'{kind}.npz'
 with np.load(cad_path) as z:cad_v,cad_f=z['V'],z['F']
 recovery=source/'recovery'/f'{group}_{video}_RESULT.json'
 w0_root=final_packet_path(source,group,video) if recovery.exists() else source/'w0'/f'{group}_{video}'
 with np.load(w0_root/'W0.npz') as z:
  cameras={str(i):c for i,c in zip(z['ids'],z['c2w'])}
 vertices,faces,colours,mesh_receipts=[],[],[],[];offset=0
 palette=plt.get_cmap('tab20',max(20,len(rows)))
 for index,row in enumerate(rows):
  mesh_path=pathlib.Path(row['output_dir'])/'RAW_NATIVE_MESH.npz'
  with np.load(mesh_path) as z:V,F=np.asarray(z['V'],float),np.asarray(z['F'],int)
  if not len(V) or not len(F):raise ValueError(f'EMPTY_RAW_MESH {mesh_path}')
  vertices.append(V);faces.append(F+offset);colours.append(np.tile(palette(index)[:3],(len(F),1)))
  offset+=len(V)
  mesh_receipts.append(dict(target_id=str(row['target_id']),path=str(mesh_path),
                            sha256=hashlib.sha256(mesh_path.read_bytes()).hexdigest()))
 V=np.concatenate(vertices);F=np.concatenate(faces);face_colours=np.concatenate(colours)
 centre=(V.min(axis=0)+V.max(axis=0))/2
 first=rows[0];ids=[str(first['target_id'])]+str(first['support_ids']).split(';')[:2]
 if len(ids)!=3 or any(cid not in cameras for cid in ids):raise ValueError('MISSING_REAL_CAMERA')
 panels=[]
 for cid in ids:
  direction=cameras[cid][:3,3]-centre;length=np.linalg.norm(direction)
  if length<=0:raise ValueError('ZERO_CAMERA_VIEW_DIRECTION')
  direction/=length
  panels.append((cid,float(np.degrees(np.arcsin(direction[2]))),
                 float(np.degrees(np.arctan2(direction[1],direction[0])))))
 panels.extend([('World X',0.,0.),('World Y',0.,90.),('World Z',89.9999,0.)])
 fig,axes=plt.subplots(1,6,figsize=(18,3.5));scales=[]
 for axis,(label,elevation,azimuth) in zip(axes,panels):
  image,pixels_per_mm=actual_mesh_image(V,F,cad_v,cad_f,V,elevation,azimuth,
                                         '#d98989',face_colors=face_colours)
  axis.imshow(image);axis.set_title(label,fontsize=7);axis.axis('off')
  axis.plot([15,15+5*pixels_per_mm],[378,378],color='black',lw=2)
  axis.text(15,373,'~5 mm at view centre',fontsize=6)
  scales.append(float(pixels_per_mm))
 fig.suptitle(f'{group}/{video}: {len(rows)} raw target surfaces + {kind} Ring CAD; GT deployment pose unknown')
 fig.tight_layout();path=dest/'visualization/multisurface'/f'{group}_{video}.png'
 path.parent.mkdir(parents=True,exist_ok=True);fig.savefig(path,dpi=110);plt.close(fig)
 result=dict(group_id=group,video_id=video,cad_kind=kind,cad_sha256=hashlib.sha256(cad_path.read_bytes()).hexdigest(),
             W0_sha256=hashlib.sha256((w0_root/'W0.npz').read_bytes()).hexdigest(),
             view_labels=[x[0] for x in panels],scale_bar_mm=5.,pixels_per_mm=scales,
             surface_count=len(rows),source_meshes=mesh_receipts,image=str(path),
             GT_deployment_pose='UNKNOWN',all_surfaces_retained=True)
 write_json(path.with_suffix('.json'),result)
 return result

def main():
 # selection tables
 sels=sorted((O/'selection').glob('*.csv'));rows=[]
 for f in sels:
  d=pd.read_csv(f);rows.extend(d[d.ready==True].to_dict('records'))
 uni=[];seen=set()
 for r in rows:
  key=(r['group_id'],r['video_id'],r['target_id'],r['support_ids'])
  if key not in seen:seen.add(key);uni.append(r)
 print('ready rows',len(rows),'unique',len(uni),flush=True)
 model=None;cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text());sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
 model,receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text()));write_json(O/'hero/MODEL_RECEIPT.json',receipt)
 hero=[];a2b=[]
 for n,r in enumerate(uni,1):
  g,v,target=str(r['group_id']),f"{int(r['video_id']):03d}",str(r['target_id']);sups=str(r['support_ids']).split(';');packet=verify_w0_packet(O/'w0'/f'{g}_{v}',WS);out=O/'hero'/g/v/target;out.mkdir(parents=True,exist_ok=True)
  try:
   if not (out/'HERO_native.npz').exists():
    rec=infer(model,frames(packet,target,sups),out);status='PASS'
   else:rec=json.loads((out/'INFERENCE.json').read_text());status='REUSED'
   hero.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(sups),status=status,output_dir=str(out),seconds=rec.get('seconds'),raw_faces=rec.get('raw_faces'),tuple_sha=hashlib.sha256((g+'|'+v+'|'+target+'|'+';'.join(sups)).encode()).hexdigest()[:16]))
   trace(g,v,'hero','rf-m2f5-hero-native','native/hero.py::infer',[str(O/'clean_labels'/g_v) for g_v in []],[str(out)],status,{'target':target,'supports':sups})
  except Exception as e:
   hero.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(sups),status='FAIL',error=repr(e),output_dir=str(out)));print('HEROFAIL',g,v,target,e,flush=True);continue
  # A2B against all supports
  raw=np.load(out/'RAW_NATIVE_MESH.npz');V=raw['V'];F=raw['F'];ta=np.load(packet['views'][target]['cache']);K=np.asarray(ta['K'],float);rn,_,_=native_rgb_labels(ta['RGB'],ta['labels'],K);Cv=rn[raw['uv'][:,1],raw['uv'][:,0]]/255.
  for B in sups:
   b=np.load(packet['views'][B]['cache']);BK=np.asarray(b['K'],float);Bpose=packet['cameras'][B];pred=rp.render(V,F,Cv,BK,Bpose,np.eye(4),'R5' if '_R5_' in g else 'R10');met,mae,common=rp.evaluate(pred,np.asarray(b['RGB']),load_clean(g,v,B));met.update(group_id=g,video_id=v,target_id=target,support_id=B,target_B_camera_used=True,source_mesh=str(out/'RAW_NATIVE_MESH.npz'),status='GATED_NEW_HERO');a2b.append(met)
  print('HERO',n,'/',len(uni),g,v,'pairs',len(a2b),flush=True)
 pd.DataFrame(hero).to_csv(O/'hero/HERO_EXECUTION_RESULTS.csv',index=False);pd.DataFrame(a2b).to_csv(O/'evaluation/A_TO_B_METRICS.csv',index=False)
 # M2F6 uses the same renderer for retained baselines and current real outputs.
 for g in sorted(set(x['group_id'] for x in hero if x['status']!='FAIL')):
  for v in sorted(set(x['video_id'] for x in hero if x['group_id']==g and x['status']!='FAIL')):
   result=render_existing_video(O,O,g,v)
   trace(g,v,'six_view','rf-m2f5-six-view','_mesh_renderer.py::actual_mesh_image',
         [x['path'] for x in result['source_meshes']],[result['image']],'PASS',
         {'cad_kind':result['cad_kind'],'surface_count':result['surface_count'],'scale_bar_mm':5.})
 print('DONE hero',len(hero),'a2b',len(a2b))

def main_m2f6(args):
 global O,M2F6
 M2F6=True;O=pathlib.Path(args.output_root).resolve()
 groups=[x for x in args.groups.split(',') if x];videos=[x.zfill(3) for x in args.videos.split(',') if x]
 if not groups or not videos:raise ValueError('EXPLICIT_GROUPS_AND_VIDEOS_REQUIRED')
 (O/'hero').mkdir(parents=True,exist_ok=True);(O/'evaluation').mkdir(parents=True,exist_ok=True)
 for kind in ('R5','R10'):
  source=WS/'runs/m2e_historical_method_integration/cad'/f'{kind}.npz'
  dest=O/'cad'/f'{kind}.npz';dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=hashlib.sha256(source.read_bytes()).hexdigest():
   raise ValueError(f'CAD_HASH_MISMATCH {kind}')
  if not dest.exists():shutil.copy2(source,dest)
 code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WS,text=True).strip()
 run_id='M2F6-UNIFIED-OBSERVATION-001';hero=[];a2b=[];ready=[]
 hero_csv=O/'hero/HERO_EXECUTION_RESULTS.csv';a2b_csv=O/'evaluation/A_TO_B_METRICS.csv'
 for g in groups:
  for v in videos:
   try:
    packet_dir=final_packet_path(O,g,v);selection=O/'selection'/f'{g}_{v}.csv'
    if not selection.is_file():raise ValueError('MISSING_FINAL_SELECTION')
    packet=verify_w0_packet(packet_dir,WS)
    rows=pd.read_csv(selection)
    if not rows['ready'].any():raise ValueError('NO_READY_TARGETS')
    ready.append((g,v,packet,rows))
   except Exception as exc:
    reason=str(exc);hero.append(dict(group_id=g,video_id=v,target_id='',support_ids='',
      status='NOT_EVALUABLE',reason=reason,run_id=run_id,code_commit=code))
    trace(g,v,'hero','rf-m2f5-hero-native','native/hero.py::infer',[],[],
          'NOT_EVALUABLE',{'reason':reason})
 pd.DataFrame(hero).to_csv(hero_csv,index=False)
 if not ready:
  pd.DataFrame(columns=['group_id','video_id','target_id','support_id','status']).to_csv(a2b_csv,index=False)
  print('NO_READY_VIDEOS',flush=True);return
 cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text())
 sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
 model,model_receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],
   json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text()))
 write_json(O/'hero/MODEL_RECEIPT.json',model_receipt)
 for g,v,packet,rows in ready:
  trace(g,v,'hero_model','rf-m2f5-hero-native','native/hero.py::load_official',
        [cfg['checkpoint']],[str(O/'hero/MODEL_RECEIPT.json')],'PASS',
        {'model_receipt_sha256':hashlib.sha256((O/'hero/MODEL_RECEIPT.json').read_bytes()).hexdigest()})
  for r in rows.to_dict('records'):
   target=str(r['target_id']);supports=str(r.get('support_ids','')).split(';')
   if not bool(r['ready']):
    hero.append(dict(group_id=g,video_id=v,target_id=target,support_ids=r.get('support_ids',''),
      status='NOT_EVALUABLE',reason='T13_INSUFFICIENT_SUPPORT',run_id=run_id,code_commit=code))
    pd.DataFrame(hero).to_csv(hero_csv,index=False);continue
   out=O/'hero'/g/v/target
   try:
    if (out/'HERO_native.npz').exists():raise ValueError('FORMAL_OUTPUT_ALREADY_EXISTS')
    actual=verified_m2f6_frames(packet,target,supports,O)
    result,receipt=infer_with_receipt(model,actual,out,run_id,code,g,v)
    hero.append(dict(group_id=g,video_id=v,target_id=target,support_ids=';'.join(supports),
      status='PASS',output_dir=str(out),seconds=result.get('seconds'),
      raw_faces=result.get('raw_faces'),tuple_sha=receipt['tuple_sha256'],
      W0_sha256=hashlib.sha256(pathlib.Path(packet['w0_path']).read_bytes()).hexdigest(),
      source_video_sha256=packet['source_video_sha256'],run_id=run_id,code_commit=code))
    trace(g,v,'hero','rf-m2f5-hero-native','native/hero.py::infer',
      [str(out/'TUPLE_INPUT_RECEIPT.json'),packet['w0_path']],[str(out/'HERO_native.npz'),str(out/'RAW_NATIVE_MESH.npz')],
      'PASS',{'target':target,'supports':supports,'tuple_sha256':receipt['tuple_sha256']})
    pd.DataFrame(hero).to_csv(hero_csv,index=False)
   except Exception as exc:
    reason=repr(exc);hero.append(dict(group_id=g,video_id=v,target_id=target,
      support_ids=';'.join(supports),status='FAIL',reason=reason,output_dir=str(out),
      run_id=run_id,code_commit=code))
    trace(g,v,'hero','rf-m2f5-hero-native','native/hero.py::infer',[],[],
      'FAIL',{'target':target,'reason':reason})
    pd.DataFrame(hero).to_csv(hero_csv,index=False);print('HERO_FAIL',g,v,target,reason,flush=True)
    continue
   try:
    with np.load(out/'RAW_NATIVE_MESH.npz') as raw:
     V,F,uv=raw['V'],raw['F'],raw['uv']
    A=actual[0];clean_rgb,_,_=native_rgb_labels(A['RGB'],A['labels'],A['K'])
    Cv=clean_rgb[uv[:,1],uv[:,0]]/255.
    for B in supports:
     b=next(x for x in actual if x['id']==B)
     pred=rp.render(V,F,Cv,b['K'],b['c2w_mm'],np.eye(4),'R5' if '_R5_' in g else 'R10')
     met,_,_=rp.evaluate(pred,b['RGB'],b['labels'])
     met.update(group_id=g,video_id=v,target_id=target,support_id=B,
       target_B_camera_used=True,source_mesh=str(out/'RAW_NATIVE_MESH.npz'),
       tuple_sha=receipt['tuple_sha256'],status='PASS',run_id=run_id,code_commit=code)
     a2b.append(met)
    trace(g,v,'a2b','rf-m2f5-a2b-native','reprojection.py::render/evaluate',
      [str(out/'RAW_NATIVE_MESH.npz'),str(out/'TUPLE_INPUT_RECEIPT.json')],[str(a2b_csv)],
      'PASS',{'target':target,'supports':supports})
   except Exception as exc:
    a2b.append(dict(group_id=g,video_id=v,target_id=target,support_id='',
      status='NOT_EVALUABLE',reason=repr(exc),tuple_sha=receipt['tuple_sha256'],
      run_id=run_id,code_commit=code))
    trace(g,v,'a2b','rf-m2f5-a2b-native','reprojection.py::render/evaluate',[],[],
      'NOT_EVALUABLE',{'target':target,'reason':repr(exc)})
   pd.DataFrame(a2b).to_csv(a2b_csv,index=False)
   print('HERO',g,v,target,'pairs',len(a2b),flush=True)
  if any(x['group_id']==g and x['video_id']==v and x['status']=='PASS' for x in hero):
   try:
    result=render_existing_video(O,O,g,v)
    trace(g,v,'six_view','rf-m2f5-six-view','_mesh_renderer.py::actual_mesh_image',
      [x['path'] for x in result['source_meshes']],[result['image']],'PASS',
      {'cad_kind':result['cad_kind'],'surface_count':result['surface_count'],'scale_bar_mm':5.})
   except Exception as exc:
    trace(g,v,'six_view','rf-m2f5-six-view','_mesh_renderer.py::actual_mesh_image',
      [],[],'FAIL',{'reason':repr(exc)})
    print('SIX_VIEW_FAIL',g,v,repr(exc),flush=True)
 pd.DataFrame(hero).to_csv(hero_csv,index=False)
 pd.DataFrame(a2b if a2b else [dict(status='NOT_EVALUABLE')]).to_csv(a2b_csv,index=False)
 print('DONE hero',len(hero),'a2b',len(a2b),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--m2f6',action='store_true')
 ap.add_argument('--output-root',default='runs/m2f6_unified/formal_001')
 ap.add_argument('--groups',default='');ap.add_argument('--videos',default='004,005')
 args=ap.parse_args();main_m2f6(args) if args.m2f6 else main()
