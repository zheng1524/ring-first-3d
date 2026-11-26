"""Only manifest/output adaptation of approved TRUSTED-only implementation."""
from common2 import *
import types,tempfile,trimesh
from ring_first_3d.v6_raw.surface_clean import mapped_input_for_source
from ring_first_3d.v6_raw.trusted_restore import trusted_subset,stats
from ring_first_3d.mainline.native.cleaning import classify_native
from ring_first_3d.mainline.native.geometry import unproject

def mapping(source):
 # Avoid route.legacy -> environment/cache/scheduler imports; unchanged mapping
 # still verifies exact original V/F using the exact V6 depth_mesh function.
 from ring_first_3d.v6_raw import route
 ns=original(V6/'v6_common.py',['depth_mesh'],dict(np=np,trimesh=trimesh,unproject=unproject,K=np.array([[490.,0,319.5],[0,490.,179.5],[0,0,1.]])))
 oldlegacy,oldbind=route.legacy,route.bind
 route.legacy=lambda:None;route.bind=lambda *a:{'v6':types.SimpleNamespace(depth_mesh=ns['depth_mesh'])}
 try:return mapped_input_for_source(source)
 finally:route.legacy,route.bind=oldlegacy,oldbind

def clean_one(group,ordinal,source,out,old):
 resource();key=source['side']+'__'+source['tag'];dest=out/'clean'/key;dest.mkdir(parents=True,exist_ok=False);start=stage_freeze('CLEAN',dest,[T/'config'/group/'ASSETS.json']);info=mapping(source);V,F=info['V'],info['F'];reuse=None
 for j,c in enumerate(old,1):
  if c['case']==source['case']and c['tag']==source['tag']:
   assert c['mesh_sha256']==source['mesh_sha256']and c['native_sha256']==source['native_sha256']and c['raw_support']==source['raw_support'];assert sha(c['camera_path'])==source['camera_sha256']and sha(c['cad_path'])==source['cad_sha256'];reuse=CLEAN_RUN/('source'+str(j));break
 if reuse:
  complete=read(reuse/'COMPLETE.json')
  for name in ['TRUSTED_ONLY.npz','FACE_EVIDENCE.npz','ORIGINAL_MAPPING.npz']:
   assert sha(reuse/name)==complete['outputs'][str(reuse/name)]
  e=dict(np.load(reuse/'FACE_EVIDENCE.npz'));m=np.load(reuse/'ORIGINAL_MAPPING.npz');a=np.load(reuse/'TRUSTED_ONLY.npz');assert np.array_equal(m['F'],F)and np.array_equal(m['V'],V);assert np.array_equal(a['F'],F[e['state']==0])and np.array_equal(a['V'],V);rec=read(reuse/'CLEANING.json');origin='REUSED'
 else:
  # This temporary output is ours, never an upstream directory. The unmodified
  # classifier writes diagnostics here; retain compact evidence instead of meshes.
  scratch=T/'runtime/scratch';scratch.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=scratch,prefix='clean_')as tmp:
   rec=classify_native(Path(tmp),source['cad_path'],mapped_input=info['payload']);e=dict(np.load(Path(tmp)/'FACE_EVIDENCE.npz'))
  origin='NEW'
 state=e['state'];assert np.array_equal(e['F'],F)and np.array_equal(e['original_face_id'],np.arange(len(F)));sub=trusted_subset(V,F,state);assert np.array_equal(sub['V'],V)and np.array_equal(sub['F'],F[sub['original_face_id']]);tri=V[F];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 np.savez_compressed(dest/'FACE_SELECTION.npz',state=state,reason_bits=e['reason_bits'],original_face_id=e['original_face_id'],trusted_original_face_id=sub['original_face_id'],working_uv=info['uv'],native_pixel_id=info['raw']['native_pixel_id'])
 # Stable raw triangle sample IDs and barycentric coordinates, independent of clean.
 from ring_first_3d.multisurface.geometry import sample_mesh
 _,ids,bary=sample_mesh(V,F,CFG['surface_samples_per_source'],20261127+ordinal);np.savez_compressed(dest/'RAW_DOMAIN.npz',original_face_id=ids,bary=bary)
 record=dict(source=source,origin=origin,reused_path=str(reuse)if reuse else None,classification=rec,raw=stats(V,F),trusted=stats(V,F[state==0]),raw_area_mm2=float(area.sum()),trusted_area_mm2=float(area[state==0].sum()),excluded_area_mm2=float(area[state!=0].sum()),raw_faces=len(F),trusted_faces=int((state==0).sum()),coordinate_change_max_mm=0.,vertices_preserved_by_original_reference=True,selection_path=str(dest/'FACE_SELECTION.npz'),selection_sha256=sha(dest/'FACE_SELECTION.npz'),raw_domain=str(dest/'RAW_DOMAIN.npz'))
 assert sha(info['meshpath'])==source['mesh_sha256']and sha(info['nativepath'])==source['native_sha256'];save(dest/'COMPLETE.json',record);print('CLEAN',group,key,origin,int((state==0).sum()),'/',len(F),flush=True)
 return record

def make_clean(group):
 asset=read(T/'config'/group/'ASSETS.json');out=RUN/'real'/group;old=read(CLEAN_T/'config/SOURCES_FROZEN.json')['cases'];index=[]
 for ordinal,source in enumerate(asset['sources']):
  try:record=clean_one(group,ordinal,source,out,old)
  except Exception as error:
   import traceback
   record=dict(source=source,status='MISSING',origin='FAILED',error=repr(error),traceback=traceback.format_exc());print('CLEAN FAILURE',group,source['tag'],repr(error),flush=True)
  index.append(record);save(out/'CLEAN_INDEX.json',index)
 return index
