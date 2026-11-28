"""M4-only post-registration Clean and common-coordinate asset interface."""
from context import *
from clean2 import mapping,verify_clean_identity
from ring_first_3d.multisurface.geometry import sample_mesh
from ring_first_3d.sim.geometry import transform
from ring_first_3d.v6_raw.trusted_restore import stats
import argparse,traceback
sys.path.append(str(ROOT/'experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001/code'))
from clean_after import one as original_clean_after

def clean_source(source,ordinal,out,TV):
 resource();verify_clean_identity();folder=out/'sources'/source['source_id'];folder.mkdir(parents=True,exist_ok=True)
 classifier={n:sha(ROOT/'src/ring_first_3d/mainline/native'/n)for n in ['cleaning.py','_clean_kernels.py','cleaning_protocol.json']}
 key=cache_key(dict(source=source,T=TV,classifier=classifier,adapter=sha(ROOT/'experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001/code/clean_after.py'),mapping=sha(ROOT/'src/ring_first_3d/v6_raw/surface_clean.py'),ordinal=ordinal))
 if (folder/'COMPLETE.json').exists():
  r=read(folder/'COMPLETE.json');assert r['cache_key']==key,'CLEAN_CACHE_MISMATCH';assert sha(r['selection_path'])==r['selection_sha256'];assert sha(r['raw_domain'])==r['raw_domain_sha256'];return r
 if (folder/'clean_M4').exists():
  isolate_incomplete(folder);folder.mkdir(parents=True)
 save(folder/'PREDICTION_FREEZE.json',dict(T=TV,registration_sha256=sha(out/'REGISTRATION.json'),cache_key=key))
 # Exact identity sources can reuse R1's own verified classification, relative to the same CAD.
 if np.array_equal(TV,np.eye(4)):
  old=FULL/'clean'/source['case']/source['tag'];r=read(old/'COMPLETE.json');assert r['raw_mesh_sha256']==source['mesh_sha256']and r['native_sha256']==source['native_sha256'];assert r['parents'][source['cad_path']]==source['cad_sha256'];assert r['parents'][str(Path(source['run'])/'CAMERA_COMPLETE.json')]==sha(Path(source['run'])/'CAMERA_COMPLETE.json');assert r['filter']=='F[state==0]'
  for n,h in classifier.items():assert r['parents'][n]==h
  ev=old/'FACE_EVIDENCE.npz';assert sha(ev)==r['retained_hashes'][str(ev)];e=dict(np.load(ev));info=mapping(source);V,F=info['V'],info['F'];assert np.array_equal(e['V'],V)and np.array_equal(e['F'],F);state=e['state'];assert np.array_equal(e['original_face_id'],np.arange(len(F)))
  sel=folder/'FACE_SELECTION.npz';np.savez_compressed(sel,state=state,reason_bits=e['reason_bits'],original_face_id=e['original_face_id'],trusted_original_face_id=np.flatnonzero(state==0),working_uv=info['uv'],native_pixel_id=info['raw']['native_pixel_id'])
  _,ids,bary=sample_mesh(V,F,CFG['surface_samples_per_source'],20261127+ordinal);domain=folder/'RAW_DOMAIN.npz';np.savez_compressed(domain,original_face_id=ids,bary=bary)
  raw=stats(V,F);trusted=stats(V,F[state==0]);rec=dict(source=source,status='COMPLETE',origin='REUSED_EXACT_IDENTITY_R1',upstream_receipt=str(old/'COMPLETE.json'),upstream_receipt_sha256=sha(old/'COMPLETE.json'),upstream_evidence_sha256=sha(ev),raw=raw,trusted=trusted,raw_faces=len(F),trusted_faces=int((state==0).sum()),raw_area_mm2=raw['area_mm2'],trusted_area_mm2=trusted['area_mm2'],selection_path=str(sel),selection_sha256=sha(sel),raw_domain=str(domain),T_local_to_global=TV,common_faces_additional_coordinate_change_mm=0.)
 else:
  # The scientific function is the unchanged, pinned R1 original, now called routinely for M4.
  adapted=dict(source,side='B');rec=original_clean_after(adapted,ordinal,folder,TV,method='M4');rec['source']=source
 rec.update(cache_key=key,raw_domain_sha256=sha(rec['raw_domain']),registration_method='M4',classifier=classifier);save(folder/'COMPLETE.json',rec);return rec

def outputs(g):
 out=group_out(g);asset,reg=verify_registration(out);before=sha(out/'REGISTRATION.json');freeze('OUTPUTS',out,[out/'REGISTRATION.json']);index=[];sources=[];videos=[]
 for v in asset['videos']:
  connection=reg['videos'][v['case']];t=connection['T'];entry=dict(case=v['case'],status=connection['status'],T_local_to_common=t,path_to_reference=connection['path'],local_camera=v['camera'],local_camera_sha256=v['camera_sha256'],common_cameras=None,camera_coordinate_frame=None)
  if t is not None:
   cams=dict(np.load(v['camera']));p=out/'cameras'/(v['case']+'.npz');p.parent.mkdir(exist_ok=True);globalcams=np.array(t)@cams['c2w'];export=dict(cams,c2w=globalcams,units='mm',coordinate_frame='COMMON')
   if 'points'in cams:export['points']=transform(cams['points'],np.array(t))
   np.savez_compressed(p,**export);entry.update(common_cameras=str(p),common_cameras_sha256=sha(p),camera_coordinate_frame='COMMON',landmark_coordinate_frame='COMMON',landmark_key='points',landmark_track_id_key='point_track_ids',landmark_track_namespace=v['case'])
  videos.append(entry)
 for ordinal,source in enumerate(asset['sources']):
  t=reg['videos'][source['case']]['T'];rec=dict(source=source,status='MISSING',origin='UNCONNECTED',error='NO_VIDEO_TRANSFORM')
  if t is not None:
   try:rec=clean_source(source,ordinal,out,np.array(t))
   except Exception as e:rec=dict(source=source,status='MISSING',origin='ERROR',error=repr(e),traceback=traceback.format_exc());print('CLEAN ERROR',source['source_id'],repr(e),flush=True)
  index.append(rec);save(out/'CLEAN_INDEX.json',index)
  sources.append(dict(source_id=source['source_id'],case=source['case'],tag=source['tag'],reference=source['reference'],target=source['raw_target'],support=source['raw_support'],raw_mesh=str(Path(source['run'])/'meshes'/(source['tag']+'_Polyp.ply')),raw_mesh_sha256=source['mesh_sha256'],native_depth=str(Path(source['run'])/'raw'/(source['tag']+'.npz')),native_sha256=source['native_sha256'],raw_coordinate_frame='LOCAL',T_local_to_common=t,connected=t is not None,clean_status=rec['status'],selection=rec.get('selection_path'),selection_sha256=rec.get('selection_sha256'),raw_domain=rec.get('raw_domain'),clean_rule='original F[state==0]; same original V after one rigid transform'))
  print('SOURCE',g,ordinal+1,'/',len(asset['sources']),rec['origin'],flush=True)
 landmarks=[]
 for e in reg['edges']:
  lm=np.load(Path(e['folder'])/'LANDMARKS.npz');p=out/'landmarks'/(e['parent'].rsplit('_',1)[-1]+'__'+e['child'].rsplit('_',1)[-1]+'.npz');p.parent.mkdir(exist_ok=True);points=[]
  for k,case in enumerate([e['parent'],e['child']]):
   tv=reg['videos'][case]['T'];points.append(transform(lm['xyz'][:,k],np.array(tv))if tv is not None else np.full_like(lm['xyz'][:,k],np.nan))
  np.savez_compressed(p,xyz=np.stack(points,1),fit=lm['fit'],held=lm['held'],coordinate_frame='COMMON',units='mm');landmarks.append(dict(path=str(p),sha256=sha(p),cases=[e['parent'],e['child']],independent_DLT_not_fused=True))
 assert len({s['source_id']for s in sources})==len(sources);assert before==sha(out/'REGISTRATION.json')
 save(out/'GROUP.json',dict(schema='R1_M4_COMMON_OBSERVATIONS_1',group=g,method='M4',registration_status=reg['status'],reference=reg['reference'],units='mm',scale=1,rule='C_global=T_v@C_local; X_global=T_v@X_local; preserve K, intravideo relative geometry and axial Z',videos=videos,all_video_states=asset['all_video_states'],sources=sources,landmarks=landmarks,CAD_fixed_in_reference=True,registration_sha256=before,body_fitting_started=False))
 # Actual consumer smoke check for every connected source; no optimization involved.
 from consume import load_source
 maxerr=0.;checked=0
 for s in sources:
  if s['clean_status']!='COMPLETE':continue
  data=load_source(out/'GROUP.json',s['source_id']);checked+=1;local=np.load(s['native_depth']);C=local['c2w'][s['reference']];G=data['c2w'][s['reference']];import trimesh
  mesh=trimesh.load(s['raw_mesh'],process=False);V=np.asarray(mesh.vertices);a=(V-C[:3,3])@C[:3,:3];b=(data['V']-G[:3,3])@G[:3,:3];maxerr=max(maxerr,float(np.max(abs(a-b)))if len(V)else 0.)
 assert maxerr<1e-7
 save(out/'CONSUMER_CHECK.json',dict(sources_loaded=checked,max_camera_xyz_and_axial_z_difference_mm=maxerr,transform_unchanged=True,vertices_original_and_face_selection_only=True));print('OUTPUTS',g,checked,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group');args=p.parse_args()
 for row in read(T/'config/INVENTORY.json')['groups']:
  g=row['group']
  if args.group and args.group!=g:continue
  try:outputs(g)
  except Exception as e:save(group_out(g)/'OUTPUT_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));print('OUTPUT FAILURE',g,repr(e),flush=True)
