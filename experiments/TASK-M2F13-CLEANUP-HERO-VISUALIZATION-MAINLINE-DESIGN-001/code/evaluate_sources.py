"""Evaluate every unique generated source with original CAD/A-to-B code; no refit."""
import ast,inspect,copy,traceback
import trimesh,cv2
from common import *
E=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
def extract(path,names,ns):
 tree=ast.parse(Path(path).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
# Original V6 topology contract: 360x640 interpolated z, Polyp mask, triangle axial-Z range <=.75mm.
mesh_ns=dict(np=np,trimesh=trimesh);extract(E/'ring_first_v1/scripts/common.py',['unproject'],mesh_ns);extract(E/'ring_first_v6_local_reconstruction/scripts/v6_common.py',['depth_mesh'],dict(mesh_ns,K=np.eye(3)))
# Select the unchanged Ring scoring prefix of the M2F12 evaluator, returning its diagnostics.
f=ast.parse(inspect.getsource(oldhero.evaluate)).body[0];body=[]
for node in f.body:
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='m'for t in node.targets):break
 body.append(node)
f.name='ring_only';f.body=body+ast.parse('return rm, d, np.where(common,abs(depth-cad),np.nan), rgb, labels, ns').body;ast.fix_missing_locations(f);ns=dict(oldhero.__dict__);exec(compile(ast.Module(body=[f],type_ignores=[]),__file__+'::original_ring_prefix','exec'),ns);ring_only=ns['ring_only']
plans=read(B/'PLANS_FROZEN.json')['plans'];hresults={r['source_id']:r for r in read(B/'H004_RESULTS.json')};v6=read(B/'V6_SOURCES.json');sources=[]
for p in plans:
 r=copy.deepcopy(p);r.update(formal=True,canonical=True,canonical_source_id=p['source_id'],alias_count=1,status=hresults[p['source_id']]['status'],native_path=str(Path(p['output'])/'HERO_native.npz'),mesh_path=str(Path(p['output'])/'RAW_NATIVE_MESH.npz'),representation='native_H004');sources.append(r)
sources += [copy.deepcopy(r)for r in v6 if r['canonical']]
aliases="--aliases" in sys.argv
if aliases:sources=[copy.deepcopy(r)for r in v6 if not r["canonical"]]
results=[]
for k,r in enumerate(sources):
 O=B/'source_evaluation'/r['source_id'];O.mkdir(parents=True,exist_ok=True)
 try:
  fs=oldhero.frames(r);assert combo_id(frame_identity(fs,r['raw_sha256']))==r['combo_id'];native=Path(r['native_path']);z=np.load(native)
  if 'reference_pose_mm'in z.files:
   q=O/'HERO_native.npz'
   if not q.exists():q.symlink_to(native)
  else:
   np.savez_compressed(O/'HERO_native.npz',depth_mm=z['depth_mm'],K_index_native=z['K_index_native'],reference_pose_mm=z['c2w'][int(z['reference'])])
  ring,errors,heat,rgb,labels,render_ns=ring_only(r,fs,O)
  ring.update(max_mm=float(errors.max())if len(errors)else None,over_5mm_count=int((errors>5).sum()),over_5mm_fraction=float((errors>5).mean())if len(errors)else None,valid_depth_fraction_is_numeric_only=True,CAD_common_coverage_is_camera_conditional=True)
  mesh_path=Path(r['mesh_path'])
  if not mesh_path.exists():
   assert r['route']=='V6';scope=dict(mesh_ns,K=fs[0]['K']);extract(E/'ring_first_v6_local_reconstruction/scripts/v6_common.py',['depth_mesh'],scope)
   m=scope['depth_mesh'](cv2.resize(z['depth_mm'].astype(float),(640,360),interpolation=cv2.INTER_LINEAR),fs[0]['labels']==1,fs[0]['c2w_mm'],fs[0]['RGB']);mesh_path=O/'ORIGINAL_V6_CONVERSION.ply';m.export(mesh_path);r['mesh_conversion']='original V6 function, linear native-to-work z, triangle axial-Z range <=.75mm; no new inference'
  if mesh_path.suffix=='.npz':
   m=np.load(mesh_path);V=m['V'];F=m['F'];uv=m['uv'].astype(int);colors=rgb[uv[:,1],uv[:,0]]/255.
  else:
   m=trimesh.load(mesh_path,process=False);V=np.asarray(m.vertices);F=np.asarray(m.faces);colors=np.asarray(m.visual.vertex_colors)[:,:3]/255.
  assert len(V)and len(F)and np.isfinite(V).all()and np.isfinite(fs[0]['c2w_mm']).all(),'NONFINITE_OR_EMPTY_MESH_OR_CAMERA'
  target=fs[1];pred=render_ns['render'](V,F,colors,target['K'],target['c2w_mm'],np.eye(4),'R10'if r['ring_inner_mm']==10 else'R5');ab,err,common=render_ns['evaluate'](pred,target['RGB'],target['labels']);ab.update(B_is_HERO_support=True,independent_holdout=False)
  np.savez_compressed(O/'DISPLAY_DIAGNOSTICS.npz',ring_heat_mm=heat,target_RGB=fs[0]['RGB'],target_Mask=fs[0]['labels'],B_RGB=target['RGB'],A_to_B_RGBA=pred['RGBA'],A_to_B_error=np.where(common,err,np.nan))
  r.update(renderable=True,status='RENDERABLE',mesh_path=str(mesh_path),mesh_sha256=sha(mesh_path),native_sha256=sha(native),ring=ring,a_to_b=ab,vertices=len(V),faces=len(F),bbox_min_mm=V.min(0).tolist(),bbox_max_mm=V.max(0).tolist(),vertex_color_source='actual target RGB; original vertex association',display_diagnostics=str(O/'DISPLAY_DIAGNOSTICS.npz'))
 except Exception as ex:r.update(renderable=False,status='NOT_RENDERABLE',failure=repr(ex),traceback=traceback.format_exc());print(r['traceback'],flush=True)
 save(O/'SOURCE_RESULT.json',r);results.append(r);save(B/('ALL_ALIAS_RESULTS.json' if aliases else 'ALL_UNIQUE_SOURCES.json'),results);print('SOURCE_EVAL',k+1,len(sources),r['source_id'],r['status'],flush=True)
save(T/('ALIAS_EVALUATION_SUMMARY.json' if aliases else 'SOURCE_EVALUATION_SUMMARY.json'),dict(total_unique=len(results),renderable=sum(x.get('renderable',False)for x in results),not_renderable=[dict(source_id=x['source_id'],reason=x.get('failure'))for x in results if not x.get('renderable')],evaluator_sha256=sha(P12/'code/hero_check.py'),reprojection_sha256=sha(oldhero.REPRO),V6_converter_sha256=sha(E/'ring_first_v6_local_reconstruction/scripts/v6_common.py'),no_refit_no_ICP_no_scale_no_face_filter_added=True))
