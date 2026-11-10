from objective019 import *
import copy

def correct_scope(scope):
 p=R/'results'/(scope+'_SEARCH_SELECTION.json');data=load(p);grid=load(R/'metrics'/(scope+'_FULL_SEARCH.json'));c=load(R/'metrics'/(scope+'_SEARCH_CANDIDATES.json'));old=R/'results'/(scope+'_SEARCH_SELECTION_RAW_POOL.json')
 if not old.exists():old.write_text(json.dumps(data,indent=2)+'\n')
 data['A1']=min(grid+[x for x in c if x['source']=='CONTINUOUS_polyp'],key=lambda r:r['polyp']);data['A3']=min(grid+[x for x in c if x['source']=='CONTINUOUS_feature'or x['source'].startswith('SIFT_PNP_YAW')],key=lambda r:r['feature']);data['selection_audit']='A1 uses silhouette grid/refinement only; A3 uses feature grid/refinement/PnP only. A4 union unchanged. Scope checked before any HOLDOUT evaluation.';save('results/'+scope+'_SEARCH_SELECTION.json',data);return data

def run(scope,ids):
 data=correct_scope(scope);obj=PoseObjective(ids,scope);finals=[];torch.manual_seed(20261111)
 for ix,seed in enumerate(data['refinement_seeds']):
  folder=R/'refinement'/scope/('seed'+str(ix));folder.mkdir(parents=True,exist_ok=True);done=folder/'FINAL.json'
  if done.exists():finals.append(load(done));continue
  cand=tensor(seed['T'],torch.float64);q=torch.zeros(6,device=device,dtype=torch.float64,requires_grad=True);opt=torch.optim.Adam([q],lr=.01);hist=[];initial,ip=obj.evaluate(q,cand,False);nacc=0;start=time.time();initial_record=dict(seed=seed,loss=initial,parts=ip,pose_parameter_scale=obj.scale.detach().cpu().numpy(),variables='normalized t(.6mm), rotation(5deg); official se3_exp_map translation first')
  if not(folder/'INITIAL.json').exists():save(str(folder.relative_to(R)/'INITIAL.json'),initial_record)
  checkpoints=list(folder.glob('ITER_*.pt'));start_iteration=0
  if checkpoints:
   checkpoint=max(checkpoints,key=lambda p:int(p.stem.split('_')[1]));st=torch.load(checkpoint,map_location=device,weights_only=False)
   with torch.no_grad():q.copy_(st['q'])
   opt.load_state_dict(st['optimizer']);start_iteration=st['iteration'];hist=[x for x in load(folder/'HISTORY.json')if x['iteration']<=start_iteration];nacc=hist[-1]['accepted_total'];save(str(folder.relative_to(R)/'RESUME.json'),dict(checkpoint=asset(checkpoint),q_and_Adam_restored=True,restored_iteration=start_iteration,backend='official Ring hard bin32; loss/geometry/all pixels unchanged, equivalence gate required',prior_segment_runtime='not fully recorded, final seconds resumed segment only'));print('POSE019_RESUMED',scope,ix,start_iteration,nacc,flush=True)
  for it in range(start_iteration+1,81):
   L,parts=obj.evaluate(q,cand,True);g=q.grad.detach().clone();old=q.detach().clone();state=copy.deepcopy(opt.state_dict());opt.step();proposal=q.detach().clone();afterstate=copy.deepcopy(opt.state_dict());accepted=False;reason=[];nextparts=parts;candidate_loss=None;alpha=0.
   with torch.no_grad():q.copy_(old)
   opt.load_state_dict(state)
   for k in range(8):
    alpha=.5**k;qt=old+alpha*(proposal-old);delta=exp_se3(qt*obj.scale);tn=float(delta[:3,3].norm());rn=float((qt[3:]*obj.scale[3:]).norm()*180/np.pi);bad=[]
    if not torch.isfinite(qt).all()or not torch.isfinite(g).all():bad.append('NONFINITE')
    if tn>1.2 or rn>10:bad.append('PREDECLARED_LOCAL_POSE_BOUNDS')
    if not bad:
     with torch.no_grad():candidate_loss,pp=obj.evaluate(qt,cand,False)
     if candidate_loss>L+1e-9:bad.append('FULL_FIT_OBJECTIVE')
     if pp['ring']>ip['ring']+.001:bad.append('RING_PROJECTION_SACRIFICE')
    if not bad:
     with torch.no_grad():q.copy_(qt)
     opt.load_state_dict(afterstate);accepted=True;nacc+=1;nextparts=pp;L=candidate_loss;break
    reason+=bad
   if not accepted:
    with torch.no_grad():q.copy_(old)
    opt.load_state_dict(state)
   H=obj.transform(q,cand).detach().cpu().numpy();hist.append(dict(iteration=it,accepted=accepted,accepted_total=nacc,alpha=alpha if accepted else 0.,loss=L,parts=nextparts,gradient=g.detach().cpu().numpy(),gradient_finite=bool(torch.isfinite(g).all()),normalized_q=q.detach().cpu().numpy(),actual_left_twist=q.detach().cpu().numpy()*obj.scale.detach().cpu().numpy(),T=H,reasons=list(dict.fromkeys(reason))))
   if it in [1,10,40,80]:
    save(str(folder.relative_to(R)/('ITER_%03d.json'%it)),hist[-1]);torch.save(dict(q=q.detach().cpu(),optimizer=opt.state_dict(),iteration=it,candidate=seed),folder/('ITER_%03d.pt'%it));save(str(folder.relative_to(R)/'HISTORY.json'),hist);print('POSE019',scope,ix,it,nacc,round(L,7),flush=True)
  val,parts=obj.evaluate(q,cand,False);H=obj.transform(q,cand).detach().cpu().numpy();result=dict(scope=scope,seed_index=ix,initial=seed,initial_loss=initial,initial_parts=ip,final_loss=val,final_parts=parts,T=H,R=H[:3,:3],t_mm=H[:3,3],normalized_q=q.detach().cpu().numpy(),twist_translation_rotation=q.detach().cpu().numpy()*obj.scale.detach().cpu().numpy(),accepted=nacc,iterations=len(hist),seconds=time.time()-start,body_updated=False,scale=1.,coordinate='X004=R X005+t; c2w004_camera = T004_from005 @ c2w005_camera; mm, column vectors',no_GT=True);save(str(done.relative_to(R)),result);finals.append(result)
 best=min(finals,key=lambda r:r['final_loss']);save('results/'+scope+'_A5_ALL_INITIALIZATIONS.json',finals);save('results/'+scope+'_A5_FINAL.json',best);print('ALL_REFINEMENT_DONE',scope,best['seed_index'],best['accepted'],best['final_loss'],flush=True)

def main():
 guard_optimizer();views=load(R/'config/VIEWS.json');save('provenance/BEFORE_REFINE_FREEZE.json',dict(epoch=time.time(),source=[asset(p)for p in(R/'code').glob('*.py')],protocol=asset(R/'01_PROTOCOL.md'),GT=False,HOLDOUT=False));run('CROSS',[v['id']for v in views if v['video']=='005'and v['role']=='FIT']);torch.cuda.empty_cache();run('NEGATIVE',load(R/'config/NEGATIVE_SPLIT.json')['target_fit']);save('provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json',dict(epoch=time.time(),results=[asset(p)for p in(R/'results').glob('*.json')],body=asset(R/'inputs/G01/BODY018.npz'),mesh_not_changed=True,no_scale=True,HOLDOUT_used_for_selection=False,GT=False));print('019_POSE_PREDICTIONS_FROZEN',flush=True)
if __name__=='__main__':main()
