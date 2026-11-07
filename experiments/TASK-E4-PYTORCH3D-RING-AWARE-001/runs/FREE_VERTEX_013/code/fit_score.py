"""FIT-only fixed-denominator pilot selection. No HOLDOUT or Blender access."""
from common import *
from scipy.ndimage import distance_transform_edt
from evaluate import pointcast

def score(name,path,fit_only=True):
 z=np.load(path);V,F=z['V'],z['F'];rt=scene(V,F);a0=np.load(R/'inputs'/name/'INITIAL.npz');r0=scene(a0['V'],a0['F']);r=np.load(R/'inputs'/name/'RING.npz');rs=scene(r['V'],r['F']);rows=[]
 for v in getcase(name)['views']:
  if fit_only and v['role']!='FIT':continue
  cid=v['id'];a=np.load(R/'inputs'/name/(cid+'.npz'));K,T=a['K'],a['T'];lab=a['labels'];target=lab==1;cad=cast(rs,K,T,*target.shape);zh=cast(rt,K,T,*target.shape);zp=cast(r0,K,T,*target.shape);pred=np.isfinite(zh)&(zh<cad);p0=np.isfinite(zp)&(zp<cad);known=lab!=2;far=target&~p0&(distance_transform_edt(~p0)>10);ct=contour(target);co=contour(pred&known);bd=float(np.r_[cKDTree(ct).query(co)[0],cKDTree(co).query(ct)[0]].mean())if len(ct)and len(co)else float(np.hypot(*target.shape));recall=float((pred&target).sum()/max(1,target.sum()));fr=float((pred&far).sum()/max(1,far.sum()))if far.any()else recall;fp=float((pred&~target&known).sum()/max(1,target.sum()));depthcost=0.;dp=R/'depth_observations'/(cid+'.npz');drec={}
  if dp.exists():
   d=np.load(dp);rays=np.c_[d['uv'],np.ones(len(d['uv']))]@np.linalg.inv(d['K']).T;P=(rays*d['z'][:,None])@T[:3,:3].T+T[:3,3];_,_,zq=pointcast(rt,P,d['K'],T);_,_,zc=pointcast(rs,P,d['K'],T);hit=np.isfinite(zq)&(zq>0)&(zq<zc-.05);e=np.where(hit,(zq-d['z'])/.5,0.);h=np.where(abs(e)<1,.5*e*e,abs(e)-.5).clip(0,9.5);depthcost=float(np.where(hit,h,9.5).mean())if len(hit)else 9.5;drec=dict(fixed_N=len(hit),hit_N=int(hit.sum()),depth_hit_rate=float(hit.mean())if len(hit)else None,depth_MAE_mm=stats((zq-d['z'])[hit])['MAE'])
  rows.append(dict(case=name,view=cid,role=v['role'],full_mask_N=int(target.sum()),IoU=float((pred&target).sum()/max(1,(target|(pred&known)).sum())),recall=recall,far_missing_N=int(far.sum()),far_recall=fr,FP_per_mask=fp,boundary_MAE_px=bd,raw_fixed_depth_cost=depthcost,score=.5*fr+.5*recall-.5*fp-.02*bd-.02*depthcost,**drec))
 return dict(case=name,mean={k:float(np.mean([x[k]for x in rows]))for k in ['IoU','recall','far_recall','FP_per_mask','boundary_MAE_px','raw_fixed_depth_cost','score']},per_view=rows)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('path');p.add_argument('--all-views',action='store_true');a=p.parse_args();s=score(a.case,a.path,not a.all_views);save('metrics/'+a.case+'_FIT_SCORE.json',s);print(s['mean'])
