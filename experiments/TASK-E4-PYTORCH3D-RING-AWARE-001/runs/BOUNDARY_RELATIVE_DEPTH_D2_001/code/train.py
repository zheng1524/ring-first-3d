from depth_terms import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');ap.add_argument('arm',choices=['B','E1','E2','E3']);args=ap.parse_args();guard_optimizer();cfg=load(R/'config/PROTOCOL.json');assert load(R/'metrics/PREFLIGHT.json')['passed'];assert load(R/'metrics/PROJECTION_GATE.json')['passed'];freeze=load(R/'assets_index/PREOPT_FREEZE.json');
 for aa in freeze['files']:assert sha(aa['path'])==aa['sha256']
 c=Case(args.case);prior=RelativePrior(c);depth=D2Depth(c)if args.arm!='B'else None;torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);out=R/'local_results'/args.case/args.arm;out.mkdir(parents=True,exist_ok=True);assert not(out/'FINAL.npz').exists();v0=c.base.verts_packed().detach();off=torch.zeros_like(v0,requires_grad=True);F=c.base.faces_packed();opt=torch.optim.SGD([off],lr=1.,momentum=.9);steps=0;hist=[];trace=[];status='COMPLETED';t0=time.time()
 def current():return Meshes(verts=[v0+off],faces=[F])
 def snap(step):
  V,ff=c.mm(current());tag='STEP_%04d'%step;np.savez_compressed(out/(tag+'.npz'),V=V,F=ff,step=step);trimesh.Trimesh(V,ff,process=False).export(out/(tag+'_mm.ply'));torch.save(dict(step=step,offset=off.detach().cpu(),optimizer=opt.state_dict(),numpy_state=np.random.get_state(),torch_state=torch.get_rng_state(),cuda_state=torch.cuda.get_rng_state(),config=cfg),out/(tag+'.pt'))
 snap(0)
 for i in range(300):
  opt.zero_grad();m=current();before=m.verts_packed().detach().clone();chosen=np.random.permutation(len(c.fit))[:2];sil=sum(c.loss(m,c.fit[j],'RingAware')for j in chosen)/len(chosen);pr=prior(m);reg=relative_total(pr);ab=sil*0;rel=sil*0;infos=[]
  if depth:
   depth.begin(m)
   for j in chosen:
    aa,bb,info,q=depth.terms(m,c.fit[j],args.arm);ab+=aa/len(chosen);rel+=bb/len(chosen);infos.append(dict(case=args.case,arm=args.arm,step=i+1,**info))
  total=sil+reg+(.01*ab if depth else 0.)+(.01*rel if args.arm=='E3'else 0.);diag=None
  if(i+1)in[1,50,100,200,300]:
   diag=dict(before_V=before.cpu().numpy()*c.scale+c.center,F=c.F,views=np.array([c.fit[j]for j in chosen]))
   for key,L in [('silhouette',sil),('prior',reg),('absolute',.01*ab),('relative',.01*rel if args.arm=='E3'else rel*0)]:
    grad=torch.autograd.grad(L,off,retain_graph=True,allow_unused=True)[0];diag[key+'_gradient_per_mm']=grad.detach().cpu().numpy()/c.scale if grad is not None else np.zeros_like(c.V)
   diag['momentum_before']=opt.state[off].get('momentum_buffer',torch.zeros_like(off)).detach().cpu().numpy()
  total.backward();gn=float(off.grad.norm());reason=None
  if not torch.isfinite(total)or not torch.isfinite(off.grad).all():reason='NONFINITE'
  elif gn>100:reason='GRADIENT_OVER_100'
  if reason:status='STOPPED_'+reason;break
  opt.step();steps+=1;V,ff=c.mm(current());mm=trimesh.Trimesh(V,ff,process=False);disp=float((current().verts_packed().detach()-before).norm(dim=1).max())*c.scale;ratio=float(mm.volume/trimesh.Trimesh(c.V,c.F,process=False).volume)
  if disp>2 or not(.1<=ratio<=10)or not np.isfinite(V).all():status='STOPPED_UNSAFE_CANDIDATE';np.savez_compressed(out/'UNSAFE_CANDIDATE.npz',V=V,F=ff);break
  if diag is not None:
   diag.update(after_V=V,actual_displacement_mm=V-diag['before_V'],momentum_after=opt.state[off]['momentum_buffer'].detach().cpu().numpy());np.savez_compressed(out/('MECHANISM_%04d.npz'%(i+1)),**diag)
  hist.append(dict(case=args.case,arm=args.arm,step=i+1,views=[c.fit[j]for j in chosen],silhouette=float(sil.detach()),absolute_depth=float(ab.detach()),relative_depth=float(rel.detach()),prior=float(reg.detach()),total=float(total.detach()),gradient_norm=gn,volume_mm3=float(mm.volume),volume_ratio_P0=ratio,max_step_mm=disp,**{k:float(v.detach())for k,v in pr.items()}));trace+=infos
  if(i+1)in cfg['checkpoints']:snap(i+1)
  if(i+1)%50==0:print(args.case,args.arm,i+1,'L',hist[-1]['total'],'volume_ratio',ratio,flush=True)
 if status=='COMPLETED':
  V,ff=c.mm(current());np.savez_compressed(out/'FINAL.npz',V=V,F=ff);trimesh.Trimesh(V,ff,process=False).export(out/'FINAL_mm.ply')
 table('metrics/'+args.case+'_'+args.arm+'_TRAINING.csv',hist);table('metrics/'+args.case+'_'+args.arm+'_DEPTH_TRACE.csv',trace);save('metrics/'+args.case+'_'+args.arm+'_RUN.json',dict(case=args.case,arm=args.arm,status=status,optimizer_steps=steps,elapsed_seconds=time.time()-t0,peak_GPU_bytes=torch.cuda.max_memory_allocated(),GT_mesh_read=False,multiview_diagnostic_read=False,camera_updated=False))
if __name__=='__main__':main()
