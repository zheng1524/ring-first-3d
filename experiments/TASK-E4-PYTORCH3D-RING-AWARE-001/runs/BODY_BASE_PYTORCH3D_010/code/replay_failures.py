"""Post-freeze read-only gradient replay at failed global proposals; zero optimizer steps."""
from depth_terms import *

def cosine(a,b):
 d=float(a.norm()*b.norm());return float((a*b).sum()/d)if d>1e-20 else None

def main():
 rows=[];cfg=load(R/'config/PROTOCOL.json')
 for failure in load(R/'metrics/FAILURE_DIAGNOSIS.json'):
  n=failure['case'];route=failure['route'];folder=R/'local_results'/n/route;ck=torch.load(folder/'UNSAFE_CANDIDATE.pt',map_location='cpu',weights_only=False);assert ck['stage']=='GLOBAL6';qnew=ck['global_q'];state=ck['optimizer'];momentum=next(iter(state['state'].values()))['momentum_buffer'];lr=state['param_groups'][0]['lr'];q=(qnew+lr*momentum).to(device).detach().requires_grad_();c=Case(n,route);v0=c.base.verts_packed().detach();v=v0*q[3:].exp()+q[:3]
  if c.boundary.any():
   bs=load(R/'inputs'/n/'BASE_SELECTION.json');plane=np.array(bs['selected_plane']);normal=tensor(plane[:3]);h0=float((plane[:3]@c.center+plane[3])/c.scale);v=v-torch.where(tensor(c.boundary,torch.bool)[:,None],((v*normal).sum(1)+h0)[:,None]*normal,torch.zeros_like(v))
  m=Meshes(verts=[v],faces=[c.base.faces_packed()]);prior=RelativePrior.__new__(RelativePrior);prior.c=c;prior.v0=v0;prior.edges=c.base.edges_packed();prior.length0=(v0[prior.edges[:,0]]-v0[prior.edges[:,1]]).norm(dim=1).detach();prior.L=c.base.laplacian_packed().detach();prior.lap0=torch.sparse.mm(prior.L,v0).detach();prior.unknown=tensor(np.load(R/'local_results'/(n+'_'+route+'_P0_SUPPORT.npz'))['unknown'],torch.bool);depth=D2Depth(c);rng=np.random.RandomState(cfg['seed'])
  for i in range(failure['steps']):chosen=rng.permutation(len(c.fit))[:2]
  sil=sum(c.loss(m,c.fit[j],'RingAware')for j in chosen)/len(chosen);pr=relative_total(prior(m));ab=sil*0;rel=sil*0;depth.begin(m);sources=[]
  for j in chosen:
   cid=c.fit[j]
   if cid not in depth.obs:continue
   a,b,_,_=depth.terms(m,cid,'E3');ab+=a/len(chosen);rel+=b/len(chosen);sources.append(cid)
  gs={};loss={}
  for key,L in[('silhouette',sil),('shape',pr),('absolute',.01*ab),('relative',.01*rel)]:
   gs[key]=torch.autograd.grad(L,q,retain_graph=True)[0];loss[key]=float(L.detach())
  total=sum(gs.values());dep=gs['absolute']+gs['relative'];before=v.detach().cpu().numpy()*c.scale+c.center;stored=np.load(folder/'LAST_SAFE.npz')['V'];difference=float(np.linalg.norm(before-stored,axis=1).max());mb=momentum.to(device);rec=dict(case=n,route=route,rejected_step=failure['steps'],chosen_views=[c.fit[j]for j in chosen],depth_sources=sources,reconstructed_before_max_difference_mm=difference,replay_position_agrees_under_1e_4mm=difference<1e-4,weighted_losses=loss,global_parameter_gradient_norms={k:float(g.norm())for k,g in gs.items()},global_gradient_silhouette_vs_depth_cosine=cosine(gs['silhouette'],dep),negative_current_gradient_vs_actual_SGD_parameter_update_cosine=cosine(-total,-mb),actual_momentum_buffer_norm=float(mb.norm()),current_gradient_norm=float(total.norm()),momentum_is_not_single_loss_gradient=True,optimizer_steps_in_replay=0,approximate_FP32_parameter_reconstruction=True,model_changed=False);rows.append(rec);print('REPLAY',n,route,difference,flush=True)
 save('metrics/FAILED_PROPOSAL_GRADIENT_REPLAY.json',rows);table('metrics/FAILED_PROPOSAL_GRADIENT_REPLAY.csv',rows)
if __name__=='__main__':main()
