"""Read-only gradient diagnosis at a frozen common011 initial mesh. No optimizer."""
from multiview import *
import argparse
def main():
 p=argparse.ArgumentParser();p.add_argument('case');a=p.parse_args();guard_optimizer();c=Case(a.case);ch=FreeVertices(c);cfg=load(R/'config/ARM.json');obj=MultiObjective(c,ch,cfg['loss']);obj.attempt=40;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);names=['silhouette','missing','extra','contour','absolute','relative','prior'];GG={k:torch.zeros_like(q)for k in names};values={k:0. for k in names};m=ch.mesh(q);obj.depth.begin(m);localization=[];far_nodes=np.zeros(ch.N,bool)
 def accumulate(name,term):
  values[name]+=float(term.detach());g=torch.autograd.grad(term,q,retain_graph=True,allow_unused=True)[0]
  if g is not None:GG[name].add_(g.detach())
 for cid in c.fit:
  m=ch.mesh(q);fr=c.fragments(m,cid);base,alpha,w,*_=c.aware(fr,cid,True);t=c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=obj.contour(ch.vertices(q),cid);weight=obj.w[cid];fpc=.1 if cfg['loss']in['D1_split','D3_combo']else .05;cdc=.02 if cfg['loss']in['D2_bidir','D3_combo']else .01
  for key,term in [('silhouette',weight*base),('missing',weight*.05*fg),('extra',weight*fpc*fp),('contour',weight*cdc*cd)]:accumulate(key,term)
  if cid in obj.contour.last:
   last=obj.contour.last[cid];ct=last['target_contour_uv'];ij=np.clip(np.rint((ct+.5)*.5-.5).astype(int),[0,0],[319,179]);near=np.isin(c.views[cid]['classes'].cpu().numpy()[ij[:,1],ij[:,0]],[1,2,4]);far=last['reverse_native_px']>=10.;nodes=np.unique(last['eid'][last['nn'][far]])if far.any()else np.array([],int);far_nodes[nodes]=True;localization.append(dict(view=cid,target_contour_N=len(ct),Ring_uncertainty_band_target_N=int(near.sum()),far_target_over10px_N=int(far.sum()),associated_far_vertex_N=len(nodes),interpretation='projection-nearest proxy, not true3D correspondence; occlusion boundary location can be ambiguous'))
  if cid in obj.depth.obs:
   ab,rel,_,_=obj.depth.terms(m,cid,'E3');accumulate('absolute',obj.dw[cid]*.01*ab);accumulate('relative',obj.dw[cid]*.01*rel)
 accumulate('prior',relative_total(obj.prior(ch.mesh(q))));total=sum(GG.values());v,parts=obj.compute(q,True);error=float((total-q.grad).norm()/q.grad.norm().clamp_min(1e-20));rows=[]
 for key in names:
  g=GG[key];rows.append(dict(case=a.case,arm=cfg['tag'],component=key,weighted_value=values[key],gradient_norm=float(g.norm()),gradient_max_vertex=float(g.norm(dim=1).max()),nonzero_vertex_N=int((g.norm(dim=1)>1e-14).sum()),finite=bool(torch.isfinite(g).all()),gradient_units='objective_per_mm',state='common frozen011 initial, ramp fully1; no optimizer update'))
 assert all(r['finite']for r in rows)and error<1e-4
 from normalized_local import local_normalized
 bands=local_normalized(ch,q,total);covered=np.zeros(ch.N,bool)
 for _,direction in bands:covered|=direction.norm(dim=1).cpu().numpy()>0
 save('metrics/'+a.case+'_GRADIENT_DIAGNOSTIC.json',dict(rows=rows,additive_gradient_relative_error=error,localization=localization,far_associated_vertex_N=int(far_nodes.sum()),far_vertices_in_jointgradient_local_bands_N=int((far_nodes&covered).sum()),source_initial=asset(R/'inputs'/a.case/'INITIAL.npz'),prediction_changed=False,GT_read=False));np.savez_compressed(R/'metrics'/(a.case+'_GRADIENT_DIAGNOSTIC.npz'),V=c.V,F=c.F,far_associated=far_nodes,joint_local_band=covered,**{k:g.cpu().numpy()for k,g in GG.items()});print('GRADIENT_PROBE',a.case,cfg['tag'],error,flush=True)
if __name__=='__main__':main()
