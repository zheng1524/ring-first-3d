"""Fixed-geometry shadow isolation of detached Ring visibility and raster branches."""
from tape import *

def main():
 guard_optimizer();c=Case('G02');ch=FreeVertices(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch);obj.attempt=40;obj.depth.begin(ch.mesh(q));original=c.fragments;refs={};current={};frozen={};records=[];gradients={};mode='ORIGINAL'
 def fragments(m,cid):
  fr=frozen[cid]if mode=='FIX_FRAGMENT'and cid in frozen else original(m,cid)
  if cid not in frozen:frozen[cid]=fr
  return fr
 def aware(fr,cid,return_aux=False):
  d=c.views[cid];valid=fr.pix_to_face[0]>=0;p=torch.sigmoid(-fr.dists[0]/1e-4)*valid;z=fr.zbuf[0];rz=d['cad_z'];actualvis=torch.where(d['cad_finite'][...,None],(z.detach()<=rz[...,None]).to(z.dtype),torch.ones_like(z));vis=refs[cid]['vis']if mode=='FIX_VISIBILITY'and cid in refs else actualvis
  alpha=1.-torch.prod(1.-p*vis,dim=-1);protected=((d['classes']==1)|(d['classes']==2)|(d['classes']==4))&(d['target']==0);front=((valid&vis.bool()).any(dim=-1)).to(p.dtype);w=torch.where(protected,torch.where(d['cad_finite'],front,torch.zeros_like(front)),torch.ones_like(front))
  if mode=='FIX_W'and cid in refs:w=refs[cid]['w']
  actual=dict(vis=actualvis.detach(),w=w.detach(),alpha=alpha.detach(),faces=fr.pix_to_face[0].detach(),dists=fr.dists[0].detach(),z=z.detach())
  if cid not in refs:refs[cid]=actual
  ref=refs[cid];current[cid]=dict(visibility_bit_changes=int(((actualvis!=ref['vis'])&valid).sum()),weight_bit_changes=int((w.detach()!=ref['w']).sum()),face_assignment_changes=int((actual['faces']!=ref['faces']).sum()),alpha_max_change=float((alpha.detach()-ref['alpha']).abs().max()),finite_z_max_change=float((z.detach()-ref['z']).abs()[valid].max())if valid.any()else 0.)
  loss=((alpha-d['target'])**2*w).mean()
  return(loss,alpha,w,vis,p)if return_aux else loss
 c.fragments=fragments;c.aware=aware
 for mode in ['ORIGINAL','FIX_W','FIX_VISIBILITY','FIX_FRAGMENT']:
  prev=None
  for rep in range(6):
   sums={k:torch.zeros_like(q)for k in NAMES};by=[]
   for cid in c.fit:
    ts,_=view_terms(c,ch,obj,q,cid)
    for k,t in ts.items():sums[k]+=gradient(t,q)
    by.append(dict(view=cid,**current[cid]))
   sums['prior']=gradient(relative_total(obj.prior(ch.mesh(q))),q);total=sum(sums.values());row=dict(mode=mode,repeat=rep,view_branch_changes=by,gradient_norm=float(total.norm()))
   if prev is not None:row['component_repeat_relative']={k:float((sums[k]-prev[k]).norm()/prev[k].norm().clamp_min(1e-30))for k in NAMES};row['total_repeat_relative']=float((total-sum(prev.values())).norm()/sum(prev.values()).norm().clamp_min(1e-30))
   records.append(row);prev={k:g.clone()for k,g in sums.items()};gradients[mode+'_'+str(rep)]=total.cpu().numpy()
 summary=[]
 for m in ['ORIGINAL','FIX_W','FIX_VISIBILITY','FIX_FRAGMENT']:
  rr=[x for x in records if x['mode']==m];summary.append(dict(mode=m,maximum_relative_total_gradient_repeat_error=max(x.get('total_repeat_relative',0)for x in rr),maximum_visibility_bit_changes=max(v['visibility_bit_changes']for x in rr for v in x['view_branch_changes']),maximum_weight_bit_changes=max(v['weight_bit_changes']for x in rr for v in x['view_branch_changes'])))
 save('metrics/G02_RASTER_BRANCH_ISOLATION.json',dict(summary=summary,records=records,shadow_only=True,optimizer_steps=0,GT_read=False,training_visibility_unchanged=True));np.savez_compressed(R/'metrics/G02_RASTER_BRANCH_GRADIENTS.npz',V=c.V,F=c.F,**gradients);print('RASTER_BRANCH_ISOLATION',summary,flush=True)
if __name__=='__main__':main()
