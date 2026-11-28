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
     if fr['role']!='FIT':continue
     f=np.load(fr['observations_2D']['path']);lab=cv2.imread(fr['Mask']['path'],0);yy,xx=np.mgrid[:lab.shape[0],:lab.shape[1]];uv=np.c_[xx.ravel(),yy.ravel()];rr=rays(uv,f['K'],f['C']);z,fid=cast(meshscene,rr);cz,_=cast(cadscene,rr);valid=np.isfinite(z)&(fid>=0)&(fid<len(body['F_solid']))&(z<cz)
     vf=np.zeros(len(body['F_solid']),bool);cf=vf.copy();vf[fid[valid]]=True;cf[fid[valid&(lab.ravel()==1)]]=True;visible.append(vf);compatible.append(cf);records.append(dict(case=vi['case'],frame=fr['id'],full_canvas_N=lab.size,visible_model_pixels_N=int(valid.sum()),Mask_compatible_pixels_N=int((valid&(lab.ravel()==1)).sum()),cap_pixels_N=int(body['inferred_base_faces'][fid[valid]].sum()),GT='NOT_EVALUABLE'))
   np.savez_compressed(folder/'VISIBILITY.npz',visible_model_faces_by_frame=np.array(visible),Mask_compatible_model_faces_by_frame=np.array(compatible),inferred_base_faces=body['inferred_base_faces'])
   save(folder/'VISIBILITY.json',dict(key=key,frames=records,resolution='full original image grid',definition='model visibility / Mask compatibility only, not measured surface or GT',files=[asset(folder/'VISIBILITY.npz')]))
  print('VISIBILITY',g,flush=True)
if __name__=='__main__':main()
