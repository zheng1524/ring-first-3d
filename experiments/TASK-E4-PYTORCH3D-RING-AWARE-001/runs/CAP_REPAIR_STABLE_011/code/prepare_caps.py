"""Directed 009 B-blue inheritance. Same data rule across all morphologies."""
from common import *
from planes import normalize,compare
from parametric import body,signed_body
from fit_body import Problem,diagnose
OLD=R.parent/'BODY_BASE_INIT_009'

def publish(n,model,provenance):
 V,F,Fs,flag=body(np.array(model['p']),model['meta']);root=R/'inputs'/n;bound=np.zeros(len(V),bool)
 if flag.any():bound[np.unique(Fs[flag])]=True;bound[-1]=False
 np.savez_compressed(root/'INITIAL.npz',V=V,F=F,F_solid=Fs,inferred_base_faces=flag,boundary_vertex=bound,p=model['p']);save('inputs/'+n+'/C_INITIAL_MODEL.json',dict(model,inheritance=provenance));trimesh.Trimesh(V,Fs,process=False).export(root/'INITIAL_mm.ply');c=getcase(n);save('inputs/'+n+'/NORMALIZATION.json',dict(center=V.mean(0),scale_mm=c['R_mid_mm']-c['wire_mm'],source='current frozen C center and known CAD inner radius; no sphere'))

class InheritProblem(Problem):
 def __init__(self,n,meta,p,blue,weights):
  super().__init__(n,meta,p,'DEPTH');self.blue=blue;self.weights=weights
 def residual(self,p,record=True):
  r=super().residual(p,record);e=signed_body(self.blue,p,self.meta)/.5;soft=e*np.sqrt(2/(np.sqrt(1+e*e)+1));ref=soft*np.sqrt(.005*self.weights);out=np.r_[r,ref]
  if record:self.history[-1].update(B_blue_soft_reference=float(ref@ref),objective=float(out@out/2))
  return out

def main():
 guard_optimizer();assert load(R/'assets_index/INIT_PROTOCOL_FREEZE.json')['initial_C_refitting_not_started'];rows=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];base=load(OLD/'inputs'/n/'BASE.json');e=np.load(OLD/'inputs'/n/'BASE_EVIDENCE.npz');plane=normalize(base['plane']);B=np.load(OLD/'local_results'/n/'B_SELECTED.npz');oldC=load(OLD/'local_results'/n/'C_SELECTED.json');V=B['V'];h=V@plane[:3]+plane[3];blue=h>=0;need=base['contact_status']=='BROAD'and np.any(h<-.001)and np.any(h>.001);evidence=e['Polyp_internal_XYZ']@plane[:3]+plane[3];angles=[];offsets=[];anchor=np.median(e['Polyp_internal_XYZ'],axis=0)
  for t in base['trials']:
   if t['plane']is not None:_,a,d=compare(t['plane'],plane,anchor);angles.append(a);offsets.append(d)
  sign_fixed_status=next(x for x in load(R.parent/'BODY_BASE_PYTORCH3D_010/metrics/BASE_SIGN_REGRESSION.json')if x['case']==n)['new_status'];bs=dict(base,plane=plane,selected_plane=plane,selected_ROI_upper_px=45,base_status=sign_fixed_status,uncertain_base=sign_fixed_status!='RELIABLE',truncate_allowed=bool(need),directed_plane_source='009 BASE.json exactly as blue/gray renderer, normalized without sign change',retained_side_rule='009 B blue positive side; not internal HERO median',original_B_blue_vertex_N=int(blue.sum()),original_B_gray_vertex_N=int((~blue).sum()),B_blue_height_mm=stats(h[blue]),HERO_signed_height_quantiles=np.quantile(evidence,[.1,.5,.9,.95,.99]),HERO_positive_fraction=float((evidence>=0).mean()),direction_warning=bool(np.quantile(evidence,.9)<=0),max_normal_change_deg=max(angles),max_anchor_offset_change_mm=max(offsets),uncertainty_label='UNCERTAIN_BASE'if sign_fixed_status!='RELIABLE'else'STABLE_PLANE_PROXY_NOT_ANATOMICAL_GT')
  save('inputs/'+n+'/BASE_SELECTION.json',bs);save('inputs/'+n+'/BASE.json',dict(base,plane=plane,truncate_allowed=bool(need)))
  why=dict(B=asset(OLD/'local_results'/n/'B_SELECTED.npz'),old_C=asset(OLD/'local_results'/n/'C_SELECTED.npz'),plane_source=asset(OLD/'inputs'/n/'BASE.json'),blue_gray_definition='face/vertex height n dot X+d; directed + side retained',base_plane_not_reselected=True,baseline_normal_flip_for_sign_stability_only=True,small_contact_not_truncated=not need)
  if not need or oldC['meta']['family']=='cap':
   # Keep exact existing parameters and exact mesh sampling, no C refit for already capped bodies.
   model=dict(oldC);why['action']='EXACT_FROZEN_C_REUSED';publish(n,model,why);oldz=np.load(OLD/'local_results'/n/'C_SELECTED.npz');newz=np.load(R/'inputs'/n/'INITIAL.npz');assert np.array_equal(newz['V'],oldz['V'])and np.array_equal(newz['F_solid'],oldz['F_solid'])
  else:
   Q=np.array(base['plane_basis']);A=np.array(base['anchor']);q=(V-A)@Q;blueids=np.flatnonzero(blue);blueids=blueids[np.linspace(0,len(blueids)-1,min(256,len(blueids))).astype(int)];mass=np.bincount(B['F'].ravel(),weights=np.repeat(trimesh.triangles.area(V[B['F']])/3,3),minlength=len(V));w=mass[blueids];w/=w.sum();edges=np.unique(np.sort(np.r_[B['F'][:,[0,1]],B['F'][:,[1,2]],B['F'][:,[2,0]]],1),axis=0);cross=(h[edges[:,0]]*h[edges[:,1]]<0);ed=edges[cross];t=h[ed[:,0]]/(h[ed[:,0]]-h[ed[:,1]]);X=V[ed[:,0]]+t[:,None]*(V[ed[:,1]]-V[ed[:,0]]);footXY=(X-A)@Q;foot=np.mean(footXY[:,:2],axis=0);axes=np.maximum(.25,np.max(abs(footXY[:,:2]-foot),axis=0));height=max(.1,float(np.quantile(q[blue,2],.95)));p=np.r_[foot,np.log(axes),np.log(height),0.];meta=dict(family='cap',base_Q=Q,anchor=A,stage='C0');fits=[];folder=R/'init_results'/n;folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/'B_BLUE_REFERENCE.npz',points=V[blueids],original_vertex_ID=blueids,weights=w,plane_intersection_points=X,initial_p=p)
   initial=dict(p=p,meta=meta,phase='B_BLUE_INITIAL');Vi,Fi,Fsi,flag=body(p,meta);np.savez_compressed(folder/'C_START.npz',V=Vi,F=Fi,F_solid=Fsi,inferred_base_faces=flag,p=p)
   previous=None
   for stage in['C0','C1','C2']:
    if stage=='C1':
     if previous['diagnostics']['FIT_boundary_MAE_px']<=3:break
     p=np.r_[previous['p'],.5]
    if stage=='C2':
     if previous['diagnostics']['FIT_boundary_MAE_px']<=3:break
     p=np.r_[previous['p'],[0.,0.]]
    meta=dict(meta,stage=stage);model=InheritProblem(n,meta,p,V[blueids],w).solve(p,30);model['diagnostics']=diagnose(n,model);fits.append(model);vv,ff,full,flags=body(np.array(model['p']),meta);np.savez_compressed(folder/(stage+'.npz'),V=vv,F=ff,F_solid=full,inferred_base_faces=flags,p=model['p']);save('init_results/'+n+'/'+stage+'.json',model);previous=model;p=np.array(model['p'])
   feasible=[x for x in fits if x['diagnostics']['selection_eligible']];model=min(feasible or fits,key=lambda x:x['objective']+.001*len(x['p']));model['selection_status']='011_REQUIRED_CAP_FIT'if feasible else'011_REQUIRED_CAP_FIT_WITH_GEOMETRY_WARNING';why.update(action='PARAMETRIC_CAP_REFIT_6_7_9_FROM_B_BLUE',B_reference_is_soft_not_GT=True,plane_fixed_to_009=True,optimizer_uses_original_Mask_and_HERO=True);publish(n,model,why)
  z=np.load(R/'inputs'/n/'INITIAL.npz');m=trimesh.Trimesh(z['V'],z['F_solid'],process=False);he=z['V']@plane[:3]+plane[3];rows.append(dict(case=n,type=c['morphology'],contact=base['contact_status'],needs_cap=bool(need),base_status=sign_fixed_status,base_label=bs['uncertainty_label'],action=why['action'],family=model['meta']['family'],parameter_N=len(model['p']),underground_vertex_N=int((he<-.001).sum())if need else None,minimum_height_mm=float(he.min()),max_height_mm=float(he.max()),cap_F_N=int(z['inferred_base_faces'].sum()),watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),original_plane_same=True,HERO_p90_signed_height_mm=float(np.quantile(evidence,.9)),direction_warning=bs['direction_warning']));print('C_INIT',n,rows[-1],flush=True)
 save('metrics/C_INHERITANCE.json',rows);table('metrics/C_INHERITANCE.csv',rows)
if __name__=='__main__':main()
