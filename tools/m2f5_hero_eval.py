#!/usr/bin/env python3
"""M2F5: HERO, Raw metric mesh, B-camera A-to-B and six-view for fresh 13-group selections."""
import sys,json,pathlib,hashlib,time
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
if __name__=='__main__':main()
