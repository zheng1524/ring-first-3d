#!/usr/bin/env python3
"""M2F8 V6-GENERALIZED adapter. Calls frozen V6/V5 source; no core algorithm copy."""
import sys,json,hashlib,runpy,argparse,traceback,ast,subprocess,datetime
from pathlib import Path
import cv2,numpy as np,pandas as pd
WS=Path('/home/liu/ring_first_3d_workspace');BASE=WS/'runs/m2f8_v6_general';INP=BASE/'current_inputs';RUN_ID=''
V6=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction');V6S=V6/'scripts'
V5=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v5_geometry_crossvideo');V5S=V5/'scripts'
DXY=Path('/home/liu/new-polyp-dxy');GROUPS=['GP_Ip_12.0mm_closed_R10_single_refY','GP_Ip_20.0mm_closed_R10_single_refY','GP_IIa_14.0mm_closed_R10_single_refY','GP_Ip_8.8mm_closed_R5_single_refY','GP_Is_14.0mm_closed_R5_single_refY']
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=1,default=str)+'\n')
def trace(run,stage,status,inputs=(),outputs=(),extra=None):
 run=Path(run);p=run/'RUN_TRACE.jsonl';p.parent.mkdir(parents=True,exist_ok=True)
 files=lambda ps:{str(Path(x).resolve()):h(x) if Path(x).is_file() else None for x in ps}
 rec=dict(run_id=RUN_ID+'-'+run.name,stage=stage,status=status,
          utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
          code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[1],text=True).strip(),
          input_sha256=files(inputs),output_sha256=files(outputs))
 if extra:rec.update(extra)
 with p.open('a') as f:f.write(json.dumps(rec,sort_keys=True,default=str)+'\n');f.flush()
 return rec
def ring_r(g):return 3.1 if '_R5_' in g else 5.6
def raw_video_paths(raw_root,group,wanted):
 return [p for p in sorted(Path(raw_root).glob(f'{group}_*.mp4'))
         if p.stem.rsplit('_',1)[-1] in wanted]
def prepare_raw_subprocess(group,video,source,run):
 """Reuse M2F6 preparation without contaminating V5's historical module names."""
 worktree=Path(__file__).resolve().parents[1]
 child=("import sys; from pathlib import Path; from tools import m2f5_unified as p; "
        "p.O=Path(sys.argv[1]); p.M2F6=True; p.trace=lambda *a,**k: None; "
        "p.prepare_one_m2f6(sys.argv[2],Path(sys.argv[3]))")
 command=[sys.executable,'-c',child,str(INP),group,str(source)]
 log=Path(run)/'RAW_PREP.log';log.parent.mkdir(parents=True,exist_ok=True)
 trace(run,'raw_prepare','STARTED',[source],[],{'entrypoint':'m2f5_unified.prepare_one_m2f6','process':'isolated'})
 with log.open('w') as output:
  result=subprocess.run(command,cwd=worktree,stdout=output,stderr=subprocess.STDOUT,check=False)
 prepared=INP/'prepared'/f'{group}_{video}'
 if result.returncode or not (prepared/'PREPARED.json').is_file():
  trace(run,'raw_prepare','EXECUTION_ERROR',[source],[log],{'returncode':result.returncode})
  raise RuntimeError(f'RAW_PREP_FAILED returncode={result.returncode}; log={log}')
 trace(run,'raw_prepare','PASS',[source],[prepared/'PREPARED.json',log],{'process':'isolated'})
 return prepared
def ring_status_by_id(records):
 out={}
 for row in records:
  key=row['source']
  if key in out:raise ValueError('DUPLICATE_RING_OBSERVATION '+key)
  out[key]=row
 return out

def adapt_reference_lookups(source,reference_index,heldout_index,expected):
 """Bind only V6's protocol-frame lookups to explicit current ledger indices."""
 source=Path(source);tree=ast.parse(source.read_text(),filename=str(source));counts={'reference':0,'heldout':0}
 class Adapter(ast.NodeTransformer):
  def visit_Compare(self,node):
   self.generic_visit(node)
   if (len(node.ops)!=1 or not isinstance(node.ops[0],ast.Eq) or len(node.comparators)!=1 or
       not isinstance(node.left,ast.Subscript) or not isinstance(node.left.value,ast.Name) or
       node.left.value.id!='a' or not isinstance(node.left.slice,ast.Constant) or
       node.left.slice.value!='raw_frame' or not isinstance(node.comparators[0],ast.Constant)):
    return node
   value=node.comparators[0].value
   if value not in (459,516):return node
   key='reference' if value==459 else 'heldout';counts[key]+=1
   name='_M2F9_REFERENCE_INDEX' if key=='reference' else '_M2F9_HELDOUT_INDEX'
   return ast.copy_location(ast.Compare(left=ast.Name(id='i',ctx=ast.Load()),ops=[ast.Eq()],
                                        comparators=[ast.Name(id=name,ctx=ast.Load())]),node)
 tree=ast.fix_missing_locations(Adapter().visit(tree))
 if counts!=expected:raise ValueError(f'REFERENCE_LOOKUP_CONTRACT {source.name} {counts} != {expected}')
 receipt=dict(source=str(source),source_sha256=h(source),adapted_ast_sha256=hashlib.sha256(ast.dump(tree).encode()).hexdigest(),
              reference_index=int(reference_index),heldout_index=int(heldout_index),replacements=counts)
 return tree,receipt

def new_run_state(run_id,code_commit,config_sha256,raw_video):
 raw=Path(raw_video).resolve()
 return dict(run_id=run_id,route_id='rf-m2f9-v6-generalized@1',code_commit=code_commit,
             config_sha256=config_sha256,raw_video=str(raw),raw_video_sha256=h(raw),stages=[])

def record_stage(state,name,input_path,output_path):
 inp=Path(input_path).resolve();out=Path(output_path).resolve()
 if any(s['stage']==name for s in state['stages']):raise ValueError('DUPLICATE_STAGE '+name)
 if state['stages'] and h(inp)!=state['stages'][-1]['output_sha256']:
  raise ValueError('INPUT_PARENT_MISMATCH '+name)
 state['stages'].append(dict(stage=name,status='completed',input_path=str(inp),input_sha256=h(inp),
                             output_path=str(out),output_sha256=h(out),
                             finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))

def verify_run_state(state,run_id,code_commit,config_sha256):
 if (state.get('run_id'),state.get('code_commit'),state.get('config_sha256'))!=(run_id,code_commit,config_sha256):
  raise ValueError('RUN_STATE_IDENTITY_MISMATCH')
 raw=Path(state['raw_video'])
 if not raw.is_file() or h(raw)!=state['raw_video_sha256']:raise ValueError('RAW_SHA_MISMATCH')
 previous=None;seen=set()
 for item in state['stages']:
  if item['stage'] in seen:raise ValueError('DUPLICATE_STAGE '+item['stage'])
  seen.add(item['stage'])
  inp=Path(item['input_path']);out=Path(item['output_path'])
  if not inp.is_file() or h(inp)!=item['input_sha256'] or (previous and item['input_sha256']!=previous):
   raise ValueError('INPUT_SHA_MISMATCH '+item['stage'])
  if not out.is_file() or h(out)!=item['output_sha256']:
   raise ValueError('OUTPUT_SHA_MISMATCH '+item['stage'])
  previous=item['output_sha256']
 return True

def classify_outputs(root,camera_status):
 """Keep every native prediction even when validation or packaging is absent."""
 root=Path(root);cases=[]
 for name in ('MVS_cases.json','MVS_supported_cases.json'):
  path=root/'inputs'/name
  if path.is_file():cases+=json.loads(path.read_text())
 errors={}
 for name in ('MVS005_runs.json','MVS005_supported_runs.json'):
  path=root/'metrics'/name
  if path.is_file():
   for row in json.loads(path.read_text()):
    if not row.get('success',False):errors[row['tag']]=row.get('failure','HERO_EXECUTION_ERROR')
 out={}
 for case in cases:
  tag=case['tag'];native=root/'raw'/f'{tag}.npz';surface=root/'predictions'/f'{tag}_surface.npz';mesh=root/'meshes'/f'{tag}_Polyp.ply'
  validated=camera_status.get(tag)=='VALIDATED'
  insufficient='fewer than three supported source cameras' in errors.get(tag,'')
  status=('PACKAGED_MESH' if native.is_file() and surface.is_file() and mesh.is_file() else
          'VALIDATED_HERO' if native.is_file() and validated else
          'RAW_HERO' if native.is_file() else
          'NOT_EVALUABLE' if insufficient else
          'EXECUTION_ERROR' if tag in errors else 'NOT_EVALUABLE')
  out[tag]=dict(status=status,camera_status=camera_status.get(tag,'UNKNOWN'),
                raw_hero_path=str(native) if native.is_file() else None,
                mesh_path=str(mesh) if mesh.is_file() else None,
                mesh_state='PACKAGED' if status=='PACKAGED_MESH' else 'MISSING_MESH_PREREQUISITE',
                reason='SUPPORT_INSUFFICIENT' if insufficient else errors.get(tag) if status=='EXECUTION_ERROR' else None,
                execution_error=errors.get(tag))
 return out

def summarize_native_metrics(targets):
 def aggregate(keys):
  result=[]
  for name,part in targets.groupby(keys,dropna=False,sort=True):
   identity=name if isinstance(name,tuple) else (name,)
   raw=part[part.raw_sha256.notna()];pack=raw[raw.execution_status=='PACKAGED_MESH'];validated=raw[raw.camera_status=='VALIDATED']
   def median(frame,col):return float(frame[col].median()) if len(frame) and frame[col].notna().any() else float('nan')
   row=dict(zip(keys,identity));row.update(target_count=len(part),raw_count=len(raw),
       validated_raw_count=len(validated),packaged_count=len(pack),
       unfiltered_ratio_median=median(raw,'ring_ratio_median'),
       unfiltered_mae_median_mm=median(raw,'ring_mae_mm'),
       validated_ratio_median=median(validated,'ring_ratio_median'),
       validated_mae_median_mm=median(validated,'ring_mae_mm'),
       packaged_ratio_median=median(pack,'ring_ratio_median'),
       packaged_mae_median_mm=median(pack,'ring_mae_mm'))
   if keys==['group_id']:row['video_count']=part.video_id.nunique()
   result.append(row)
  return pd.DataFrame(result)
 return aggregate(['group_id','video_id']),aggregate(['group_id'])

def audit_native_runs(source_root,destination):
 """Read every existing native V6 depth, including unvalidated and unmeshed cases."""
 import open3d as o3d
 source_root=Path(source_root).resolve();destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
 trace(destination,'native_audit','STARTED',[source_root],[],{'selection':'all_cases_no_posthoc_filter'})
 scenes={};cad_hashes={}
 for kind in ('R5','R10'):
  cad=WS/'runs/m2f5_unified/cad'/f'{kind}.npz';cad_hashes[kind]=h(cad)
  with np.load(cad) as a:vertices=np.asarray(a['V'],np.float32);faces=np.asarray(a['F'],np.uint32)
  scene=o3d.t.geometry.RaycastingScene(nthreads=2);scene.add_triangles(o3d.core.Tensor(vertices),o3d.core.Tensor(faces));scenes[kind]=scene
 rows=[];inputs={}
 for root in sorted(source_root.glob('*_*')):
  ledger_path=root/'inputs/ledger005.json'
  if not ledger_path.is_file():continue
  inputs[str(ledger_path)]=h(ledger_path);ledger=json.loads(ledger_path.read_text())
  group,video=root.name.rsplit('_',1);kind='R5' if '_R5_' in group else 'R10'
  val=root/'metrics/local_validation.json';camera_status={}
  if val.is_file():
   d=json.loads(val.read_text());versions={x['version']:x for x in d['versions']};primary=versions.get(d['primary'])
   if primary:
    per=primary['per_frame']
    for case_name in ('MVS_cases.json','MVS_supported_cases.json'):
     case_path=root/'inputs'/case_name
     if case_path.is_file():
      inputs[str(case_path)]=h(case_path)
      for case in json.loads(case_path.read_text()):camera_status[case['tag']]=per[case['reference']]['status']
  statuses=classify_outputs(root,camera_status)
  for tag,item in statuses.items():
   row=dict(group_id=group,video_id=video,ring=kind,tag=tag,
            execution_status=item['status'],camera_status=item['camera_status'],reason=item['reason'],
            raw_sha256=None,raw_frame=None,ring_ratio_median=float('nan'),ring_mae_mm=float('nan'))
   native=root/'raw'/f'{tag}.npz'
   if native.is_file():
    inputs[str(native)]=h(native)
    with np.load(native) as z:
     i=int(z['reference']);a=ledger[i];label=cv2.imread(a['Mask_path'],0)
     if label is None or h(a['Mask_path'])!=a['Mask_SHA256'] or h(a['RGB_path'])!=a['RGB_SHA256']:
      raise ValueError('AUDIT_INPUT_HASH '+tag)
     if str(z['geometry_status']) not in ('LOCAL005_MODEL_PREDICTED_PREVIEW','LOCAL005_GEOMETRY_SCREENED','LOCAL005_GEOMETRY_SCREENED_STILL_NO_GT'):
      raise ValueError('AUDIT_GEOMETRY_STATUS '+tag)
     measure=native_depth_metrics(z['depth_mm'],z['K_index_native'],z['c2w'][i],label,scenes[kind])
     row.update(measure,raw_sha256=inputs[str(native)],raw_frame=int(a['source_raw_frame']),
                native_K_sha256=hashlib.sha256(np.ascontiguousarray(z['K_index_native']).tobytes()).hexdigest(),
                camera_sha256=hashlib.sha256(np.ascontiguousarray(z['c2w'][i]).tobytes()).hexdigest())
     if measure['polyp_centroid_mm'] is not None:
      row.update(zip(('polyp_centroid_x_mm','polyp_centroid_y_mm','polyp_centroid_z_mm'),measure['polyp_centroid_mm']))
   rows.append(row)
  trace(destination,'native_audit_video','PASS',[ledger_path],[native for native in (root/'raw').glob('*.npz')],
        {'group_id':group,'video_id':video,'cases':len(statuses),'raw':sum((root/'raw'/f'{tag}.npz').is_file() for tag in statuses)})
 targets=pd.DataFrame(rows);videos,groups=summarize_native_metrics(targets)
 targets.to_csv(destination/'TARGET_METRICS.csv',index=False);videos.to_csv(destination/'VIDEO_METRICS.csv',index=False);groups.to_csv(destination/'GROUP_METRICS.csv',index=False)
 write(destination/'AUDIT_INPUT_RECEIPT.json',dict(run_id=RUN_ID,source_root=str(source_root),cad_sha256=cad_hashes,
      input_sha256=inputs,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[1],text=True).strip()))
 trace(destination,'native_audit','PASS',[destination/'AUDIT_INPUT_RECEIPT.json'],
       [destination/'TARGET_METRICS.csv',destination/'VIDEO_METRICS.csv',destination/'GROUP_METRICS.csv'],
       {'cases':len(targets),'raw':int(targets.raw_sha256.notna().sum())})
 return targets,videos,groups

def compare_hero_adapters(source_run,tag,destination):
 """Rerun only M2F6 adapter on an exact V6 four-view raw tuple."""
 source_run=Path(source_run).resolve();destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
 trace(destination,'adapter_compare','STARTED',[source_run/'inputs/ledger005.json',source_run/'raw'/f'{tag}.npz'],[],{'tag':tag})
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
 from ring_first_3d.mainline.input_identity import tuple_receipt
 from ring_first_3d.mainline.native.hero import load_official,infer
 cases=[]
 for name in ('MVS_cases.json','MVS_supported_cases.json'):
  path=source_run/'inputs'/name
  if path.is_file():cases+=json.loads(path.read_text())
 matches=[c for c in cases if c['tag']==tag]
 if len(matches)!=1:raise ValueError('ADAPTER_CASE_IDENTITY '+tag)
 c=matches[0];ledger=json.loads((source_run/'inputs/ledger005.json').read_text())
 primary=json.loads((source_run/'predictions/local005_primary.json').read_text())['primary_version']
 with np.load(source_run/f'predictions/local005_camera_{primary}.npz') as a:poses=np.asarray(a['c2w'])
 frames=[]
 for i in [c['reference']]+c['sources']:
  a=ledger[i]
  if h(a['RGB_path'])!=a['RGB_SHA256'] or h(a['Mask_path'])!=a['Mask_SHA256']:
   raise ValueError('ADAPTER_FRAME_HASH '+a['id'])
  frames.append(dict(id=a['id'],RGB=cv2.imread(a['RGB_path'])[:,:,::-1].copy(),
                     labels=cv2.imread(a['Mask_path'],0),K=np.asarray(a['K'],float),c2w_mm=poses[i]))
 receipt=tuple_receipt(True,frames,RUN_ID,subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[1],text=True).strip())
 v6_receipt=json.loads((source_run/'inputs'/f'TUPLE_{tag}.json').read_text())
 if receipt['tuple_sha256']!=v6_receipt['tuple_sha256']:raise ValueError('ADAPTER_TUPLE_MISMATCH')
 with np.load(source_run/'raw'/f'{tag}.npz') as a:
  if int(a['reference'])!=c['reference'] or not np.array_equal(a['sources'],c['sources']) or not np.array_equal(a['c2w'],poses):
   raise ValueError('ADAPTER_V6_CAMERA_MISMATCH')
  if not np.array_equal(a['K_full'],frames[0]['K']):raise ValueError('ADAPTER_V6_K_MISMATCH')
  v6_depth=np.asarray(a['depth_mm'],float);v6_K=np.asarray(a['K_index_native'],float)
 write(destination/'SHARED_TUPLE_RECEIPT.json',receipt)
 trace(destination,'adapter_tuple','VERIFIED',[source_run/'inputs'/f'TUPLE_{tag}.json',source_run/'raw'/f'{tag}.npz'],[destination/'SHARED_TUPLE_RECEIPT.json'],
       {'tuple_sha256':receipt['tuple_sha256']})
 cfg=json.loads((WS/'mainline/configs/SITE.local.json').read_text())
 sys.path[:0]=[str(x) for x in cfg.get('readonly_dependency_paths',[])]
 model,model_receipt=load_official(cfg['mvs_root'],cfg['checkpoint'],cfg['dino_root'],
    json.loads((WS/'src/ring_first_3d/mainline/native/upstream_source_lock.json').read_text()))
 write(destination/'MODEL_RECEIPT.json',model_receipt)
 trace(destination,'adapter_model','PASS',[cfg['checkpoint']],[destination/'MODEL_RECEIPT.json'],
       {'checkpoint_sha256':model_receipt.get('checkpoint_SHA256')})
 output=destination/'m2f6_hero';infer(model,frames,output)
 trace(destination,'adapter_infer','PASS',[destination/'SHARED_TUPLE_RECEIPT.json'],[output/'HERO_native.npz'],{'tag':tag})
 with np.load(output/'HERO_native.npz') as a:m2_depth=np.asarray(a['depth_mm'],float);m2_K=np.asarray(a['K_index_native'],float)
 if m2_depth.shape!=v6_depth.shape:raise ValueError('ADAPTER_NATIVE_SHAPE_MISMATCH')
 valid=np.isfinite(m2_depth)&np.isfinite(v6_depth)&(m2_depth>0)&(v6_depth>0)
 delta=abs(m2_depth[valid]-v6_depth[valid]);result=dict(run_id=RUN_ID,source_run=str(source_run),tag=tag,
       source_raw_sha256=h(source_run/'raw'/f'{tag}.npz'),m2f6_raw_sha256=h(output/'HERO_native.npz'),
       tuple_sha256=receipt['tuple_sha256'],pixels=int(valid.sum()),
       native_K_max_abs=float(np.max(abs(m2_K-v6_K))),
       depth_abs_median_mm=float(np.median(delta)) if len(delta) else float('nan'),
       depth_abs_p95_mm=float(np.quantile(delta,.95)) if len(delta) else float('nan'),
       depth_abs_max_mm=float(np.max(delta)) if len(delta) else float('nan'),
       depth_exact_fraction=float(np.mean(delta==0)) if len(delta) else float('nan'))
 write(destination/'ADAPTER_EQUIVALENCE.json',result)
 trace(destination,'adapter_compare','PASS',[output/'HERO_native.npz',source_run/'raw'/f'{tag}.npz'],
       [destination/'ADAPTER_EQUIVALENCE.json'],result)
 return result

def select_v6_reference(rows,rings,edges,ring_counts):
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
 from tools.run_w0_camera import select_reference
 raw=[int(a['raw_frame']) for a in rows]
 ref,receipt=select_reference(raw,rings,edges,ring_counts)
 held=max((i for i in range(len(raw)) if i!=ref),key=lambda i:(abs(raw[i]-raw[ref]),-i))
 return ref,held,dict(receipt,heldout_index=held,heldout_raw_frame=raw[held],
                      heldout_policy='largest_raw_time_distance_from_reference')

def native_depth_metrics(depth_mm,K_native,c2w_mm,labels,scene):
 """Existing CAD axial-ray metric on every raw HERO prediction, before selection."""
 import open3d as o3d
 z=np.asarray(depth_mm,float);K=np.asarray(K_native,float);pose=np.asarray(c2w_mm,float)
 mask=cv2.resize(np.asarray(labels,dtype=np.uint8),(z.shape[1],z.shape[0]),interpolation=cv2.INTER_NEAREST)
 yy,xx=np.nonzero((mask==2)&np.isfinite(z)&(z>0))
 uv=np.c_[xx,yy,np.ones(len(xx))];direction=(uv@np.linalg.inv(K).T)@pose[:3,:3].T
 rays=np.c_[np.broadcast_to(pose[:3,3],direction.shape),direction].astype(np.float32)
 hits=scene.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy() if len(rays) else np.empty(0)
 good=np.isfinite(hits)&(hits>0);hero=z[yy[good],xx[good]];cad=hits[good];ratio=hero/cad
 yp,xp=np.nonzero((mask==1)&np.isfinite(z)&(z>0))
 up=np.c_[xp,yp,np.ones(len(xp))]
 points=pose[:3,3]+((up@np.linalg.inv(K).T)*z[yp,xp,None])@pose[:3,:3].T if len(up) else np.empty((0,3))
 return dict(ring_pixels=int(len(hero)),ring_ratio_median=float(np.median(ratio)) if len(ratio) else float('nan'),
             ring_ratio_mae=float(np.mean(abs(ratio-1))) if len(ratio) else float('nan'),
             ring_mae_mm=float(np.mean(abs(hero-cad))) if len(hero) else float('nan'),
             ring_signed_median_mm=float(np.median(hero-cad)) if len(hero) else float('nan'),
             polyp_pixels=int(len(points)),polyp_centroid_mm=points.mean(0).tolist() if len(points) else None,
             polyp_bbox_min_mm=points.min(0).tolist() if len(points) else None,
             polyp_bbox_max_mm=points.max(0).tolist() if len(points) else None)

def invoke_adapted_v6(module,source,reference_index,heldout_index,expected,top_level=False):
 tree,receipt=adapt_reference_lookups(source,reference_index,heldout_index,expected)
 if top_level:
  namespace={'__name__':'m2f9_v6_support','__file__':str(source),
             '_M2F9_REFERENCE_INDEX':reference_index,'_M2F9_HELDOUT_INDEX':heldout_index}
  exec(compile(tree,str(source),'exec'),namespace)
 else:
  functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main']
  if len(functions)!=1:raise ValueError('V6_MAIN_CONTRACT '+str(source))
  module.__dict__.update(_M2F9_REFERENCE_INDEX=reference_index,_M2F9_HELDOUT_INDEX=heldout_index)
  exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),module.__dict__)
  module.main()
 return receipt

def prep_input(g,v,root):
 root=Path(root);m=json.loads((root/'PREPARED.json').read_text());run=BASE/'v6'/f'{g}_{v}'
 source=Path(m['video_path'])
 if not source.is_file() or h(source)!=m['video_sha256']:raise ValueError('RAW_VIDEO_HASH')
 candidate_path=Path(m['candidate_manifest'])
 if h(candidate_path)!=m['candidate_manifest_sha256']:raise ValueError('CANDIDATE_MANIFEST_HASH')
 candidates={a['view']:a for a in json.loads(candidate_path.read_text())['candidates']}
 for d in ['inputs','observations','predictions','metrics','raw','meshes','scenes','visualizations']:(run/d).mkdir(parents=True,exist_ok=True)
 ((run/'scripts').unlink() if (run/'scripts').is_symlink() or (run/'scripts').exists() else None);(run/'scripts').symlink_to(V6S, target_is_directory=True)
 (run/'v5raw').mkdir(parents=True,exist_ok=True)
 ((run/'v5raw'/'scripts').unlink() if (run/'v5raw'/'scripts').is_symlink() or (run/'v5raw'/'scripts').exists() else None);(run/'v5raw'/'scripts').symlink_to(V5S, target_is_directory=True)
 rows=[];clean_root=INP/'clean_labels'/f'{g}_{v}'
 for q in m['views']:
  expected=candidates[q['view']];cache=Path(q['cache']);clean=clean_root/(q['view']+'.npz')
  if h(cache)!=expected['cache_sha256']:raise ValueError('CACHE_HASH '+q['view'])
  if not clean.is_file() or h(clean)!=expected['clean_labels_sha256']:raise ValueError('CLEAN_LABEL_HASH '+q['view'])
  with np.load(cache) as z:rgb=np.asarray(z['RGB']);K=np.asarray(z['K'],float)
  with np.load(clean) as z:labels=np.asarray(z['labels'])
  array_sha=lambda x:hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
  if array_sha(rgb)!=expected['RGB_sha256'] or array_sha(labels)!=expected['clean_mask_sha256'] or array_sha(K)!=expected['K_sha256']:
   raise ValueError('INPUT_ARRAY_HASH '+q['view'])
  if rgb.shape!=(360,640,3) or labels.shape!=(360,640) or K.shape!=(3,3) or not np.allclose(K,m['K']):
   raise ValueError('INPUT_GEOMETRY '+q['view'])
  rgbp=run/'inputs'/f'{q["view"]}.png';maskp=run/'inputs'/f'{q["view"]}_mask.png'
  if not cv2.imwrite(str(rgbp),rgb[:,:,::-1]) or not cv2.imwrite(str(maskp),labels):raise OSError('INPUT_PNG_WRITE')
  rows.append(dict(id=q['view'],source=source.name,source_id=v,raw_frame=int(q['raw_frame']),
                   source_raw_frame=int(q['raw_frame']),RGB_path=str(rgbp),Mask_path=str(maskp),
                   RGB_SHA256=h(rgbp),Mask_SHA256=h(maskp),K=K.tolist(),K_SHA256=array_sha(K),
                   cache_SHA256=h(cache),clean_labels_SHA256=h(clean),original16=False,
                   role='M2F9 RAW current M2F6 selection plus DXY clean'))
 if not rows:raise ValueError('NO_SELECTED_OBSERVATIONS')
 write(run/'inputs/ledger005.json',rows)
 write(run/'inputs/INPUT_IDENTITY.json',dict(raw_video=str(source),raw_video_sha256=h(source),
       prepared_sha256=h(root/'PREPARED.json'),candidate_manifest_sha256=h(candidate_path),
       selected=[dict(id=a['id'],raw_frame=a['raw_frame'],RGB_SHA256=a['RGB_SHA256'],
                      Mask_SHA256=a['Mask_SHA256'],K_SHA256=a['K_SHA256']) for a in rows]))
 write(run/'config.json',json.loads((V6/'config.json').read_text()))
 ref=len(rows)//2;held=len(rows)-1 if len(rows)>1 else ref
 if held==ref and len(rows)>1:held=0
 return run,rows,ref,held

def source_modules(ring_R):
 sys.path[:0]=[str(V6S),str(V5S),str(DXY/'src')]
 import g5_common,g5_common as g5
 # parameterize the one authoritative V5/V6 Ring formula; no second formula
 orig=g5.contour_project
 def cp(pose,n=256,K0=None):
  if K0 is None:K0=g5.K
  return g5.contours(pose[:3,3],pose[:3,:3],K0,R=ring_R,r=.6,n=n)
 g5.contour_project=cp
 import v6_common
 v6_common.ring_residual=g5.torus_residual;v6_common.contours=cp
 import ring_candidates_new,local_ring_sfm,track005
 local_ring_sfm.ring_residual=g5.torus_residual;local_ring_sfm.contours=cp
 return dict(g5=g5,v6=v6_common,ns=ring_candidates_new.ns,lba=local_ring_sfm,track=track005)

def build_ring(run,rows,ring_R,mods):
 # V5 DXY observations on current raw labels, then the existing V5 seed/solve path with R5/R10 parameter
 v5root=run/'v5raw';v5root.mkdir(parents=True,exist_ok=True);(v5root/'inputs').mkdir(exist_ok=True);(v5root/'metrics').mkdir(exist_ok=True);(v5root/'observations').mkdir(exist_ok=True);(v5root/'predictions').mkdir(exist_ok=True)
 write(v5root/'inputs/ledger.json',rows);write(v5root/'config.json',json.loads((V5/'config.json').read_text()))
 files={str(p.resolve()):h(p) for p in [v5root/'config.json',v5root/'inputs/ledger.json',run/'inputs/INPUT_IDENTITY.json']+[Path(a[k]) for a in rows for k in ('RGB_path','Mask_path')]}
 write(v5root/'metrics/freeze_inputs.json',dict(files=files,GT_selection=False,historical_measurement_fallback=0))
 import g5_common,ring_observations
 g5_common.R=v5root;ring_observations.R=v5root
 ring_observations.main()
 import ring_candidates_new
 from branch_seed_policy import diverse_four
 ns=ring_candidates_new.ns;ns['rad']=ring_R;ns['tube']=.6
 obs={a['id']:dict(np.load(v5root/'observations'/f'{a["id"]}.npz')) for a in rows}
 st=ring_status_by_id(json.loads((v5root/'metrics/ring_observations.json').read_text()))
 K=np.asarray(json.loads((V5/'config.json').read_text())['K'],float);records=[]
 for a in rows:
  ob=obs[a['id']];ob['mask']=ob['ring_mask'];ns.update(K=K,cfg=dict(seed_depth_factors=[.85,1.,1.2],seed_inclinations_deg=[0,35,60],seed_azimuths_deg=[0,90,180,270],seed_retain=4,max_nfev=100,huber_px=1.,numerical_success_max_training_px=3.))
  def residual(x,ref,observations):
   cen,Q=ns['decode'](x,ref);po=np.eye(4);po[:3,:3]=Q.T;po[:3,3]=-Q.T@cen;return g5_common.torus_residual(po,ob,K0=K)
  ns['residual']=residual;seeds=ns['image_seeds'](ob);e=st[a['id']]['geometry'].get('centerline')
  if e:
   z=ring_R*K[0,0]/e['major_radius'];xy=(np.array([e['cx'],e['cy']])-K[:2,2])/np.diag(K)[:2];inc=np.arccos(np.clip(e['minor_radius']/e['major_radius'],0,1));az=np.deg2rad(e['angle_deg'])
   for sign in [-1,1]:seeds.append(np.r_[xy,np.log(z),sign*inc*np.cos(az),sign*inc*np.sin(az)])
  seeds=diverse_four(seeds,lambda x:float(np.mean(2*(np.sqrt(1+residual(x,np.eye(4),[ob])**2)-1))))
  fit=ns['solve']([ob],np.eye(4),seeds);allfit=[{k:v for k,v in fit.items() if k not in ['alternatives','ambiguity_alternatives']}]+fit['alternatives'];cands=[]
  for x in allfit:
   Q=np.array(x['Q']);c=np.array(x['center']);po=np.eye(4);po[:3,:3]=Q.T;po[:3,3]=-Q.T@c;cands.append(dict(**x,c2r=po.tolist(),heldout=g5_common.stats(g5_common.torus_residual(po,ob,'held')),azimuth_gauge='arbitrary representative'))
  records.append(dict(id=a['id'],source_id=a['source_id'],K=K,candidates=cands,rotation_symmetry_unresolved=True,no_gt_inputs=True))
 write(run/'predictions/ring_candidates005.json',records)
 # V6 observations aliases
 for a in rows:
  src=v5root/'observations'/f'{a["id"]}.npz';np.savez_compressed(run/'observations'/f'{a["id"]}_ring.npz',**dict(np.load(src)))
 write(run/'metrics/segmentation_ring005.json',[dict(id=a['id'],Ring_pixels=int((cv2.imread(a['Mask_path'],0)==2).sum())) for a in rows])
 v6=mods['v6'];v6.R=run;v6.V5=v5root;v6.REPO=Path('/home/liu/polyp_research');v6.freeze('ring_inputs',[run/'inputs/ledger005.json',run/'inputs/INPUT_IDENTITY.json',run/'metrics/segmentation_ring005.json',run/'predictions/ring_candidates005.json']+[Path(a['Mask_path']) for a in rows]+list((run/'observations').glob('*_ring.npz')))
 return records

def checkpoint(run,state,name,input_path,output_path):
 record_stage(state,name,input_path,output_path)
 write(run/'RUN_STATE.json',state)
 trace(run,name,'PASS',[input_path],[output_path],{'stage_output_sha256':h(output_path)})

def hero_input_receipts(run,rows,cases_path):
 """Record actual V6 PNG/K/camera tuple before the original HERO module runs."""
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
 from ring_first_3d.mainline.input_identity import tuple_receipt
 cases=json.loads(Path(cases_path).read_text());primary=json.loads((run/'predictions/local005_primary.json').read_text())['primary_version']
 with np.load(run/f'predictions/local005_camera_{primary}.npz') as z:poses=np.asarray(z['c2w'])
 for c in cases:
  tag=c['tag']
  if len(c['sources'])!=3:
   trace(run,'hero_input','NOT_EVALUABLE',[cases_path],[],{'target':tag,'reason':'SUPPORT_INSUFFICIENT'})
   continue
  frames=[]
  for i in [c['reference']]+c['sources']:
   a=rows[i];rgb=cv2.imread(a['RGB_path'],cv2.IMREAD_COLOR)[:,:,::-1].copy();lab=cv2.imread(a['Mask_path'],0)
   if h(a['RGB_path'])!=a['RGB_SHA256'] or h(a['Mask_path'])!=a['Mask_SHA256']:
    raise ValueError('HERO_INPUT_FILE_HASH '+a['id'])
   frames.append(dict(id=a['id'],RGB=rgb,labels=lab,K=np.asarray(a['K'],float),c2w_mm=poses[i]))
  receipt=tuple_receipt(True,frames,RUN_ID+'-'+run.name,
                       subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[1],text=True).strip())
  path=run/'inputs'/f'TUPLE_{tag}.json';write(path,receipt)
  trace(run,'hero_input','VERIFIED',[cases_path,run/f'predictions/local005_camera_{primary}.npz']+[a['RGB_path'] for a in [rows[i] for i in [c['reference']]+c['sources']]]+[a['Mask_path'] for a in [rows[i] for i in [c['reference']]+c['sources']]],
        [path],{'target':tag,'tuple_sha256':receipt['tuple_sha256']})

def run_v6(run,rows,mods,ring_records,state):
 for mod in (mods['track'],mods['lba']):
  mod.R=run;mod.V5=run/'v5raw';mod.REPO=Path('/home/liu/polyp_research')
 mods['v6'].R=run
 mods['track'].main();checkpoint(run,state,'tracks',run/'predictions/ring_candidates005.json',run/'observations/tracks005.npz')
 with np.load(run/'observations/tracks005.npz') as z:tracks={k:z[k] for k in z.files}
 with np.load(run/'observations/pairs005.npz') as z:pairs={k:z[k] for k in z.files}
 edges=mods['lba'].pair_data(tracks,pairs)
 ring_counts=[len(np.load(run/'observations'/f"{a['id']}_ring.npz")['q_train']) for a in rows]
 ref,held,reference=select_v6_reference(rows,ring_records,edges,ring_counts)
 write(run/'inputs/REFERENCE_RECEIPT.json',reference)
 trace(run,'reference','PASS',[run/'observations/tracks005.npz',run/'predictions/ring_candidates005.json'],[run/'inputs/REFERENCE_RECEIPT.json'],
       {'reference_index':ref,'heldout_index':held,'raw_frame_unchanged':True})
 receipts=[]
 try:
  receipts.append(invoke_adapted_v6(mods['lba'],V6S/'local_ring_sfm.py',ref,held,{'reference':1,'heldout':0}))
  if not any(x['success'] for x in json.loads((run/'metrics/local005_solver.json').read_text())):
   raise RuntimeError('NO_SUCCESSFUL_V6_INITIALIZATION')
  checkpoint(run,state,'local_ba',run/'observations/tracks005.npz',run/'metrics/local005_solver.json')
 except Exception as e:
  trace(run,'local_ba','EXECUTION_ERROR',[run/'observations/tracks005.npz'],[],{'reason':repr(e),'traceback':traceback.format_exc()})
  raise
 sys.path.insert(0,str(V6S));import validate_select
 validate_select.R=run;validate_select.V5=run/'v5raw';validate_select.contours=mods['v6'].contours
 receipts.append(invoke_adapted_v6(validate_select,V6S/'validate_select.py',ref,held,{'reference':1,'heldout':1}))
 checkpoint(run,state,'validation',run/'metrics/local005_solver.json',run/'metrics/local_validation.json')
 write(run/'inputs/V6_INDEX_ADAPTER.json',receipts)
 try:
  receipts.append(invoke_adapted_v6(None,V6S/'select_supported_views.py',ref,held,{'reference':1,'heldout':1},top_level=True))
  checkpoint(run,state,'support',run/'metrics/local_validation.json',run/'inputs/MVS_supported_cases.json')
 except (ValueError,StopIteration) as e:
  trace(run,'support','NOT_EVALUABLE',[run/'metrics/local_validation.json'],[],{'reason':'SUPPORT_INSUFFICIENT','detail':repr(e)})
 write(run/'inputs/V6_INDEX_ADAPTER.json',receipts)
 import run_mvs005,run_mvs005_supported,package_surfaces
 for module in (run_mvs005,run_mvs005_supported,package_surfaces):
  module.R=run;module.V5=run/'v5raw';module.REPO=Path('/home/liu/polyp_research')
 previous=Path(state['stages'][-1]['output_path'])
 for name,case_name,module,metric in [('hero_raw','MVS_cases.json',run_mvs005,'MVS005_runs.json'),
                                       ('hero_supported','MVS_supported_cases.json',run_mvs005_supported,'MVS005_supported_runs.json')]:
  case_path=run/'inputs'/case_name
  if not case_path.is_file():continue
  cases=json.loads(case_path.read_text());conflicts=[c['tag'] for c in cases if (run/'raw'/f"{c['tag']}.npz").exists()]
  if conflicts:
   trace(run,name,'EXECUTION_ERROR',[case_path],[],{'reason':'EXISTING_OUTPUT_CONFLICT','targets':conflicts})
   continue
  hero_input_receipts(run,rows,case_path)
  try:
   module.main()
   metric_path=run/'metrics'/metric
   if metric_path.is_file():checkpoint(run,state,name,previous,metric_path);previous=metric_path
  except Exception as e:
   trace(run,name,'EXECUTION_ERROR',[case_path],[],{'reason':repr(e),'traceback':traceback.format_exc()})
 supported=run/'inputs/MVS_supported_cases.json'
 if supported.is_file():
  cases=json.loads(supported.read_text());missing=[c['tag'] for c in cases if not (run/'raw'/f"{c['tag']}.npz").is_file()]
  if len(cases)!=2 or missing or not (run/'metrics/MVS005_supported_runs.json').is_file():
   trace(run,'mesh','NOT_EVALUABLE',[supported],[],{'reason':'MISSING_MESH_PREREQUISITE','missing':missing})
  else:
   try:
    package_surfaces.main();checkpoint(run,state,'mesh',previous,run/'metrics/surfaces005.json')
   except Exception as e:trace(run,'mesh','EXECUTION_ERROR',[supported],[],{'reason':repr(e),'traceback':traceback.format_exc()})
 else:trace(run,'mesh','NOT_EVALUABLE',[],[],{'reason':'MISSING_MESH_PREREQUISITE'})
 validation=json.loads((run/'metrics/local_validation.json').read_text());primary=validation['primary']
 per=next(x for x in validation['versions'] if x['version']==primary)['per_frame'];cam_status={}
 for case_file in ('MVS_cases.json','MVS_supported_cases.json'):
  path=run/'inputs'/case_file
  if path.is_file():
   for c in json.loads(path.read_text()):cam_status[c['tag']]=per[c['reference']]['status']
 statuses=classify_outputs(run,cam_status);write(run/'metrics/EXECUTION_STATUS.json',statuses)
 trace(run,'classification','PASS',[run/'metrics/local_validation.json'],[run/'metrics/EXECUTION_STATUS.json'],
       {'counts':{s:sum(x['status']==s for x in statuses.values()) for s in ('RAW_HERO','VALIDATED_HERO','PACKAGED_MESH','NOT_EVALUABLE','EXECUTION_ERROR')}})
 return statuses

def main():
 global BASE,INP,RUN_ID
 ap=argparse.ArgumentParser();ap.add_argument('--run-id',required=True);ap.add_argument('--groups',default=','.join(GROUPS));ap.add_argument('--videos',default='004,005');ap.add_argument('--limit',type=int,default=0);ap.add_argument('--stage',choices=('prepare','all'),default='all');ap.add_argument('--verify-resume',action='store_true');ap.add_argument('--audit-source');ap.add_argument('--compare-run');ap.add_argument('--compare-tag');a=ap.parse_args()
 import re
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):raise SystemExit('INVALID_RUN_ID')
 RUN_ID=a.run_id;BASE=WS/'runs/m2f9_v6_general'/RUN_ID;INP=BASE/'current_inputs'
 code=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[1],text=True).strip()
 cfg_sha=h(V6/'config.json')
 if a.verify_resume:
  states=sorted((BASE/'v6').glob('*/RUN_STATE.json'))
  if not states:raise SystemExit('RUN_STATE_MISSING')
  for p in states:
   state=json.loads(p.read_text());verify_run_state(state,state['run_id'],code,cfg_sha)
   print('RUN_STATE_OK',state['run_id'],len(state['stages']),flush=True)
  return
 if BASE.exists():raise SystemExit('RUN_ID_ALREADY_EXISTS '+str(BASE))
 BASE.mkdir(parents=True)
 if a.compare_run:
  if not a.compare_tag:raise SystemExit('COMPARE_TAG_REQUIRED')
  result=compare_hero_adapters(a.compare_run,a.compare_tag,BASE/'adapter_compare')
  print('ADAPTER_COMPARE_DONE',result['tag'],result['pixels'],result['depth_abs_p95_mm'],flush=True)
  return
 if a.audit_source:
  targets,videos,groups=audit_native_runs(a.audit_source,BASE/'analysis')
  print('AUDIT_DONE',len(targets),int(targets.raw_sha256.notna().sum()),len(videos),len(groups),flush=True)
  return
 raw_root=WS/'smart_endoscope_20260805 (1)'/'raw';groups=[x for x in a.groups.split(',') if x];wanted={x.zfill(3) for x in a.videos.split(',') if x};attempted=0
 for g in groups:
  paths=raw_video_paths(raw_root,g,wanted);found={p.stem.rsplit('_',1)[-1] for p in paths}
  for missing in sorted(wanted-found):
   run=BASE/'v6'/f'{g}_{missing}'
   trace(run,'raw_source','NOT_EVALUABLE',[raw_root],[],{'reason':'MISSING_RAW_VIDEO'})
  for path in paths:
   v=path.stem.rsplit('_',1)[-1];run=BASE/'v6'/f'{g}_{v}'
   state=new_run_state(RUN_ID+'-'+run.name,code,cfg_sha,path)
   write(run/'RUN_STATE.json',state)
   try:
    prepared=prepare_raw_subprocess(g,v,path,run)
    checkpoint(run,state,'prepare',path,prepared/'PREPARED.json')
    if a.stage=='all':
     run,rows,_,_=prep_input(g,v,prepared)
     checkpoint(run,state,'input_bridge',prepared/'PREPARED.json',run/'inputs/INPUT_IDENTITY.json')
     mods=source_modules(ring_r(g));records=build_ring(run,rows,ring_r(g),mods)
     checkpoint(run,state,'ring',run/'inputs/INPUT_IDENTITY.json',run/'predictions/ring_candidates005.json')
     run_v6(run,rows,mods,records,state)
    print('V6_DONE',g,v,run,flush=True)
   except Exception as e:
    trace(run,'video','EXECUTION_ERROR',[path],[],{'reason':repr(e),'traceback':traceback.format_exc()})
    write(run/'metrics/EXECUTION_FAILURE.json',dict(group=g,video=v,reason=repr(e),traceback=traceback.format_exc()))
    print('V6_FAIL',g,v,repr(e),flush=True)
   attempted+=1
   if a.limit and attempted>=a.limit:break
  if a.limit and attempted>=a.limit:break
 print('DONE',attempted,BASE,flush=True)
if __name__=='__main__':main()
