"""Exact inherited objective terms, instrumented without altering their gradients."""
from stalk import *
NAMES=['silhouette','missing','extra','contour','absolute','relative','prior']

def view_terms(c,ch,obj,q,cid):
 m=ch.mesh(q);fr=c.fragments(m,cid);base,alpha,w,*_=c.aware(fr,cid,True);t=c.views[cid]['target'];fg=((1-alpha)**2*t).sum()/t.sum().clamp_min(1);known=w*(1-t);fp=(alpha**2*known).sum()/known.sum().clamp_min(1);cd,_=obj.contour(ch.vertices(q),cid);ramp=.25+.75*min(1.,obj.attempt/40.)
 terms=dict(silhouette=obj.w[cid]*base,missing=obj.w[cid]*ramp*.05*fg,extra=obj.w[cid]*ramp*.05*fp,contour=obj.w[cid]*ramp*.01*cd)
 exact=obj.w[cid]*(base+ramp*(.05*fg+.05*fp+.01*cd))
 if cid in obj.depth.obs:
  ab,rel,_,_=obj.depth.terms(m,cid,'E3');terms.update(absolute=obj.dw[cid]*.01*ab,relative=obj.dw[cid]*.01*rel);exact+=obj.dw[cid]*(.01*ab+.01*rel)
 obj._last_exact_view_loss=exact
 return terms,m

def gradient(t,q,retain=True):
 g=torch.autograd.grad(t,q,retain_graph=retain,allow_unused=True)[0]
 return torch.zeros_like(q)if g is None else g.detach()

def direction_cos(a,b):return float((a*b).sum()/(a.norm()*b.norm()).clamp_min(1e-30))

def instrument(c,ch,obj,q):
 obj.depth.begin(ch.mesh(q));G={k:torch.zeros_like(q)for k in NAMES};per={};rows=[];correspondence={};samegraph=[]
 for cid in c.fit:
  terms,m=view_terms(c,ch,obj,q,cid);joint=gradient(sum(terms.values()),q);twice=gradient(sum(terms.values()),q);comp={k:gradient(t,q)for k,t in terms.items()};summed=sum(comp.values());den=joint.norm().clamp_min(1e-20)
  samegraph.append(dict(view=cid,component_sum_vs_joint_relative_error=float((summed-joint).norm()/den),repeat_same_graph_relative_error=float((twice-joint).norm()/den),component_norm_sum_over_joint=float(sum(g.norm()for g in comp.values())/den)))
  for k,g in comp.items():G[k]+=g;rows.append(dict(view=cid,component=k,weighted_value=float(terms[k].detach()),gradient_norm=float(g.norm()),finite=bool(torch.isfinite(g).all())))
  per[cid]={k:g.cpu().numpy()for k,g in comp.items()}
  if cid in obj.contour.last:correspondence[cid]={k:np.array(v).copy()for k,v in obj.contour.last[cid].items()}
 prior=relative_total(obj.prior(ch.mesh(q)));G['prior']=gradient(prior,q);rows.append(dict(view='ALL',component='prior',weighted_value=float(prior.detach()),gradient_norm=float(G['prior'].norm()),finite=bool(torch.isfinite(G['prior']).all())))
 total=sum(G.values());old,parts=obj.compute(q,True);err=float((total-q.grad).norm()/q.grad.norm().clamp_min(1e-20));image=sum(G[k]for k in NAMES[:4]);depth=G['absolute']+G['relative']
 return G,per,correspondence,dict(parts=parts,component_rows=rows,same_graph=samegraph,additivity_relative_error=err,threshold=1e-4,pass_additivity=err<1e-4,image_depth_cosine=direction_cos(image,depth),image_prior_cosine=direction_cos(image,G['prior']),full_gradient_norm=float(q.grad.norm()),all_finite=all(x['finite']for x in rows))

def projection_jacobian(P,K,T):
 X=(P-T[:3,3])@T[:3,:3];z=X[:,2];J=np.zeros((len(P),2,3));J[:,0,0]=K[0,0]/z;J[:,0,2]=-K[0,0]*X[:,0]/z**2;J[:,1,1]=K[1,1]/z;J[:,1,2]=-K[1,1]*X[:,1]/z**2
 return J@T[:3,:3].T

def observability(c,V,correspondence,obj):
 H=np.zeros((len(V),3,3));Hupper=H.copy();viewcount=np.zeros(len(V),int);rows=[]
 edge_face={tuple(e):adj.tolist()for e,adj in zip(obj.contour.edges,obj.contour.adj)}
 for cid,a in correspondence.items():
  eid=a['eid'];tt=a['t'];P=(1-tt[:,None])*V[eid[:,0]]+tt[:,None]*V[eid[:,1]];d=c.views[cid];cam=(P-d['T'][:3,3])@d['T'][:3,:3];uv=(cam@d['K'].T);uv=uv[:,:2]/uv[:,2,None];nn=a['nn'];delta=uv[nn]-a['target_contour_uv'];norm=np.linalg.norm(delta,axis=1);n2=delta/np.maximum(norm[:,None],1e-12);J=projection_jacobian(P,d['K'],d['T']);jr=np.einsum('bi,bij->bj',n2,J[nn]);jt=J[nn];b=np.c_[1-tt[nn],tt[nn]];touched=set()
  for k in range(2):
   ids=eid[nn,k];part=obj.w[cid]*b[:,k]**2/max(1,len(nn));np.add.at(H,ids,part[:,None,None]*jr[:,:,None]*jr[:,None,:]);np.add.at(Hupper,ids,part[:,None,None]*np.einsum('bki,bkj->bij',jt,jt));touched.update(ids.tolist())
  viewcount[list(touched)]+=1
  for j in range(len(nn)):
   rows.append(dict(view=cid,target_uv=a['target_contour_uv'][j],predicted_uv=uv[nn[j]],residual_px=float(norm[j]),edge_vertex_ids=eid[nn[j]],original_adjacent_face_ids=edge_face[tuple(eid[nn[j]])],edge_barycentric=b[j],world_point_mm=P[nn[j]],jacobian_row_pixel_per_mm=jr[j],association='nearest current visible contour edge; no certified physical correspondence'))
 eigen=np.linalg.eigvalsh(H);upper=np.linalg.eigvalsh(Hupper);rank=(eigen>np.maximum(eigen[:,-1,None]*1e-4,1e-10)).sum(1);condition=np.divide(eigen[:,-1],eigen[:,0],out=np.full(len(V),np.inf),where=eigen[:,0]>1e-10)
 return dict(H=H,H_pixel_upper=Hupper,eigenvalues=eigen,upper_eigenvalues=upper,rank=rank,condition=condition,associated_view_count=viewcount),rows
