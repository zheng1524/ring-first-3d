"""Frozen-body mesh visibility in actual cameras, distinct from inferred base faces."""
from observations import *
def main():
 for idx in read(M4/'GROUP_INDEX.json')['groups']:
  g=idx['group'];root=T/'runs/results'/g
  if not(root/'GROUP_RESULT.json').exists():continue
  a=read(T/'runs/inputs'/g/'AUDIT.json');cadpath=next((s['cad_path']for s in a['source_metadata']),None)
  if cadpath is None:cadpath=WORK/'runs/m2f5_unified/cad'/('R5.npz'if a['videos'][0]['ring_radius_mm']<4 else'R10.npz')
  cad=np.load(cadpath);cadscene=scene(cad['V'],cad['F'])
  for r in read(root/'GROUP_RESULT.json')['results']:
   folder=root/r['configuration'];key=digest([sha(folder/'BODY.npz'),[sha(p)for p in r['source_indices']],sha(Path(__file__))])
   if(folder/'VISIBILITY.json').exists()and read(folder/'VISIBILITY.json')['key']==key:continue
   body=np.load(folder/'BODY.npz');meshscene=scene(body['V'],body['F_solid']);visible=[];compatible=[];records=[]
   for path in r['source_indices']:
    vi=read(path);vr=Path(path).parent
    for fr in vi['frames']:
     f=np.load(fr['observations_2D']['path']);lab=cv2.imread(fr['Mask']['path'],0);yy,xx=np.mgrid[:lab.shape[0],:lab.shape[1]];uv=np.c_[xx.ravel(),yy.ravel()];rr=rays(uv,f['K'],f['C']);z,fid=cast(meshscene,rr);cz,_=cast(cadscene,rr);valid=np.isfinite(z)&(fid>=0)&(fid<len(body['F_solid']))&(z<cz)
     vf=np.zeros(len(body['F_solid']),bool);cf=vf.copy();vf[fid[valid]]=True;cf[fid[valid&(lab.ravel()==1)]]=True;visible.append(vf);compatible.append(cf);target=lab.ravel()==1;known=lab.ravel()!=2;pred=valid&known
     records.append(dict(case=vi['case'],frame=fr['id'],role=fr['role'],full_canvas_N=lab.size,foreground_fixed_N=int(target.sum()),foreground_hit_N=int((target&pred).sum()),foreground_miss_N=int((target&~pred).sum()),false_positive_N=int((~target&pred).sum()),full_mesh_IoU=float((target&pred).sum()/max(1,(target|pred).sum())),visible_model_pixels_N=int(valid.sum()),Mask_compatible_pixels_N=int((valid&target).sum()),cap_pixels_N=int(body['inferred_base_faces'][fid[valid]].sum()),GT='NOT_EVALUABLE'))
   base=read(folder/'BASE.json');plane=np.array(base['plane'])if r['base_applied']else None;depth=[];bias={x['source_id']:x['b_mm']for x in r['bias']}
   for path in r['source_indices']:
    vi=read(path)
    for source in vi['sources']:
     obs=np.load(Path(path).parent/(source['source']['tag']+'_OBS.npz'));z,fid=cast(meshscene,obs['rays']);finite=np.isfinite(z)&(fid>=0)&(fid<len(body['F_solid']));cap=np.zeros(len(z),bool);cap[finite]=body['inferred_base_faces'][fid[finite]];hit=finite&~cap&(z<obs['cad_z']-.05);b=bias[source['source_id']];err=abs(z[hit]+b-obs['D'][hit]);az,ah,ac=clipped_depth(np.array(r['p']),obs['rays'],plane);both=finite&~cap&ah;delta=abs(z[both]-az[both])
     depth.append(dict(source_id=source['source_id'],fixed_N=len(z),valid_genuine_visible_N=int(hit.sum()),invalid_N=int((~hit).sum()),cap_only_N=int(cap.sum()),mesh_depth_MAE_mm=float(err.mean())if len(err)else None,mesh_depth_p95_mm=float(np.percentile(err,95))if len(err)else None,analytic_mesh_common_N=int(both.sum()),analytic_mesh_Z_p95_mm=float(np.percentile(delta,95))if len(delta)else None,analytic_mesh_hit_disagreement_N=int((ah!=(finite&~cap)).sum())))
   signed=cadscene.compute_signed_distance(o3d.core.Tensor(body['V'].astype(np.float32)),nthreads=1).numpy()
   np.savez_compressed(folder/'VISIBILITY.npz',visible_model_faces_by_frame=np.array(visible),Mask_compatible_model_faces_by_frame=np.array(compatible),inferred_base_faces=body['inferred_base_faces'])
   save(folder/'VISIBILITY.json',dict(key=key,frames=records,depth=depth,CAD_inside_model_vertex_N=int((signed<0).sum()),CAD_vertex_penetration_max_mm=float(max(0,-signed.min())),resolution='full original image grid; both FIT and HOLDOUT',definition='model visibility / Mask compatibility only, not measured surface or GT; signed CAD check samples model vertices, not exhaustive triangle collision',files=[asset(folder/'VISIBILITY.npz')]))
  print('VISIBILITY',g,flush=True)
if __name__=='__main__':main()
