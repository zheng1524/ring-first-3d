from common import *
import ast,traceback
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import distance_transform_edt
import open3d as o3d
P17=REPO/'experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017';LEG=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');PHC=Path('/home/liu/ring_first_3d/experiments')
def extract(p,names):
 nodes=[x for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)and x.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),globals())
extract(LEG/'ring_first_v1/scripts/common.py',['unproject'])
extract(PHC/'TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001/code/run.py',['face_components','edge_counts'])
def cfg():return load(P17/'config/PROTOCOL.json')['inherited_density']
extract(PHC/'TASK-PHASEC-DENSITY-MULTIGROUP-001/code/density.py',['features'])
extract(P17/'code/common017.py',['native_grid'])
extract(P17/'code/analyze017.py',['mapped_labels','get_source','topology','classify','analyze','components_summary','coverage'])
extract(P17/'code/gap017.py',['patch_plane','gap_edges'])
def cast(s,uv,K,T):
 ray=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;return s.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32)))
def main():
 plan=load(R/'config/VIEW_PLAN.json');records=[];t=load(P17/'config/PROTOCOL.json')['thresholds']
 for r in plan:
  cid=r['view_id'];root=R/('hero_fit'if r['role']=='FIT'else'holdout/hero')/cid;source=root/'SOURCE.json'
  if not source.exists():records.append(dict(group=r['group'],view_id=cid,role=r['role'],success=False,reason='INFERENCE_NOT_FINISHED'));continue
  rec=load(source);dest=root/'CLEANING.json'
  if dest.exists():records.append(load(dest));continue
  start=time.time();status=dict(group=r['group'],view_id=cid,role=r['role'],success=False)
  try:
   assert rec['success'],rec.get('failure');d=np.load(r['cache']);n=np.load(rec['native']);z=n['depth_mm'];A=np.diag([z.shape[1]/640,z.shape[0]/360,1.]);A[:2,2]=np.array([z.shape[1]/640,z.shape[0]/360])*.5-.5;Kn=A@d['K'];rp=R/'inputs'/r['group']/'RING.npz';rv=np.load(rp);ring=scene(rv['V'],rv['F'])
   # Exact017 original Raw label reuse is preferred when its native/mesh hashes match.
   if rec['reused']:
    p=P17/'final_results'/cid/'ARCHIVE_RAW/FACE_EVIDENCE.npz';ev=dict(np.load(p));assert sha(rec['native'])==sha(r['reuse']['native_depth'])and sha(rec['mesh'])==sha(r['reuse']['archive_mesh']);f={k:ev[k]for k in ['area_mm2','normal_coherence','incidence_min','CAD_inside_samples','CAD_occluded','boundary_distance_native_px']};P,F,uv,state=ev['V'],ev['F'],ev['uv'],ev['state'];label_source=asset(p)
   else:
    # Same017 classifier and once-frozen gap rule, original raw triangle subset only.
    row=dict(native_depth=rec['native'],K=d['K'],Kn=Kn,T=d['T'],Mask=r['meta']['Mask_source'],archive_pack=rec['pack'],archive_mesh=rec['mesh'],archive_points=rec['points']);s=get_source(row,'ARCHIVE_RAW');f,state,reason,top=analyze(s,ring,t);ns=get_source(row,'NATIVE_GRID');gaps,grows=gap_edges(z,ns['native_labels'],Kn,d['T'],ns['P'],ns['F'],ns['uv'],t);P,F,uv=s['P'],s['F'],s['uv'];px=s['native_pixel_id'];confirmed=np.zeros(len(F),bool)
    for i,j in [(0,1),(1,2),(2,0)]:confirmed|=np.array([tuple(sorted(p))in gaps for p in px[F[:,[i,j]]]])
    shape=(f['triangle_quality']<t['needle_quality'])|(f['normal_angle_deg']>t['neighbor_angle_deg'])|(f['normal_coherence']<t['normal_coherence']);material=f['CAD_inside_samples']>=t['ring_inside_samples_min'];rej=confirmed&shape&((f['boundary_distance_native_px']<=t['edge_native_px'])|material)&f['native_mask_supported']&(~f['CAD_occluded']|material)&(f['native_depth_jump_mm']>t['native_depth_jump_mm'])&(f['perspective_stretch']>t['stretch_perspective']);state[rej]=2;reason[confirmed]|=1<<13;reason[rej]|=1<<14
    ev=dict(V=P,F=F,uv=uv,original_face_id=np.arange(len(F)),state=state,reason_bits=reason,native_pixel_id=s['native_pixel_id'],K=d['K'],Kn=Kn,T=d['T'],**f);label_source=dict(rule=str(P17/'config/FINAL_CLEANING_RULE.json'),source017_code_SHA=sha(P17/'code/analyze017.py'),new_asset_labeled=True)
   # Unmodified original faces; real TRUSTED-only subset, not just recoloring.
   trust=state==0;normal=trimesh.Trimesh(P,F,process=False).face_normals.copy();C=P[F].mean(1);normal[((d['T'][:3,3]-C)*normal).sum(1)<0]*=-1
   np.savez_compressed(root/'FACE_EVIDENCE.npz',**ev);np.savez_compressed(root/'FULL_HERO.npz',V=P,F=F,original_face_id=np.arange(len(F)),uv=uv,K=d['K'],T=d['T']);np.savez_compressed(root/'TRUSTED_HERO.npz',V=P,F=F[trust],original_face_id=np.flatnonzero(trust),uv=uv,face_normals=normal[trust],K=d['K'],T=d['T']);trimesh.Trimesh(P,F[trust],process=False).export(root/'TRUSTED_HERO.ply')
   # All original native pixels are queried; no sparse256 surrogate. Labels come
   # from the source's first original Raw face, native z values never resampled.
   native_lab,_=mapped_labels(d['labels'],d['K'],Kn,z.shape);yy,xx=np.nonzero((native_lab==1)&np.isfinite(z)&(z>0));pix=np.c_[xx,yy];body=scene(P,F);hit=cast(body,pix,Kn,d['T']);fid=hit['primitive_ids'].numpy().astype(np.int64);found=fid<len(F);cad=cast(ring,pix,Kn,d['T'])['t_hit'].numpy();zh=z[yy,xx].astype(float);ray=np.c_[pix,np.ones(len(pix))]@np.linalg.inv(Kn).T;X=(ray*zh[:,None])@d['T'][:3,:3].T+d['T'][:3,3];sd=ring.compute_signed_distance(o3d.core.Tensor(X.astype(np.float32)),nsamples=3).numpy();eligible=found&(zh<cad-.05)&(sd>=-.02);tflag=np.zeros(len(pix),bool);tflag[found]=trust[fid[found]];flags=dict(FULL=eligible,TRUSTED=eligible&tflag)
   for kind,mask in flags.items():
    ix=np.flatnonzero(mask);np.savez_compressed(root/('OBS_'+kind+'.npz'),uv=pix[ix],pixel_id=yy[ix]*z.shape[1]+xx[ix],z=zh[ix],X=X[ix],normal=normal[fid[ix]],face_id=fid[ix],K=Kn,T=d['T'],weight=np.ones(len(ix)),cad_z=cad[ix],native_shape=z.shape)
   comp=face_components(F[trust]);area=trimesh.triangles.area(P[F]);ca=np.bincount(comp,weights=area[trust])if len(comp)else np.array([])
   status.update(success=bool(flags['TRUSTED'].any()),original_faces=len(F),trusted_faces=int(trust.sum()),trusted_area_mm2=float(area[trust].sum()),total_area_mm2=float(area.sum()),trusted_components=len(ca),largest_trusted_component_area_mm2=float(ca.max())if len(ca)else 0.,full_native_observations=int(flags['FULL'].sum()),trusted_native_observations=int(flags['TRUSTED'].sum()),source_CAD_occluded=int((zh>=cad-.05).sum()),source_CAD_material=int((sd<-.02).sum()),native_samples_total=len(pix),label_source=label_source,original_vertices_unchanged=True,seconds=time.time()-start,assets={k:asset(root/k)for k in ['FACE_EVIDENCE.npz','TRUSTED_HERO.npz','OBS_FULL.npz','OBS_TRUSTED.npz']})
  except Exception:status.update(reason=traceback.format_exc(),seconds=time.time()-start);print(status['reason'],flush=True)
  dest.write_text(json.dumps(clean(status),ensure_ascii=False,indent=2)+'\n');records.append(status);print('CLEAN018',cid,status['success'],status.get('trusted_native_observations'),flush=True)
 save('metrics/HERO_CLEANING_RESULTS.json',records)
if __name__=='__main__':main()
