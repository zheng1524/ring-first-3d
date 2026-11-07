"""Thin low-dimensional SciPy-TRF adapter over the existing repaired PyTorch3D/Ring-Aware renderer."""
from parametric import *
from p3d import Case,mesh,torch,tensor
from scipy.optimize import least_squares
from evaluate import pointcast
from components import Depth
from depth_terms import D2Depth
import argparse,open3d as o3d

def robustify(r):return r*np.sqrt(2/(np.sqrt(1+r*r)+1))
class Problem:
 def __init__(self,name,meta,base,phase,weak=False):
  self.name=name;self.meta=meta;self.base=np.array(base);self.phase=phase;self.weak=weak;self.c=Case(name);self.cfg=load(R/'config/PROTOCOL.json');self.calls=0;self.history=[];saved_views=self.c.views;self.c.views={k:v for k,v in saved_views.items()if(R/'depth_observations'/(k+'.npz')).exists()};self.depth=Depth(self.c);self.c.views=saved_views;self.base_evidence=load(R/'inputs'/name/'BASE.json');self.ringP=self.c.ringV[::16];self.loss_labels=[]
  self.observed=[cid for cid in self.c.fit if(R/'depth_observations'/(cid+'.npz')).exists()];self.depth.obs={k:v for k,v in self.depth.obs.items()if k in self.observed};self.viewmass={}
  for cid in self.c.fit:
   t=self.c.views[cid]['target'];self.viewmass[cid]=(.5*t/t.sum().clamp_min(1)+.5*(1-t)/(1-t).sum().clamp_min(1))
 def residual(self,p,record=True):
  self.calls+=1;V,F,full,flag=body(p,self.meta);self.c.F=F;mm=mesh((V-self.c.center)/self.c.scale,F);parts=[];silcost=0.;relcost=0.;abscost=0.;cadcost=0.;depth_infos=[]
  with torch.no_grad():
   for cid in self.c.fit:
    fr=self.c.fragments(mm,cid);loss,alpha,w,*_=self.c.aware(fr,cid,return_aux=True);r=((alpha-self.c.views[cid]['target'])*torch.sqrt(w*self.viewmass[cid]/len(self.c.fit))).cpu().numpy().ravel();parts.append(r);silcost+=float(r@r)
   if self.phase=='DEPTH':
    self.depth.begin(mm)
    for cid in self.observed:
     a=self.depth.obs[cid];z,active,z0,fid=D2Depth.query(self.depth,mm,cid);pred=z.cpu().numpy();hit=active.cpu().numpy();err=(pred-a['z'])/.5;r=robustify(err);r=np.clip(r,-np.sqrt(19.),np.sqrt(19.));r=np.where(hit,r,np.sqrt(19.));ar=r*np.sqrt(.1/max(1,len(r))/max(1,len(self.observed)));parts.append(ar);abscost+=float(ar@ar)
     pair=a['pairs'];good=hit[pair].all(1);dr=(pred[pair[:,0]]-pred[pair[:,1]])-(a['z'][pair[:,0]]-a['z'][pair[:,1]]);r=robustify(dr/.5);r=np.clip(r,-np.sqrt(19.),np.sqrt(19.));r=np.where(good,r,np.sqrt(19.));r=r/np.sqrt(max(1,len(r))*max(1,len(self.observed)));parts.append(r);relcost+=float(r@r);depth_infos.append(dict(source=cid,hit_N=int(hit.sum()),fixed_N=len(hit),pairs_N=len(pair),pair_hit_N=int(good.sum())))
   # Fixed known Ring material signed-distance proxy; final acceptance uses actual CAD collision.
   tri=V[full];P=np.r_[V,tri.mean(1),(tri[:,0]+tri[:,1])/2,(tri[:,1]+tri[:,2])/2,(tri[:,2]+tri[:,0])/2];sd=torus_sdf(P,self.c.meta['R_mid_mm'],self.c.meta['wire_mm']);r=np.maximum(0,.005-sd)/.05*np.sqrt(20/len(P));inside=signed_body(self.ringP,p,self.meta);ri=np.maximum(0,.005-inside)/.05*np.sqrt(20/len(inside));parts.extend([r,ri]);cadcost=float(r@r+ri@ri)
   prior=(p-self.base)/np.r_[np.ones(min(3,len(p)))*10,np.ones(max(0,len(p)-3))];prior*=np.sqrt(.005);parts.append(prior)
   if self.weak and self.base_evidence['plane']is not None:
    plane=np.array(self.base_evidence['plane']);h=V@plane[:3]+plane[3];r=np.maximum(0,-h)/2*np.sqrt(.01/len(h));parts.append(r)
  result=np.concatenate(parts).astype(float)
  if not np.isfinite(result).all():raise FloatingPointError('NONFINITE_RESIDUAL')
  if record:self.history.append(dict(call=self.calls,objective=float(result@result/2),silhouette=silcost,relative_depth=relcost,absolute_depth=abscost,Ring_proxy=cadcost,parameters=p.copy(),depth=depth_infos))
  return result
 def jac(self,p):
  n=len(p);J=[]
  if self.meta['family']in['ellipsoid','star']:h=np.r_[np.full(3,.02),np.full(3,.002),np.full(3,.002),np.full(n-9,.005)]
  else:h=np.r_[np.full(2,.02),np.full(3,.002),.002,np.full(n-6,.005)]
  for k,step in enumerate(h):
   a=p.copy();b=p.copy();a[k]+=step;b[k]-=step;J.append((self.residual(a,False)-self.residual(b,False))/(2*step))
  return np.stack(J,axis=1)
 def bounds(self):
  n=len(self.base)
  if self.meta['family']in['ellipsoid','star']:
   lo=np.r_[np.full(3,-20),np.full(3,-.8),np.log(np.full(3,.25)),np.full(n-9,-.2)];hi=np.r_[np.full(3,20),np.full(3,.8),np.log(np.full(3,20)),np.full(n-9,.2)]
  else:
   lo=np.r_[[-20,-20],np.log([.25,.25,.1]),-np.pi];hi=np.r_[[20,20],np.log([20,20,20]),np.pi]
   if n>=7:lo=np.r_[lo,.5];hi=np.r_[hi,2.]
   if n>=9:lo=np.r_[lo,[-.25,-.25]];hi=np.r_[hi,[.25,.25]]
  return lo,hi
 def solve(self,start,budget):
  lo,hi=self.bounds();start=np.clip(start,lo+1e-6,hi-1e-6);r0=self.residual(start);t0=time.time();result=least_squares(self.residual,start,jac=self.jac,bounds=(lo,hi),method='trf',loss='linear',max_nfev=budget,ftol=1e-4,xtol=1e-4,gtol=1e-4,x_scale='jac');return dict(p=result.x,meta=self.meta,nfev=result.nfev,actual_forward_calls=self.calls,success=bool(result.success),termination=result.message,initial_objective=float(r0@r0/2),objective=float(result.fun@result.fun/2),seconds=time.time()-t0,history=self.history,phase=self.phase)

def export(name,tag,model):
 out=R/'local_results'/name;out.mkdir(parents=True,exist_ok=True);p=np.array(model['p']);V,F,full,flag=body(p,model['meta']);np.savez_compressed(out/(tag+'.npz'),V=V,F=F,F_solid=full,inferred_base_faces=flag,p=p);trimesh.Trimesh(V,full,process=False).export(out/(tag+'_mm.ply'));save('local_results/'+name+'/'+tag+'.json',model)

def diagnose(name,model):
 c=getcase(name);V,F,full,flag=body(np.array(model['p']),model['meta']);m=trimesh.Trimesh(V,full,process=False);rr=np.load(R/'inputs'/name/'RING.npz');ring=trimesh.Trimesh(rr['V'],rr['F'],process=False);cm=trimesh.collision.CollisionManager();cm.add_object('Ring',ring);collision=bool(cm.in_collision_single(m));rt=scene(V,F);rs=scene(rr['V'],rr['F']);inside=signed_body(rr['V'][::16],np.array(model['p']),model['meta']);per=[]
 for v in c['views']:
  a=np.load(R/'inputs'/name/(v['id']+'.npz'));z=cast(rt,a['K'],a['T'],360,640);cz=cast(rs,a['K'],a['T'],360,640);pred=np.isfinite(z)&(z<cz);target=a['labels']==1;known=a['labels']!=2;inter=(pred&target).sum();union=(target|(pred&known)).sum();co=contour(pred&known);ct=contour(target);bd=stats(np.r_[cKDTree(co).query(ct)[0],cKDTree(ct).query(co)[0]])if len(co)and len(ct)else stats([]);r=dict(source=v['id'],role=v['role'],IoU=float(inter/max(1,union)),coverage=float(inter/max(1,target.sum())),boundary_px=bd,outside_per_mask=float((pred&~target&known).sum()/max(1,target.sum())))
  dp=R/'depth_observations'/(v['id']+'.npz')
  if dp.exists():
   o=np.load(dp);ray=np.c_[o['uv'],np.ones(len(o['uv']))]@np.linalg.inv(o['K']).T;X=(ray*o['z'][:,None])@o['T'][:3,:3].T+o['T'][:3,3];_,_,zh=pointcast(rt,X,o['K'],o['T']);_,_,cad=pointcast(rs,X,o['K'],o['T']);hit=np.isfinite(zh)&(zh>0)&(zh<cad-.05);pair=o['pairs'];good=hit[pair].all(1);err=zh-o['z'];delta=(zh[pair[good,0]]-zh[pair[good,1]])-(o['z'][pair[good,0]]-o['z'][pair[good,1]]);r.update(depth_fixed_N=len(hit),depth_hit_N=int(hit.sum()),depth_hit_rate=float(hit.mean())if len(hit)else None,absolute_depth_error_mm=stats(err[hit]),relative_depth_error_mm=stats(delta),pair_fixed_N=len(pair),pair_hit_N=int(good.sum()),fixed_denominator_relative_score=float((abs(delta).sum()+2.5*(~good).sum())/max(1,len(pair))))
  per.append(r)
 fit=[x for x in per if x['role']=='FIT'];axes=np.exp(model['p'][6:9])if model['meta']['family']in['ellipsoid','star']else np.exp(model['p'][2:5]);valid=bool(np.isfinite(V).all()and m.is_watertight and m.is_winding_consistent and len(m.split(only_watertight=False))==1 and not collision and not(inside<-.001).any()and max(axes)/min(axes)<=30);eligible=valid and np.mean([x['coverage']for x in fit])>=.5
 return dict(geometry_valid=valid,selection_eligible=eligible,Ring_collision=collision,Ring_inside_body_N=int((inside<-.001).sum()),axis_ratio=float(max(axes)/min(axes)),watertight=bool(m.is_watertight),components=len(m.split(only_watertight=False)),vertices=len(V),faces_retained=len(F),inferred_closure_faces=int(flag.sum()),volume_diagnostic_only_mm3=float(m.volume),per_view=per,fit_IoU=float(np.mean([x['IoU']for x in fit])),holdout_IoU=float(np.mean([x['IoU']for x in per if x['role']!='FIT'])),fit_coverage=float(np.mean([x['coverage']for x in fit])),FIT_boundary_MAE_px=float(np.mean([x['boundary_px']['MAE']for x in fit if x['boundary_px']['MAE']is not None])))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');args=ap.parse_args();name=args.case;guard_optimizer();cfg=load(R/'config/PROTOCOL.json');assert load(R/'assets_index/PREOPT_FREEZE.json')['body_optimization_not_started'];a=np.load(R/'inputs'/name/'INITIAL.npz');p0,Q=initial_parameters(a['V']);meta=dict(family='ellipsoid',Q0=Q);initial=dict(p=p0,meta=meta);export(name,'A_ELLIPSOID_PARAMETER_ADAPTER',initial);solutions=[];starts=[]
 for seed in[0,1,2]:
  rng=np.random.default_rng(20261106+seed);p=p0.copy()
  if seed:p[:3]+=rng.normal(0,.3,3);p[3:6]+=rng.normal(0,.06,3);p[6:9]+=rng.normal(0,.1,3)
  contour_fit=Problem(name,meta,p0,'CONTOUR').solve(p,20);export(name,f'B_seed{seed}_CONTOUR',contour_fit);depth_fit=Problem(name,meta,p0,'DEPTH').solve(np.array(contour_fit['p']),30);depth_fit.update(seed=seed);depth_fit['diagnostics']=diagnose(name,depth_fit);export(name,f'B_seed{seed}_DEPTH',depth_fit);solutions.append(depth_fit);starts.append(p)
 feasible=[x for x in solutions if x['diagnostics']['selection_eligible']];best=min(feasible or solutions,key=lambda x:x['objective']);best['selection_status']='FEASIBLE_CANDIDATE'if feasible else'NO_FEASIBLE_CANDIDATE_DIAGNOSTIC_ONLY';best['all_initials_retained']=True;export(name,'B_SELECTED',best)
 # Bounded star is offered to every case by the same residual rule, never by morphology.
 if best['diagnostics']['FIT_boundary_MAE_px']>3 and best['diagnostics']['fit_coverage']>=.5:
  smeta=dict(meta,family='star');p=np.r_[best['p'],np.zeros(7)];star=Problem(name,smeta,p,'DEPTH').solve(p,25);star['diagnostics']=diagnose(name,star);export(name,'B_STAR_CANDIDATE',star)
  if star['diagnostics']['selection_eligible']and star['objective']<best['objective']*.99:best=star;best['selection_status']='FEASIBLE_BOUNDED_STAR_CANDIDATE';export(name,'B_SELECTED',best)
 base=load(R/'inputs'/name/'BASE.json');stages=[]
 if base['plane'] is not None and base['contact_status']=='BROAD' and np.any(body(np.array(best['p']),best['meta'])[0]@np.array(base['plane'][:3])+base['plane'][3]<-.001) and np.any(body(np.array(best['p']),best['meta'])[0]@np.array(base['plane'][:3])+base['plane'][3]>.001):
  V,_,_,_=body(np.array(best['p']),best['meta']);q=(V-np.array(base['anchor']))@np.array(base['plane_basis']);foot=np.median(q[:,:2],axis=0);ax=np.maximum(.25,np.quantile(abs(q[:,:2]-foot),.95,axis=0));height=max(.1,np.quantile(q[:,2],.95));p=np.r_[foot,np.log(ax),np.log(height),0.];cmeta=dict(family='cap',base_Q=base['plane_basis'],anchor=base['anchor'],stage='C0');previous=None
  for stage in['C0','C1','C2']:
   if stage=='C1':
    if previous['diagnostics']['FIT_boundary_MAE_px']<=3:break
    p=np.r_[previous['p'],.5]
   if stage=='C2':
    if previous['diagnostics']['FIT_boundary_MAE_px']<=3:break
    p=np.r_[previous['p'],[0.,0.]]
   cmeta=dict(cmeta,stage=stage);fit=Problem(name,cmeta,p,'DEPTH').solve(p,30);fit['diagnostics']=diagnose(name,fit);stages.append(fit);export(name,stage+'_BASE_CANDIDATE',fit);previous=fit;p=np.array(fit['p'])
  viable=[x for x in stages if x['diagnostics']['selection_eligible']];cbest=min(viable or stages,key=lambda x:x['objective']+.001*len(x['p']));cbest['selection_status']='BASE_TRUNCATED_CANDIDATE'if viable else'BASE_TRUNCATED_INFEASIBLE_DIAGNOSTIC';export(name,'C_SELECTED',cbest)
 elif base['base_status']=='WEAK'and base['contact_status']=='BROAD':
  weak=Problem(name,best['meta'],best['p'],'DEPTH',weak=True).solve(np.array(best['p']),25);weak['diagnostics']=diagnose(name,weak);weak['selection_status']='WEAK_BASE_UNTRUNCATED';export(name,'C_SELECTED',weak)
 else:
  cbest=dict(best);cbest['selection_status']='NO_TRUNCATION_EVIDENCE_INSUFFICIENT_OR_SMALL_CONTACT';cbest['same_as_B']=True;export(name,'C_SELECTED',cbest)
 save('metrics/'+name+'_FIT_RUN.json',dict(case=name,completed=True,seconds='per candidate JSON',multistart_N=3,type_not_used_in_optimizer=True,body_free_vertex_updates=False,camera_updates=False,base_qualification=base['base_status'],contact=base['contact_status'],HERO_crossview_loss=False));print('CASE_DONE',name,flush=True)
if __name__=='__main__':main()
