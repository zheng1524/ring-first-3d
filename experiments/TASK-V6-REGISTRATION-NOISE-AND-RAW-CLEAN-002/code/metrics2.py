"""Frozen-domain, bidirectional held evaluation. Invalid predictions keep denominator."""
from common2 import *
from ring_first_3d.sim.geometry import transform
from scipy.spatial import cKDTree

def summarize(errors):
 a=np.asarray(errors,float);ok=np.isfinite(a);n=len(a);finite=a[ok]
 return dict(N=n,finite=int(ok.sum()),invalid=int((~ok).sum()),finite_fraction=float(ok.mean())if n else 0.,MAE=float(a.mean())if n else None,P95=float(np.sort(a)[max(0,int(np.ceil(.95*n))-1)])if n else None,conditional_MAE=float(finite.mean())if len(finite)else None,conditional_P95=float(np.quantile(finite,.95))if len(finite)else None)

def bidirectional(frames,poses,tr,xyz,T0):
 records=[];groups={};validtracks=set();frames_seen={'A':set(),'B':set()}
 for tid in np.flatnonzero(tr['held']):
  for targetside,sourceind,direction in [('B',0,'A_to_B'),('A',1,'B_to_A')]:
   P=xyz[tid,sourceind]
   for j,f in enumerate(frames):
    if f['side']!=targetside or not np.isfinite(tr['xy'][tid,j]).all():continue
    reason='VALID';error=np.inf;uv=[None,None];z=None
    if T0 is None:reason='NO_TRANSFORM'
    elif not np.isfinite(P).all():reason='SOURCE_DLT_UNAVAILABLE'
    else:
     C=T0@poses[j]if targetside=='B'else poses[j];X=P if sourceind==0 else transform(P[None],T0)[0];cam=(X-C[:3,3])@C[:3,:3];z=float(cam[2]);q=cam@np.array(f['K']).T
     if z<=0:reason='NEGATIVE_DEPTH'
     else:
      uv=q[:2]/q[2];error=float(np.linalg.norm(uv-tr['xy'][tid,j]));inside=0<=uv[0]<640 and 0<=uv[1]<360
      if not inside:reason='OUT_OF_BOUNDS'
      else:validtracks.add(int(tid));frames_seen[targetside].add(j)
    rec=dict(track=int(tid),frame=j,side=targetside,direction=direction,category=int(tr['category'][tid]),status=reason,error_px=error,projection=uv,z=z);records.append(rec);groups.setdefault(direction,[]).append(rec)
 result={}
 for d,rows in groups.items():
  result[d]=dict(**summarize([r['error_px']for r in rows]),valid_inside=sum(r['status']=='VALID'for r in rows),negative=sum(r['status']=='NEGATIVE_DEPTH'for r in rows),out_of_bounds=sum(r['status']=='OUT_OF_BOUNDS'for r in rows),source_DLT_missing=sum(r['status']=='SOURCE_DLT_UNAVAILABLE'for r in rows),categories={str(c):summarize([r['error_px']for r in rows if r['category']==c])for c in [0,1,2]})
 # Independent two-sided availability, counted by complete held track, not observations.
 both=[int(i)for i in np.flatnonzero(tr['held'])if np.isfinite(xyz[i]).all()];result['denominators']=dict(all_held_tracks=int(tr['held'].sum()),two_sided_DLT_tracks=len(both),valid_projected_tracks=len(validtracks),target_frames_A=len(frames_seen['A']),target_frames_B=len(frames_seen['B']),evidence_sufficient=len(both)>=CFG['min_held_tracks']and len(frames_seen['A'])>=2 and len(frames_seen['B'])>=2)
 return result,records

def ring_pixels(asset,frames,poses,T0):
 # Original frozen g5 contour function is installed by native torus implementation.
 from ring_first_3d.mainline.native.geometry import project as native_project
 from ring_first_3d.synthetic.raster import ray_map
 # Render fixed CAD in the A frame; NEVER move the CAD alongside each camera.
 cad=np.load(asset['sources'][0]['cad_path']);values=[];per=[]
 for i,f in enumerate(frames):
  side=f['side'];R=Path(next(v['run']for v in asset['videos']if v['side']==side));ob=np.load(R/'observations'/(f['id'].split('__',1)[1]+'_ring.npz'));q=ob['q_held'];C=(T0@poses[i])if side=='B'else poses[i]
  r=ray_map(cad['V'],cad['F'],np.array(f['K']),C,(360,640));mask=r['valid'].astype(np.uint8)
  import cv2
  curves,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
  contour=np.concatenate([c[:,0,:]for c in curves])if curves else np.empty((0,2));errors=cKDTree(contour).query(q)[0]if len(contour)else np.full(len(q),np.inf);values.extend(errors);per.append(dict(frame=i,side=side,**summarize(errors)))
 return dict(all=summarize(values),per_frame=per,domain='original q_held; fixed shared CAD; raster contour pixel discretization'),per
