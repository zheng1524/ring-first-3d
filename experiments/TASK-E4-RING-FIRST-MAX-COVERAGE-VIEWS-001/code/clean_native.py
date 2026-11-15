"""Frozen017 face classification and018 gap rule; no new thresholds or vertex changes."""
from geometry_io import *
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import distance_transform_edt
P17=REPO/'experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017';PHC=Path('/home/liu/ring_first_3d/experiments');LEG=OLD/'experiments'
def reuse(path,names):extract(path,names,globals())
reuse(LEG/'ring_first_v1/scripts/common.py',['unproject'])
reuse(PHC/'TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001/code/run.py',['face_components','edge_counts'])
def cfg():return load(P17/'config/PROTOCOL.json')['inherited_density']
reuse(PHC/'TASK-PHASEC-DENSITY-MULTIGROUP-001/code/density.py',['features'])
reuse(P17/'code/common017.py',['native_grid'])
reuse(P17/'code/analyze017.py',['mapped_labels','get_source','topology','classify','analyze','components_summary','coverage'])
reuse(P17/'code/gap017.py',['patch_plane','gap_edges'])
def cast(s,uv,K,T):return cast_points(s,uv,T,K)

def one(rec):
 root=N/'hero_fit'/rec['id'];start=time.time();status=dict(id=rec['id'],group=rec['group'],view_id=rec['view_id'],rank=rec['rank'],variant=rec['variant'],success=False)
 try:
  assert rec['success'],rec.get('error');conf=next(c for c in load(N/'config/FOUR_GROUP_INPUTS.json')if c['group']==rec['group']);rv=np.load(conf['ring']['path']);ring=scene(rv['V'],rv['F']);native=np.load(rec['native']);z=native['depth_mm'];K=native['K_index_native'];T=native['reference_pose_mm'];t=load(P17/'config/PROTOCOL.json')['thresholds'];row=dict(native_depth=rec['native'],K=K,Kn=K,T=T,Mask=str(root/'NATIVE_LABELS.png'),archive_pack=rec['pack'],archive_mesh=rec['mesh'],archive_points=rec['points']);s=get_source(row,'ARCHIVE_RAW');f,state,reason,top=analyze(s,ring,t);ns=get_source(row,'NATIVE_GRID');gaps,grows=gap_edges(z,ns['native_labels'],K,T,ns['P'],ns['F'],ns['uv'],t);V,F,uv=s['P'],s['F'],s['uv'];pix=s['native_pixel_id'];confirmed=np.zeros(len(F),bool)
  for i,j in [(0,1),(1,2),(2,0)]:confirmed|=np.array([tuple(sorted(p))in gaps for p in pix[F[:,[i,j]]]])
  shape=(f['triangle_quality']<t['needle_quality'])|(f['normal_angle_deg']>t['neighbor_angle_deg'])|(f['normal_coherence']<t['normal_coherence']);material=f['CAD_inside_samples']>=t['ring_inside_samples_min'];rej=confirmed&shape&((f['boundary_distance_native_px']<=t['edge_native_px'])|material)&f['native_mask_supported']&(~f['CAD_occluded']|material)&(f['native_depth_jump_mm']>t['native_depth_jump_mm'])&(f['perspective_stretch']>t['stretch_perspective']);state[rej]=2;reason[confirmed]|=1<<13;reason[rej]|=1<<14;trust=state==0;raw=np.load(root/'RAW_NATIVE_MESH.npz');assert np.array_equal(F,raw['F'])and np.max(abs(V-raw['V']))<1e-5
  # Authoritative rawfloat64 coordinates from native unprojection. Classifier's
  # PLY float32 reader is only a diagnosis; retain exact original generated V.
  V=raw['V'];normal=trimesh.Trimesh(V,F,process=False).face_normals.copy();cent=V[F].mean(1);normal[((T[:3,3]-cent)*normal).sum(1)<0]*=-1;ev=dict(V=V,F=F,uv=uv,original_face_id=np.arange(len(F)),state=state,reason_bits=reason,native_pixel_id=pix,K=K,T=T,**f);np.savez_compressed(root/'FACE_EVIDENCE.npz',**ev)
  for name,mask in [('TRUSTED',trust),('UNCERTAIN',state==1),('REJECTED',state==2),('UNKNOWN',state==3)]:
   np.savez_compressed(root/(name+'_HERO.npz'),V=V,F=F[mask],original_face_id=np.flatnonzero(mask),uv=uv,native_pixel_id=pix,K=K,T=T,face_normals=normal[mask]);
   if mask.any():trimesh.Trimesh(V,F[mask],process=False).export(root/(name+'_HERO.ply'))
  lab=np.asarray(Image.open(root/'NATIVE_LABELS.png'));y,x=np.nonzero((lab==1)&np.isfinite(z)&(z>0));uv=np.c_[x,y];hit=cast(scene(V,F),uv,K,T);fid=hit['primitive_ids'].numpy().astype(int);found=fid<len(F);cz=cast(ring,uv,K,T)['t_hit'].numpy();X=unproject(z[y,x],T,uv,K);sd=ring.compute_signed_distance(o3d.core.Tensor(X.astype(np.float32)),nsamples=3).numpy();tr=np.zeros(len(uv),bool);tr[found]=trust[fid[found]];valid=tr&(z[y,x]<cz-.05)&(sd>=-.02);norm=np.full((len(uv),3),np.nan);norm[found]=normal[fid[found]];np.savez_compressed(root/'OBS_TRUSTED.npz',uv=uv[valid],pixel_id=y[valid]*640+x[valid],z=z[y[valid],x[valid]],X=X[valid],normal=norm[valid],face_id=fid[valid],K=K,T=T,weight=np.ones(valid.sum()),cad_z=cz[valid],native_shape=z.shape);ar=trimesh.triangles.area(V[F]);counts={name:int((state==i).sum())for i,name in enumerate(['TRUSTED','UNCERTAIN','REJECTED','UNKNOWN'])};status.update(success=bool(valid.any()),original_faces=len(F),native_pixels=len(pix),trusted_native_observations=int(valid.sum()),state_counts=counts,area_mm2={name:float(ar[state==i].sum())for i,name in enumerate(['TRUSTED','UNCERTAIN','REJECTED','UNKNOWN'])},raw_area_mm2=float(ar.sum()),original_vertices_exact=True,interpolated_depth=0,original_face_IDs_unchanged=True,largest_component=components_summary(V,F,state!=2,ar),mask_first_surface=coverage(s,state!=2,ring),native_binding_error_px=s['identity_error_px'],confirmed_gap_edges=len(gaps),threshold_source=asset(P17/'config/PROTOCOL.json'))
 except Exception as e:status.update(error=repr(e),traceback=traceback.format_exc());print('CLEAN_FAIL',rec['id'],repr(e),flush=True)
 status['seconds']=time.time()-start;save('hero_fit/'+rec['id']+'/CLEANING.json',status);print('NATIVE_CLASSIFIED',rec['id'],status['success'],status.get('state_counts'),flush=True);return status

def main():
 records=[]
 for rec in load(N/'metrics/HERO_INFERENCE_RESULTS.json'):
  p=N/'hero_fit'/rec['id']/'CLEANING.json';records.append(load(p)if p.exists()else one(rec));save('metrics/HERO_CLEANING_RESULTS.json',records)
 freeze('provenance/NEW_HERO_CLASSIFICATION_FROZEN.json',[N/'hero_fit'/r['id']/'CLEANING.json'for r in records],GT=False);print('ALL_CLASSIFIED',len(records),flush=True)
if __name__=='__main__':main()
