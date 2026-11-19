from hero_objective018 import *
from gate018 import configure
import access018
from normalized_local import local_normalized
from stalk import StalkChart,expanded_directions,curve_directions
import argparse
from coherent016 import coherent_directions

def main():
 assert not(Path(__file__).resolve().parents[1]/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json').exists(),'015 predictions frozen: no further optimizer updates in this run'
 ap=argparse.ArgumentParser();ap.add_argument('case');ap.add_argument('--resume',action='store_true');args=ap.parse_args();name=args.case;guard_optimizer();access018.install();cfg=load(R/'config/ARM.json');c=Case(name);configure(c);mode=cfg["tag"];ch=StalkChart(c)if mode=="Stalk-C"else FreeVertices(c);ch.total_trust_D=1.;q=torch.zeros(getattr(ch,"parameter_shape",(ch.N,3)),device=device,dtype=torch.float64,requires_grad=True);obj=Objective018(c,ch,cfg['kind'],cfg.get('HERO_views'));gg=GeometryGuard(c,ch);torch.manual_seed(20261108);np.random.seed(20261108);opt=torch.optim.Adam([q],lr=.02);folder=R/'local_results'/name;folder.mkdir(parents=True,exist_ok=True);assert not(folder/'FINAL.npz').exists();accepted=0;stall=0;history=[];trials=[];start=time.time();reasonfirst=set();start_it=0
 sources=Path(__file__).resolve().parent;snapdir=R/'provenance'/'source_snapshots';snapdir.mkdir(parents=True,exist_ok=True);source_records=[]
 for pp in sources.glob('*.py'):
  h=sha(pp);dest=snapdir/(pp.stem+'_'+h+'.py')
  if not dest.exists():dest.write_bytes(pp.read_bytes())
  source_records.append(dict(name=pp.name,sha256=h,snapshot=str(dest)))
 save('provenance/'+name+('_RESUME_SOURCE.json'if args.resume else'_OPT_START.json'),dict(epoch=time.time(),files=source_records,input=asset(R/'inputs'/name/'INITIAL.npz'),config=asset(R/'config/ARM.json'),GT_used=False))
 if args.resume:
  checkpoints=list(folder.glob('*.pt'));assert checkpoints,'No exact optimizer checkpoint';p=max(checkpoints,key=lambda pp:int(torch.load(pp,map_location='cpu',weights_only=False)['attempt']));a=torch.load(p,map_location=device,weights_only=False)
  with torch.no_grad():q.copy_(a['parameters'])
  opt.load_state_dict(a['optimizer']);accepted=a['accepted'];start_it=a['attempt'];stall=a.get('stall',0);torch.set_rng_state(a['torch_state'].cpu());torch.cuda.set_rng_state(a['cuda_state'].cpu());np.random.set_state(a['numpy_state']);history=[v for v in load(R/'metrics'/(name+'_TRAINING.json'))if v['attempt']<=start_it];trials=[v for v in load(R/'metrics'/(name+'_CANDIDATES.json'))if v['attempt']<=start_it];V=ch.vertices(q).detach().cpu().numpy();gg.lastsd=gg.ring_distance(V);gg.lastreverse=gg.reverse(V);reasonfirst={p.stem.replace('REJECTED_','')for p in folder.glob('REJECTED_*.npz')};save('metrics/'+name+'_RESUME.json',dict(checkpoint=asset(p),optimizer_restored=True,RNG_restored=True,start_attempt=start_it,accepted=accepted,engineering_fix='equivalent negative-distance culling; unchanged density and epsilon'));print('RESUMED',name,start_it,accepted,flush=True)
 def snap(label,it):
  if mode=='Stalk-C':save('metrics/'+name+'_'+label+'_CENTERLINE.json',ch.curve_record(q))
  V=ch.vertices(q).detach().cpu().numpy();np.savez_compressed(folder/(label+'.npz'),V=V,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,boundary_vertex=c.boundary,parameters=q.detach().cpu().numpy(),attempt=it,accepted=accepted);trimesh.Trimesh(V,c.F_solid,process=False).export(folder/(label+'_mm.ply'));torch.save(dict(parameters=q.detach().cpu(),optimizer=opt.state_dict(),attempt=it,accepted=accepted,stall=stall,torch_state=torch.get_rng_state(),numpy_state=np.random.get_state(),cuda_state=torch.cuda.get_rng_state(),config=cfg),folder/(label+'.pt'))
 if not args.resume:
  snap('INITIAL',0);obj.diagnostic(q,'INITIAL')
 status='MAX_PROPOSALS'
 for it in range(start_it+1,cfg['budget']['max_proposals']+1):
  obj.attempt=it;oldloss,parts=obj.compute(q,True);grad=q.grad.detach().clone();before=q.detach().clone();oldV=ch.vertices(q).detach().cpu().numpy();state=copy.deepcopy(opt.state_dict());lr=state['param_groups'][0]['lr']
  if not np.isfinite(oldloss)or not torch.isfinite(grad).all():status='STOPPED_NONFINITE';break
  opt.step();proposal=q.detach().clone();propstate=copy.deepcopy(opt.state_dict());coverage=None
  if mode=='Stalk-C':directions=curve_directions(ch,before,grad)+[('ADAM',proposal-before),('STEEPEST_RESTART',-.02*grad)]
  else:
   extra,coverage=expanded_directions(ch,before,grad,obj)if cfg.get('mode')=='COHERENT'else([],None)
   directions=extra+[('ADAM',proposal-before),('STEEPEST_RESTART',-.02*grad)]+local_normalized(ch,before,grad)
  if cfg.get('mode')in['COHERENT','CONTACT_SOB16']:
   directions,coordination=coherent_directions(ch,before,directions,gg);coverage=dict(coverage or {},coordination=coordination)
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
    if method.removeprefix('PCOH_')!='ADAM':opt.state[q].clear()
    gg.lastsd,gg.lastreverse=geo;accepted+=1;stall=0;oldloss=nl;parts=testparts;done=True;alpha=aa;break
   if done:break
  if not done:
   with torch.no_grad():q.copy_(before)
   opt.load_state_dict(state);assert state_equal(opt.state_dict(),state);stall+=1;opt.param_groups[0]['lr']=max(1e-5,lr*.5)
  else:opt.param_groups[0]['lr']=.02 if method.removeprefix('PCOH_')=='STEEPEST_RESTART'else min(.02,lr*1.05)if alpha==1 else lr
  V=ch.vertices(q).detach().cpu().numpy();rec=dict(case=name,attempt=it,accepted=done,accepted_total=accepted,stall=stall,method=method if done else None,alpha=alpha,objective=oldloss,gradient_norm=float(grad.norm()),max_step_mm=float(np.linalg.norm(V-oldV,axis=1).max()),max_total_mm=float(np.linalg.norm(V-c.V,axis=1).max()),lr=opt.param_groups[0]['lr'],parts=parts,reasons=list(dict.fromkeys(reasons)));rec['coverage']=coverage;rec['per_view_HERO']=obj.last;history.append(rec)
  if done and accepted in [1,10,20,40]:
   snap('ACCEPTED_%04d'%accepted,it);np.savez_compressed(folder/('MECHANISM_%04d.npz'%accepted),before_V=oldV,after_V=V,F=c.F,F_solid=c.F_solid,full_loss_gradient=grad.detach().cpu().numpy(),actual_vertex_delta=V-oldV,attempt=it,accepted=accepted,method=method,alpha=alpha,gradient_units='objective_per_chart_coordinate; free residual mm and centerline mixed units when Stalk-C',vertex_delta_units='mm')
  if it%10==0:snap('ATTEMPT_%04d'%it,it);save('metrics/'+name+'_TRAINING.json',history);save('metrics/'+name+'_CANDIDATES.json',trials);print('TRAIN014',name,cfg['tag'],it,accepted,stall,oldloss,flush=True)
  if accepted>=cfg['budget']['max_accepted']:status='ACCEPTED_TARGET_REACHED';break
  if stall>=cfg['budget']['consecutive_rejection_stop']:status='FIXED_STALL_STOP';break
 obj.diagnostic(q,'FINAL');snap('FINAL',len(history));save('metrics/'+name+'_TRAINING.json',history);save('metrics/'+name+'_CANDIDATES.json',trials);save('metrics/'+name+'_RUN.json',dict(case=name,tag=cfg['tag'],attempts=len(history),accepted=accepted,status=status,seconds=time.time()-start,views=len(c.fit),vertices=len(c.V),faces=len(c.F_solid),maximum_displacement_mm=float(np.linalg.norm(V-c.V,axis=1).max()),peak_GPU_bytes=torch.cuda.max_memory_allocated(),initial_Ring_min_mm=float(gg.sd0.min()),final_Ring_min_mm=float(gg.lastsd.min()),GT_read=False));access018.flush(name);print('TRAIN014_DONE',name,cfg['tag'],status,accepted,flush=True)
if __name__=='__main__':main()
