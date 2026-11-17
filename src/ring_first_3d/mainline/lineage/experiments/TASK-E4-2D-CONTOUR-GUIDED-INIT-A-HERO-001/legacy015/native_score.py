"""Fixed native-observation evaluation. GT-free FIT selection, HOLDOUT post-freeze."""
from common import *
from scipy.ndimage import distance_transform_edt
import open3d as o3d

def evaluate(name,path,include_held=False,tag=None):
 z=np.load(path);V,F=z['V'],z['F'];rt=scene(V,F);rg=np.load(R/'inputs'/name/'RING.npz');rs=scene(rg['V'],rg['F']);rows=[]
 for v in getcase(name)['views']:
  if not include_held and v['role']!='FIT':continue
  cid=v['id'];a=np.load(R/'inputs'/name/(cid+'.npz'));lab=a['labels'];K,T=a['K'],a['T'];target=lab==1;known=lab!=2;p=R/'runtime/cad_depth'/ (cid+'.npz');p.parent.mkdir(exist_ok=True)
  if p.exists():cad=np.load(p)['z']
  else:cad=cast(rs,K,T,*target.shape);np.savez_compressed(p,z=cad)
  zz=cast(rt,K,T,*target.shape);pred=np.isfinite(zz)&(zz<cad);tp=int((pred&target).sum());fn=int((target&~pred).sum());fp=int((pred&~target&known).sum());pc=pred&known;ct,cp=contour(target),contour(pc);bd=float(np.r_[cKDTree(ct).query(cp)[0],cKDTree(cp).query(ct)[0]].mean())if len(ct)and len(cp)else float(np.hypot(*target.shape));drec={};depthcost=0.;dp=R/'depth_observations'/(cid+'.npz')
  if dp.exists():
   d=np.load(dp);ray=np.c_[d['uv'],np.ones(len(d['uv']))]@np.linalg.inv(d['K']).T;rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32);zh=rt.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy().astype(float);zr=rs.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy().astype(float);hit=np.isfinite(zh)&(zh>0)&(zh<zr-.05);err=(zh-d['z']);rr=np.where(hit,err/.5,0.);h=np.where(abs(rr)<1,.5*rr*rr,abs(rr)-.5).clip(0,9.5);depthcost=float(np.where(hit,h,9.5).mean());drec=dict(fixed_depth_N=len(hit),depth_hit_N=int(hit.sum()),depth_miss_N=int((~hit).sum()),depth_hit_rate=float(hit.mean()),depth_MAE_mm=stats(err[hit])['MAE'],fixed_depth_cost=depthcost)
  N=int(target.sum());iou=tp/max(1,tp+fn+fp);score=iou-.1*fp/max(1,N)-.01*bd-.01*depthcost;drec.pop('fixed_depth_cost',None)
  all_fp=int((pred&~target).sum());ring_front=int(((lab==2)&np.isfinite(cad)&np.isfinite(zz)&(zz<cad-.05)).sum());rm=lab==2;cadmask=np.isfinite(cad)&~target;ringiou=float((rm&cadmask).sum()/max(1,(rm|cadmask).sum()))
  rows.append(dict(case=name,tag=tag,view=cid,video=v['video'],role=v['role'],native_pixels=True,Mask_N=N,TP=tp,FN=fn,FP=fp,IoU=iou,Precision=tp/max(1,tp+fp),Recall=tp/max(1,N),FP_per_mask=fp/max(1,N),boundary_MAE_px=bd,CAD_visible_pixel_N=int(np.isfinite(cad).sum()),Ring_CAD_mask_IoU_diagnostic=ringiou,fixed_depth_cost=depthcost,selection_score=score,all_pixel_visible_IoU=tp/max(1,tp+fn+all_fp),all_pixel_FP=all_fp,Ring_front_conflict_N=ring_front,primary_metric_rule='frozen013 ignore observedRing; supplementary allpixel/frontconflict not method selection',**drec))
 keys=['IoU','Precision','Recall','FP_per_mask','boundary_MAE_px','fixed_depth_cost','selection_score'];means={role:{k:float(np.mean([d[k]for d in rows if d['role']==role]))for k in keys}for role in sorted({v['role']for v in rows})}
 return dict(case=name,tag=tag,mean=means,per_view=rows)

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('path');p.add_argument('--tag',default='');p.add_argument('--held',action='store_true');a=p.parse_args();d=evaluate(a.case,a.path,a.held,a.tag);save('metrics/scores/'+a.tag+'_'+a.case+'.json',d);print(d['mean'])
