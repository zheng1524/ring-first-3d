"""Inherited PyTorch3D/Ring-Aware + D2 E3 losses, with identical progressive P/S schedule."""
from depth_terms import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');ap.add_argument('route',choices=['P','S']);args=ap.parse_args();guard_optimizer();cfg=load(R/'config/PROTOCOL.json');assert load(R/'metrics/PREFLIGHT.json')['passed'];assert load(R/'metrics/PROJECTION_GATE.json')['passed']
 for aa in load(R/'assets_index/PREOPT_FREEZE.json')['files']:assert sha(aa['path'])==aa['sha256'],aa['path']
 c=Case(args.case,args.route);c.name=args.case+'_'+args.route;prior=RelativePrior(c);depth=D2Depth(c);torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);out=R/'local_results'/args.case/args.route;out.mkdir(parents=True,exist_ok=True);assert not(out/'FINAL.npz').exists();v0=c.base.verts_packed().detach();F=c.base.faces_packed();q=torch.zeros(6,device=device,requires_grad=True);off=torch.zeros_like(v0,requires_grad=True);origin=v0;stage='GLOBAL6';params=[q];opt=torch.optim.SGD(params,lr=1.,momentum=.9);boundary=tensor(c.boundary,torch.bool);bs=load(R/'inputs'/args.case/'BASE_SELECTION.json');plane=None if not boundary.any()else np.asarray(bs['selected_plane']);h0=None if plane is None else float((plane[:3]@c.center+plane[3])/c.scale);normal=None if plane is None else tensor(plane[:3]);steps=0;accepted=0;hist=[];trace=[];status='COMPLETED';t0=time.time();peak0=torch.cuda.memory_allocated()
 def current():
  v=v0*q[3:].exp()+q[:3]if stage=='GLOBAL6'else origin+off
  if plane is not None:v=v-torch.where(boundary[:,None],((v*normal).sum(1)+h0)[:,None]*normal,torch.zeros_like(v))
  return v,Meshes(verts=[v],faces=[F])
 def snap(step,label=None):
  v,m=current();V,ff=c.mm(m);tag=label or'STEP_%04d'%step;np.savez_compressed(out/(tag+'.npz'),V=V,F=ff,F_solid=c.F_solid,inferred_base_faces=c.inferred,boundary_vertex=c.boundary,step=step,stage=stage,global_q=q.detach().cpu().numpy(),local=off.detach().cpu().numpy(),origin=origin.detach().cpu().numpy(),center=c.center,scale=c.scale);trimesh.Trimesh(V,c.F_solid,process=False).export(out/(tag+'_mm.ply'));torch.save(dict(step=step,stage=stage,global_q=q.detach().cpu(),local=off.detach().cpu(),origin=origin.detach().cpu(),optimizer=opt.state_dict(),numpy_state=np.random.get_state(),torch_state=torch.get_rng_state(),cuda_state=torch.cuda.get_rng_state(),config=cfg),out/(tag+'.pt'))
 snap(0);volume0=float(trimesh.Trimesh(c.V,c.F_solid,process=False).volume)
 for i in range(cfg['steps']):
  if i==100:
   v,_=current();origin=v.detach();off=torch.zeros_like(origin,requires_grad=True);stage='LOCAL';params=[off];opt=torch.optim.SGD(params,lr=1.,momentum=.9);snap(i,'STAGE2_START')
  tick=time.time();opt.zero_grad();v,m=current();before=v.detach().clone();chosen=np.random.permutation(len(c.fit))[:2];sil=sum(c.loss(m,c.fit[j],'RingAware')for j in chosen)/len(chosen);pr=prior(m);reg=relative_total(pr);ab=sil*0;rel=sil*0;infos=[];depth.begin(m)
  for j in chosen:
   cid=c.fit[j]
   if cid not in depth.obs:continue
   aa,bb,info,query=depth.terms(m,cid,'E3');ab+=aa/len(chosen);rel+=bb/len(chosen);infos.append(dict(case=args.case,route=args.route,step=i+1,**info))
  total=sil+reg+.01*ab+.01*rel;diag=None
  if i+1 in[1,50,100,150,200,300]:
   diag=dict(before_V=before.cpu().numpy()*c.scale+c.center,F=c.F,views=np.array([c.fit[j]for j in chosen]),stage=stage)
   for key,L in[('silhouette',sil),('prior',reg),('absolute',.01*ab),('relative',.01*rel)]:
    g=torch.autograd.grad(L,v,retain_graph=True,allow_unused=True)[0];diag[key+'_gradient_per_mm']=g.detach().cpu().numpy()/c.scale if g is not None else np.zeros_like(c.V)
   diag['momentum_before']=opt.state[params[0]].get('momentum_buffer',torch.zeros_like(params[0])).detach().cpu().numpy()
  total.backward();gn=float(torch.sqrt(sum((p.grad**2).sum()for p in params)));reason=None
  if not torch.isfinite(total)or not all(torch.isfinite(p.grad).all()for p in params):reason='NONFINITE_LOSS_OR_GRADIENT'
  elif gn>100:reason='GRADIENT_OVER_100'
  if reason:status='STOPPED_'+reason;snap(accepted,'LAST_SAFE');break
  opt.step();steps+=1;v,m=current();candidate=v.detach();V,ff=c.mm(m);solid=trimesh.Trimesh(V,c.F_solid,process=False);ratio=float(solid.volume/volume0);disp=float((candidate-before).norm(dim=1).max())*c.scale
  if not np.isfinite(V).all()or disp>2 or not(.1<=ratio<=10):status='STOPPED_UNSAFE_CANDIDATE';snap(steps,'UNSAFE_CANDIDATE');np.savez_compressed(out/'LAST_SAFE.npz',V=before.cpu().numpy()*c.scale+c.center,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,boundary_vertex=c.boundary,step=accepted);break
  accepted+=1
  if diag is not None:diag.update(after_V=V,actual_displacement_mm=V-diag['before_V'],momentum_after=opt.state[params[0]]['momentum_buffer'].detach().cpu().numpy());np.savez_compressed(out/('MECHANISM_%04d.npz'%(i+1)),**diag)
  torch.cuda.synchronize();hist.append(dict(case=args.case,route=args.route,step=i+1,stage=stage,views=[c.fit[j]for j in chosen],silhouette=float(sil.detach()),absolute_depth=float(ab.detach()),relative_depth=float(rel.detach()),prior=float(reg.detach()),total=float(total.detach()),gradient_norm=gn,max_step_mm=disp,max_displacement_initial_mm=float((candidate-v0).norm(dim=1).max())*c.scale,volume_diagnostic_only_mm3=float(solid.volume),volume_ratio_initial=ratio,seconds_per_step=time.time()-tick,elapsed_seconds=time.time()-t0,**{k:float(x.detach())for k,x in pr.items()}));trace+=infos
  if i+1 in cfg['checkpoints']:snap(i+1)
  if(i+1)%50==0:print(args.case,args.route,i+1,stage,'loss',hist[-1]['total'],'volume_diagnostic',ratio,flush=True)
 if status=='COMPLETED':snap(steps,'FINAL')
 table('metrics/'+args.case+'_'+args.route+'_TRAINING.csv',hist);table('metrics/'+args.case+'_'+args.route+'_DEPTH_TRACE.csv',trace);save('metrics/'+args.case+'_'+args.route+'_RUN.json',dict(case=args.case,route=args.route,status=status,optimizer_steps=steps,accepted_steps=accepted,elapsed_seconds=time.time()-t0,peak_GPU_bytes=torch.cuda.max_memory_allocated(),GT_mesh_read=False,camera_updated=False,depth_updated=False,cross_view_depth_consistency_used=False,stage2_momentum_reset=True,cap_observation_faces_excluded=True,initial_volume_diagnostic_only_mm3=volume0));print('FINISHED',args.case,args.route,status,steps,flush=True)
if __name__=='__main__':main()
