from multiview import *
from normalized_local import local_normalized
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');name=ap.parse_args().case;guard_optimizer();cfg=load(R/'config/ARM.json');c=Case(name);ch=FreeVertices(c);ch.total_trust_D=1.;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch,cfg['loss']);gg=GeometryGuard(c,ch);torch.manual_seed(20261108);np.random.seed(20261108);opt=torch.optim.Adam([q],lr=.02);folder=R/'local_results'/name;folder.mkdir(parents=True,exist_ok=True);assert not(folder/'FINAL.npz').exists();accepted=0;stall=0;history=[];trials=[];start=time.time();reasonfirst=set()
 def snap(label,it):
  V=ch.vertices(q).detach().cpu().numpy();np.savez_compressed(folder/(label+'.npz'),V=V,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,boundary_vertex=c.boundary,parameters=q.detach().cpu().numpy(),attempt=it,accepted=accepted);trimesh.Trimesh(V,c.F_solid,process=False).export(folder/(label+'_mm.ply'));torch.save(dict(parameters=q.detach().cpu(),optimizer=opt.state_dict(),attempt=it,accepted=accepted,torch_state=torch.get_rng_state(),numpy_state=np.random.get_state(),cuda_state=torch.cuda.get_rng_state(),config=cfg),folder/(label+'.pt'))
 snap('INITIAL',0);status='MAX_PROPOSALS'
 for it in range(1,cfg['budget']['max_proposals']+1):
  obj.attempt=it;oldloss,parts=obj.compute(q,True);grad=q.grad.detach().clone();before=q.detach().clone();oldV=ch.vertices(q).detach().cpu().numpy();state=copy.deepcopy(opt.state_dict());lr=state['param_groups'][0]['lr']
  if not np.isfinite(oldloss)or not torch.isfinite(grad).all():status='STOPPED_NONFINITE';break
  opt.step();proposal=q.detach().clone();propstate=copy.deepcopy(opt.state_dict());directions=[('ADAM',proposal-before),('STEEPEST_RESTART',-.02*grad)]+local_normalized(ch,before,grad)
  with torch.no_grad():q.copy_(before)
  opt.load_state_dict(state);done=False;reasons=[];alpha=0.;check={};method=None
  for method,d in directions:
   move=float((ch.vertices(before+d).detach()-tensor(oldV,torch.float64)).norm(dim=1).max());d=d*min(1.,ch.tau/max(move,1e-15))
   for ls in range(8):
    aa=.5**ls;candidate=before+aa*d;V=ch.vertices(candidate).detach().cpu().numpy();why,check,geo=gg.inspect(V,oldV);nl=None
    if check['max_step_mm']<1e-9:why.append('ZERO_GEOMETRIC_STEP')
    if not why:
     with torch.no_grad():nl,testparts=obj.compute(candidate,False)
     if not np.isfinite(nl):why.append('NONFINITE_OBJECTIVE')
     elif nl>oldloss+1e-7:why.append('FULL_FIT_OBJECTIVE')
    trials.append(dict(attempt=it,method=method,alpha=aa,accepted=not why,reasons=why,objective_before=oldloss,objective_candidate=nl,**check))
    if why:
     reasons+=why;key=why[0]
     if key not in reasonfirst:reasonfirst.add(key);np.savez_compressed(folder/('REJECTED_'+key+'.npz'),V=V,before_V=oldV,F=c.F,F_solid=c.F_solid,reason=np.array(why),attempt=it)
     continue
    with torch.no_grad():q.copy_(candidate)
    opt.load_state_dict(propstate)
    if method!='ADAM':opt.state[q].clear()
    gg.lastsd,gg.lastreverse=geo;accepted+=1;stall=0;oldloss=nl;parts=testparts;done=True;alpha=aa;break
   if done:break
  if not done:
   with torch.no_grad():q.copy_(before)
   opt.load_state_dict(state);assert state_equal(opt.state_dict(),state);stall+=1;opt.param_groups[0]['lr']=max(1e-5,lr*.5)
  else:opt.param_groups[0]['lr']=.02 if method=='STEEPEST_RESTART'else min(.02,lr*1.05)if alpha==1 else lr
  V=ch.vertices(q).detach().cpu().numpy();rec=dict(case=name,attempt=it,accepted=done,accepted_total=accepted,stall=stall,method=method if done else None,alpha=alpha,objective=oldloss,gradient_norm=float(grad.norm()),max_step_mm=float(np.linalg.norm(V-oldV,axis=1).max()),max_total_mm=float(np.linalg.norm(V-c.V,axis=1).max()),lr=opt.param_groups[0]['lr'],parts=parts,reasons=list(dict.fromkeys(reasons)));history.append(rec)
  if done and accepted in [1,10,20,40,60,80]:snap('ACCEPTED_%04d'%accepted,it)
  if it%10==0:save('metrics/'+name+'_TRAINING.json',history);save('metrics/'+name+'_CANDIDATES.json',trials);print('TRAIN014',name,cfg['tag'],it,accepted,stall,oldloss,flush=True)
  if accepted>=cfg['budget']['max_accepted']:status='ACCEPTED_TARGET_REACHED';break
  if stall>=cfg['budget']['consecutive_rejection_stop']:status='FIXED_STALL_STOP';break
 snap('FINAL',len(history));save('metrics/'+name+'_TRAINING.json',history);save('metrics/'+name+'_CANDIDATES.json',trials);save('metrics/'+name+'_RUN.json',dict(case=name,tag=cfg['tag'],attempts=len(history),accepted=accepted,status=status,seconds=time.time()-start,views=len(c.fit),vertices=len(c.V),faces=len(c.F_solid),maximum_displacement_mm=float(np.linalg.norm(V-c.V,axis=1).max()),peak_GPU_bytes=torch.cuda.max_memory_allocated(),initial_Ring_min_mm=float(gg.sd0.min()),final_Ring_min_mm=float(gg.lastsd.min()),GT_read=False));print('TRAIN014_DONE',name,cfg['tag'],status,accepted,flush=True)
if __name__=='__main__':main()
