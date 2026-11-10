"""One input-fidelity repair before R2, retaining the original R1 derivations."""
from clean018 import *
import shutil

def main():
 records=[];plan=load(R/'config/VIEW_PLAN.json')
 for r in plan:
  root=R/('hero_fit'if r['role']=='FIT'else'holdout/hero')/r['view_id'];dst=root/'OBS_FULL.npz';backup=root/'OBS_FULL_R1_RAW_WITNESS.npz'
  if not backup.exists():shutil.copyfile(dst,backup)
  cp=root/'CLEANING.json'
  if not(root/'CLEANING_R1.json').exists():shutil.copyfile(cp,root/'CLEANING_R1.json')
  before=sha(root/'OBS_TRUSTED.npz');ev=np.load(root/'FACE_EVIDENCE.npz');d=np.load(r['cache']);z=np.load(root/'HERO_native.npz')['depth_mm'];K=ev['Kn'];T=d['T'];lab,_=mapped_labels(d['labels'],d['K'],K,z.shape);yy,xx=np.nonzero((lab==1)&np.isfinite(z)&(z>0));uv=np.c_[xx,yy];zh=z[yy,xx].astype(float);rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;X=(rays*zh[:,None])@T[:3,:3].T+T[:3,3];rv=np.load(R/'inputs'/r['group']/'RING.npz');ring=scene(rv['V'],rv['F']);cad=cast(ring,uv,K,T)['t_hit'].numpy();sd=ring.compute_signed_distance(o3d.core.Tensor(X.astype(np.float32)),nsamples=3).numpy();valid=(zh<cad-.05)&(sd>=-.02)
  P,F=ev['V'],ev['F'];fid=cast(scene(P,F),uv,K,T)['primitive_ids'].numpy().astype(np.int64);found=fid<len(F);norm=trimesh.Trimesh(P,F,process=False).face_normals.copy();cc=P[F].mean(1);norm[((T[:3,3]-cc)*norm).sum(1)<0]*=-1;normals=np.full((len(uv),3),np.nan);normals[found]=norm[fid[found]];ix=np.flatnonzero(valid)
  np.savez_compressed(dst,uv=uv[ix],pixel_id=yy[ix]*z.shape[1]+xx[ix],z=zh[ix],X=X[ix],normal=normals[ix],face_id=np.where(found,fid,-1)[ix],K=K,T=T,weight=np.ones(len(ix)),cad_z=cad[ix],native_shape=z.shape)
  assert before==sha(root/'OBS_TRUSTED.npz')
  old=load(root/'CLEANING_R1.json');c=load(cp);c.update(full_native_observations=len(ix),full_R1_Raw_witness_observations=old['full_native_observations'],full_native_without_original_Raw_face=int((valid&~found).sum()),FULL_definition='all original native positive Polyp depths before CAD and not inside CAD, including original Raw-mesher orphan pixels; face_id=-1, normal=NaN if no original Raw witness',TRUSTED_unchanged_SHA256=before);c['assets']['OBS_FULL.npz']=asset(dst);cp.write_text(json.dumps(clean(c),ensure_ascii=False,indent=2)+'\n');records.append(dict(group=r['group'],view=r['view_id'],role=r['role'],old_full_N=old['full_native_observations'],new_full_N=len(ix),orphan_N=int((valid&~found).sum()),trusted_unchanged=True,full_SHA256=sha(dst)))
  print('FULL_REPAIRED',r['view_id'],old['full_native_observations'],len(ix),flush=True)
 from setup_arms018 import old_samples
 dest=R/'depth_observations_R1';dest.mkdir(exist_ok=True)
 for r in plan:
  if r['role']=='FIT':
   p=R/'depth_observations'/(r['view_id']+'.npz')
   if not(dest/p.name).exists():shutil.copyfile(p,dest/p.name)
   old_samples(r)
 p=R/'config/PROTOCOL.json';c=load(p);c['observations']='FULL: all legal native positive Polyp depths, no Raw-mesher filter. TRUSTED: additionally original Raw face witness labelled TRUSTED by017. Both native original depth values; no thinning.';p.write_text(json.dumps(c,indent=2)+'\n')
 for a in load(R/'config/ARM_PLAN.json'):shutil.copyfile(p,Path(a['path'])/'config/PROTOCOL.json')
 # The previous freeze remains immutable; the new run freezes corrected derived data.
 save('provenance/PRE_OPTIMIZATION_ASSETS_R2.json',dict(epoch=time.time(),R1=asset(R/'provenance/PRE_OPTIMIZATION_ASSETS.json'),repair='FULL native depth inclusion; TRUSTED bytes unchanged; OLD samples regenerated consistently',records=records,sources=[asset(R/('hero_fit'if r['role']=='FIT'else'holdout/hero')/r['view_id']/f)for r in plan for f in ['SOURCE.json','CLEANING.json','HERO_native.npz','FACE_EVIDENCE.npz','OBS_FULL.npz','OBS_TRUSTED.npz']],GT=False))
 save('metrics/FULL_NATIVE_INPUT_FIDELITY_REPAIR.json',records);table('metrics/FULL_NATIVE_INPUT_FIDELITY_REPAIR.csv',records)
 for manifest in ['VIEW_HERO_COMPLETENESS_MANIFEST.json']:
  rows=load(R/manifest)
  for row in rows:
   root=R/('hero_fit'if row['role']=='FIT'else'holdout/hero')/row['view_id'];row.update(FULL_native_observations=load(root/'CLEANING.json')['full_native_observations'],FULL_observation_SHA256=sha(root/'OBS_FULL.npz'),TRUSTED_observation_SHA256=sha(root/'OBS_TRUSTED.npz'))
  save(manifest,rows);table('VIEW_HERO_COMPLETENESS_MANIFEST.csv',rows)
 save('metrics/HERO_CLEANING_RESULTS.json',[load(R/('hero_fit'if r['role']=='FIT'else'holdout/hero')/r['view_id']/'CLEANING.json')for r in plan])
if __name__=='__main__':main()
