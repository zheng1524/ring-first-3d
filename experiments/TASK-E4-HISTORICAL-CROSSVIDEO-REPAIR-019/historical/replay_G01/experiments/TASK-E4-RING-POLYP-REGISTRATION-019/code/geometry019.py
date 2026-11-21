from common import *
from renderer019 import yaw_matrix
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018'
def proxies():
 views={v['id']:v for v in load(R/'config/VIEWS.json')};rows=[];a=np.load(R/'inputs/G01/BODY018.npz');m=trimesh.Trimesh(a['V'],a['F_solid'],process=False);rows.append(dict(video='004',source='frozen018_body_center_mass_proxy',h=m.center_mass,qualification='estimated complete-body model proxy, not GT'));rows.append(dict(video='004',source='frozen018_body_vertex_median_proxy',h=np.median(a['V'],axis=0),qualification='model sampling-dependent proxy, not material centroid'))
 for video in ['004','005']:
  for cid,v in views.items():
   if v['video']!=video or v['role']!='FIT':continue
   root=P18/'hero_fit'/cid if video=='004'else R/'hero_fit'/cid
   p=root/'OBS_TRUSTED.npz'
   if not p.exists():continue
   a=np.load(p);X=a['X'];keep=(np.sqrt((np.linalg.norm(X[:,:2],axis=1)-5.6)**2+X[:,2]**2)-.6)>.6;X=X[keep]
   if len(X)<20:continue
   h=np.median(X,axis=0);rows.append(dict(video=video,source=cid,h=h,N=len(X),qualification='robust center of visible trusted source core only; partial visibility may bias it, not true full-body centroid'))
 for vid in ['004','005']:
  rr=[x for x in rows if x['video']==vid];h=np.array([x['h']for x in rr]);spread=float(np.median(np.linalg.norm(h[:,:2]-np.median(h[:,:2],axis=0),axis=1)))+.6
  for r in rr:r.update(uncertainty_proxy_mm=spread,projected_direction_length_mm=float(np.linalg.norm(r['h'][:2])),direction_informative=bool(np.linalg.norm(r['h'][:2])>spread))
 candidates=[]
 for parity in [1,-1]:
  for a in [x for x in rows if x['video']=='004']:
   for b in [x for x in rows if x['video']=='005']:
    aa=np.asarray(a['h']);bb=np.asarray(b['h'])*[1,parity,parity];angle=float(np.degrees(np.arctan2(aa[1],aa[0])-np.arctan2(bb[1],bb[0]))%360);q=min(a['projected_direction_length_mm']/a['uncertainty_proxy_mm'],b['projected_direction_length_mm']/b['uncertainty_proxy_mm']);candidates.append(dict(yaw_deg=angle,parity=parity,T=yaw_matrix(angle,parity),first=a['source'],second=b['source'],direction_strength_proxy=float(q),status='DIRECTION_CANDIDATE'if q>=1 else'AMBIGUOUS_SHORT_OR_SOURCE_DEPENDENT_DIRECTION'))
 save('metrics/SHAPE_DIRECTION_PROXIES.json',dict(proxies=rows,candidates=candidates,GT=False,not_true_centroids=True));return candidates
if __name__=='__main__':proxies()
