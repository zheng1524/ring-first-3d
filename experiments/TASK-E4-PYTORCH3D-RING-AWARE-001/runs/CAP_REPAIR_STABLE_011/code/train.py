"""Nine same-code guarded Adam routes, final accepted state after fixed proposal budget."""
from stable import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');name=ap.parse_args().case;guard_optimizer();cfg=load(R/'config/PROTOCOL.json')
 for a in load(R/'assets_index/PREOPT_FREEZE.json')['files']:assert sha(a['path'])==a['sha256'],a['path']
 assert load(R/'metrics/PREFLIGHT.json')['passed'];c=Case(name);ch=Chart(c);objective=Objective(c,ch);guard=GeometryGuard(c,ch);q=torch.zeros(54,device=device,dtype=torch.float64,requires_grad=True);optimizer=torch.optim.Adam([q],lr=.02,betas=(.9,.999));torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);folder=R/'local_results'/name;folder.mkdir(exist_ok=True);assert not(folder/'FINAL.npz').exists();history=[];trials=[];accepted=0;stage='GLOBAL';modes=0;stageaccepted={'GLOBAL':0,'LOW':0,'DETAIL':0};start=time.time();rejected_saved=set();status='COMPLETED';qpcounts=0;rollback_ok=True
 with torch.no_grad():oldloss,oldparts=objective(q);oldloss=float(oldloss)
 def snap(step,tag=None):
  V=ch.vertices(q).detach().cpu().numpy();label=tag or'STEP_%04d'%step;np.savez_compressed(folder/(label+'.npz'),V=V,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,boundary_vertex=c.boundary,parameters=q.detach().cpu().numpy(),step=step,accepted=accepted,stage=stage,active_modes=modes);trimesh.Trimesh(V,c.F_solid,process=False).export(folder/(label+'_mm.ply'));torch.save(dict(step=step,accepted=accepted,stage=stage,active_modes=modes,parameters=q.detach().cpu(),optimizer=optimizer.state_dict(),numpy_state=np.random.get_state(),torch_state=torch.get_rng_state(),cuda_state=torch.cuda.get_rng_state(),config=cfg),folder/(label+'.pt'))
 snap(0)
 for it in range(cfg['steps']):
  if it==60 and stageaccepted['GLOBAL']>=5:stage='LOW';modes=16
  if it==180 and stage=='LOW'and stageaccepted['LOW']>=10:stage='DETAIL';modes=48
  active=np.arange(6+modes);mask=torch.zeros(54,device=device,dtype=torch.float64);mask[active]=1;optimizer.zero_grad();loss,parts=objective(q);loss.backward();grad=q.grad.detach().clone()*mask;q.grad.copy_(grad);before=q.detach().clone();oldV=ch.vertices(q).detach().cpu().numpy();state=copy.deepcopy(optimizer.state_dict());lr=state['param_groups'][0]['lr'];gn=float(grad.norm())
  if not torch.isfinite(loss)or not torch.isfinite(grad).all():status='STOPPED_NONFINITE';break
  optimizer.step();proposed=q.detach().clone();proposal_state=copy.deepcopy(optimizer.state_dict());delta=(proposed-before).cpu().numpy();delta[np.setdiff1d(np.arange(54),active)]=0
  with torch.no_grad():q.copy_(before)
  optimizer.load_state_dict(state);rawV=ch.vertices(before+tensor(delta,torch.float64)).detach().cpu().numpy();rawmove=float(np.linalg.norm(rawV-oldV,axis=1).max());proposal_scale=min(1.,ch.tau/max(rawmove,1e-15));delta*=proposal_scale;directions=[('RAW',delta)];done=False;reasons_seen=[];checks={};newstate=None;used_alpha=0;qpinfo=None
  for method,direction in directions:
   need_projection=False
   for ls in range(8):
    alpha=.5**ls;candidate=np.clip(before.cpu().numpy()+alpha*direction,ch.lo,ch.hi);test=tensor(candidate,torch.float64);V=ch.vertices(test).detach().cpu().numpy();why,checks,geo=guard.inspect(V,oldV);nl=None;npv=None
    if checks['max_step_mm']<1e-9:why.append('ZERO_GEOMETRIC_STEP')
    if not why:
     with torch.no_grad():tL,npv=objective(test);nl=float(tL)
     if not np.isfinite(nl):why.append('NONFINITE_OBJECTIVE')
     elif nl>oldloss+1e-7:why.append('FULL_FIT_OBJECTIVE')
    trials.append(dict(case=name,iteration=it+1,stage=stage,method=method,backtrack=ls,alpha=alpha,accepted=not why,reasons=why,objective_before=oldloss,objective_candidate=nl,parameters=candidate,**checks))
    if why:
     reasons_seen.extend(why);need_projection|=any('RING'in r or'CAD'in r for r in why)
     if stage not in rejected_saved:
      rejected_saved.add(stage);np.savez_compressed(folder/('REJECTED_FIRST_'+stage+'.npz'),V=V,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,parameters=candidate,before_V=oldV,reason=np.array(why),step=it+1,method=method)
     continue
    with torch.no_grad():q.copy_(test)
    optimizer.load_state_dict(proposal_state);guard.lastsd,guard.lastreverse=geo;accepted+=1;stageaccepted[stage]+=1;done=True;oldloss=nl;oldparts=npv;used_alpha=alpha;newstate=optimizer.state_dict();break
   if done:break
   if method=='RAW'and need_projection:
    projected,qpinfo=active_contact_projection(ch,guard,before,direction,active);qpcounts+=1
    if projected is not None and np.linalg.norm(projected)>1e-12:directions.append(('CONTACT_QP',projected))
  if not done:
   with torch.no_grad():q.copy_(before)
   optimizer.load_state_dict(state);restored=state_equal(optimizer.state_dict(),state)and torch.equal(q.detach(),before);rollback_ok&=restored;assert restored;optimizer.param_groups[0]['lr']=max(1e-5,lr*.5)
  else:optimizer.param_groups[0]['lr']=min(.02,lr*1.05)if used_alpha==1 else lr
  afterV=ch.vertices(q).detach().cpu().numpy();stepmove=float(np.linalg.norm(afterV-oldV,axis=1).max());history.append(dict(case=name,iteration=it+1,stage=stage,active_modes=modes,accepted=done,accepted_total=accepted,accepted_loss=oldloss,gradient_norm=gn,lr_before=lr,lr_after=optimizer.param_groups[0]['lr'],proposal_max_unscaled_mm=rawmove,proposal_scale=proposal_scale,accepted_alpha=used_alpha,max_actual_step_mm=stepmove,total_displacement_mm=float(np.linalg.norm(afterV-c.V,axis=1).max()),backtracks=len([x for x in trials if x['iteration']==it+1 and not x['accepted']]),reasons=list(dict.fromkeys(reasons_seen)),QP=qpinfo,parts=oldparts,**checks));
  if it+1 in cfg['checkpoints']:snap(it+1)
  if(it+1)%25==0:print(name,it+1,stage,'accepted',accepted,'L',oldloss,'lr',optimizer.param_groups[0]['lr'],flush=True)
 snap(len(history),'FINAL');table('metrics/'+name+'_TRAINING.csv',history);save('metrics/'+name+'_TRAINING.json',history);table('metrics/'+name+'_CANDIDATES.csv',trials);save('metrics/'+name+'_CANDIDATES.json',trials);save('metrics/'+name+'_RUN.json',dict(case=name,status=status,outer_iterations=len(history),accepted_optimizer_steps=accepted,rejected_outer_iterations=len(history)-accepted,Adam_moment_updates=accepted,all_rejections_rollback_exact=rollback_ok,stages_accepted=stageaccepted,final_active_modes=modes,seconds=time.time()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated(),QP_calls=qpcounts,GT_read=False,no_camera_or_HERO_update=True,raw_initial_C_source=asset(R/'inputs'/name/'INITIAL.npz')));print('DONE',name,accepted,len(history),flush=True)
if __name__=='__main__':main()
