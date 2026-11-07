from free_model import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');name=ap.parse_args().case;guard_optimizer();cfg=load(R/'config/PROTOCOL.json')
 for a in load(R/'assets_index/PREOPT_FREEZE.json')['files']:assert sha(a['path'])==a['sha256'],a['path']
 c=Case(name);ch=FreeVertices(c);obj=Objective(c,ch);guard=GeometryGuard(c,ch);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);opt=torch.optim.Adam([q],lr=.02,betas=(.9,.999));torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);folder=R/'local_results'/name;folder.mkdir(exist_ok=True);assert not(folder/'FINAL.npz').exists();hist=[];trials=[];accepted=0;stall=0;restarts=0;commits=0;start=time.time();first_rejected=set();status='MAX_PROPOSALS'
 with torch.no_grad():oldloss,parts=obj(q);oldloss=float(oldloss)
 def snap(label,attempt):
  V=ch.vertices(q).detach().cpu().numpy();np.savez_compressed(folder/(label+'.npz'),V=V,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,boundary_vertex=c.boundary,parameters=q.detach().cpu().numpy(),attempt=attempt,accepted=accepted);trimesh.Trimesh(V,c.F_solid,process=False).export(folder/(label+'_mm.ply'));torch.save(dict(attempt=attempt,accepted=accepted,parameters=q.detach().cpu(),optimizer=opt.state_dict(),torch_state=torch.get_rng_state(),cuda_state=torch.cuda.get_rng_state(),numpy_state=np.random.get_state(),config=cfg),folder/(label+'.pt'))
 snap('ACCEPTED_0000',0)
 for it in range(1,cfg['max_proposals']+1):
  opt.zero_grad();loss,rawparts=obj(q);loss.backward();grad=q.grad.detach().clone();before=q.detach().clone();oldV=ch.vertices(q).detach().cpu().numpy();state=copy.deepcopy(opt.state_dict());lr=state['param_groups'][0]['lr']
  if not torch.isfinite(loss)or not torch.isfinite(grad).all():status='STOPPED_NONFINITE';break
  opt.step();proposal=q.detach().clone();propstate=copy.deepcopy(opt.state_dict());delta=proposal-before
  with torch.no_grad():q.copy_(before)
  opt.load_state_dict(state);directions=[('ADAM',delta),('STEEPEST_RESTART',-.02*grad)];done=False;reasons=[];used_alpha=0.;method=None;lastcheck={}
  for method,d in directions:
   move=np.linalg.norm(ch.vertices(before+d).detach().cpu().numpy()-oldV,axis=1).max();d=d*min(1.,ch.tau/max(move,1e-15))
   for ls in range(8):
    alpha=.5**ls;candidate=before+alpha*d;V=ch.vertices(candidate).detach().cpu().numpy();why,check,geo=guard.inspect(V,oldV);nl=None;lastcheck=check
    if check['max_step_mm']<1e-9:why.append('ZERO_GEOMETRIC_STEP')
    if not why:
     with torch.no_grad():testloss,testparts=obj(candidate);nl=float(testloss)
     if not np.isfinite(nl):why.append('NONFINITE_OBJECTIVE')
     elif nl>oldloss+1e-7:why.append('FULL_FIT_OBJECTIVE')
    trials.append(dict(case=name,attempt=it,method=method,alpha=alpha,accepted=not why,reasons=list(why),objective_before=oldloss,objective_candidate=nl,**check))
    if why:
     reasons.extend(why)
     category='RING'if any('RING'in x or'CAD'in x for x in why)else'OBJECTIVE'if 'FULL_FIT_OBJECTIVE'in why else'GEOMETRY'
     if category not in first_rejected:
      first_rejected.add(category);np.savez_compressed(folder/('REJECTED_FIRST_'+category+'.npz'),V=V,before_V=oldV,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,parameters=candidate.detach().cpu().numpy(),attempt=it,reason=np.array(why))
     continue
    with torch.no_grad():q.copy_(candidate)
    opt.load_state_dict(propstate)
    if method=='STEEPEST_RESTART':opt.state[q].clear();restarts+=1
    else:commits+=1
    guard.lastsd,guard.lastreverse=geo;accepted+=1;stall=0;oldloss=nl;parts=testparts;done=True;used_alpha=alpha;break
   if done:break
  if not done:
   with torch.no_grad():q.copy_(before)
   opt.load_state_dict(state);assert state_equal(opt.state_dict(),state)and torch.equal(q,before);opt.param_groups[0]['lr']=max(1e-5,lr*.5);stall+=1
  else:opt.param_groups[0]['lr']=.02 if method=='STEEPEST_RESTART'else min(.02,lr*1.05)if used_alpha==1 else lr
  V=ch.vertices(q).detach().cpu().numpy();hist.append(dict(case=name,attempt=it,accepted=done,accepted_total=accepted,consecutive_rejections=stall,accepted_method=method if done else None,alpha=used_alpha,loss=oldloss,gradient_norm=float(grad.norm()),actual_step_mm=float(np.linalg.norm(V-oldV,axis=1).max()),max_total_displacement_mm=float(np.linalg.norm(V-c.V,axis=1).max()),lr=opt.param_groups[0]['lr'],rejection_reasons=list(dict.fromkeys(reasons)),parts=parts,last_candidate_check=lastcheck))
  if done and accepted in cfg['accepted_checkpoints']:snap('ACCEPTED_%04d'%accepted,it)
  if it in cfg['attempt_checkpoints']:snap('ATTEMPT_%04d'%it,it)
  if it%25==0:print(name,it,'accepted',accepted,'stall',stall,'loss',oldloss,flush=True)
  if accepted>=cfg['max_accepted']:status='ACCEPTED_TARGET_REACHED';break
  if stall>=cfg['consecutive_rejection_stop']:status='NO_ACCEPTANCE_FOR_80_ATTEMPTS';break
 snap('FINAL',len(hist));save('metrics/'+name+'_TRAINING.json',hist);table('metrics/'+name+'_TRAINING.csv',hist);save('metrics/'+name+'_CANDIDATES.json',trials);table('metrics/'+name+'_CANDIDATES.csv',trials);save('metrics/'+name+'_RUN.json',dict(case=name,status=status,attempts=len(hist),accepted=accepted,Adam_committed=commits,gradient_restarts=restarts,allocated_parameters=3*ch.N,independent_parameters=3*len(ch.used)-int(c.boundary.sum())if ch.cap else 3*ch.N,surface_topology_unchanged=True,all_rejections_exact_rollback=True,seconds=time.time()-start,peak_GPU_bytes=torch.cuda.max_memory_allocated(),GT_read=False,initial_source='exact011FINAL',maximum_displacement_mm=float(np.linalg.norm(V-c.V,axis=1).max())));print('DONE',name,status,accepted,len(hist),flush=True)

if __name__=='__main__':main()
