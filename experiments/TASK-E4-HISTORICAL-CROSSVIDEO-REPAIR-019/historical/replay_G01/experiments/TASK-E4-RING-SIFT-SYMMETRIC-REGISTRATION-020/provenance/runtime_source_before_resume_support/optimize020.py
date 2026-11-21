from objective020 import *
import copy,importlib.util
P19=REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019'
BODY_ALLOWED=False
def no_body_hook(event,args):
 if event=='open'and isinstance(args[0],(str,bytes))and not BODY_ALLOWED:
  p=str(Path(os.fsdecode(args[0])).resolve())
  if p.endswith('/BODY018.npz')or'/TASK-E4-HERO-BODY-ADAPT-018/arms/'in p:raise PermissionError('020_NO_BODY_IN_MAIN:'+p)

def run(arm,scope,ids,seed,body=None):
 folder=R/'optimization'/arm;folder.mkdir(parents=True,exist_ok=True)
 if(folder/'FINAL.json').exists():return load(folder/'FINAL.json')
 obj=Objective(ids,scope,arm,body);q=torch.zeros(6,device=device,dtype=torch.float64,requires_grad=True);opt=torch.optim.Adam([q],lr=.01);seed=tensor(seed,torch.float64);hist=[];nacc=0;start=time.time();initial,ip=obj.evaluate(q,seed,False,True);save(str(folder.relative_to(R)/'INITIAL.json'),dict(T=seed.detach().cpu().numpy(),loss=initial,parts=ip))
 for it in range(1,81):
  L,p=obj.evaluate(q,seed,True,component_gradient=it in [1,20,80]);g=q.grad.detach().clone();old=q.detach().clone();state=copy.deepcopy(opt.state_dict());opt.step();proposed=q.detach().clone();newstate=copy.deepcopy(opt.state_dict());accepted=False;reason=[];alpha=0.
  with torch.no_grad():q.copy_(old)
  opt.load_state_dict(state)
  for k in range(8):
   a=2.**-k;qt=old+a*(proposed-old);delta=exp_se3(qt*obj.scale);bad=[]
   if not torch.isfinite(qt).all()or not torch.isfinite(g).all():bad.append('NONFINITE')
   if float(delta[:3,3].norm())>1.2 or float((qt[3:]*obj.scale[3:]).norm())>np.deg2rad(10):bad.append('LOCAL_SE3_BOUND')
   if not bad:
    with torch.no_grad():new,pp=obj.evaluate(qt,seed)
    if new>L+1e-6:bad.append('FULL_FIT_OBJECTIVE')
   if not bad:
    with torch.no_grad():q.copy_(qt)
    opt.load_state_dict(newstate);L=new;accepted=True;nacc+=1;alpha=a;break
   reason+=bad
  if not accepted:
   with torch.no_grad():q.copy_(old)
   opt.load_state_dict(state)
  H=obj.transform(q,seed).detach().cpu().numpy();row=dict(iteration=it,accepted=accepted,accepted_total=nacc,alpha=alpha,loss=L,parts_before=p,T=H,q=q.detach().cpu().numpy(),gradient=g.detach().cpu().numpy(),reasons=sorted(set(reason)));hist.append(row)
  if it in [1,10,20,40,80]:
   save(str(folder.relative_to(R)/'HISTORY.json'),hist);save(str(folder.relative_to(R)/('ITER_%03d.json'%it)),row);torch.save(dict(q=q.detach().cpu(),Adam=opt.state_dict(),iteration=it,seed=seed.detach().cpu()),folder/('ITER_%03d.pt'%it));print('POSE020',arm,it,nacc,round(L,6),'seconds',round(time.time()-start,1),flush=True)
 loss,parts=obj.evaluate(q,seed,False,True);H=obj.transform(q,seed).detach().cpu().numpy();f=dict(arm=arm,scope=scope,T=H,seed_T=seed.detach().cpu().numpy(),loss=loss,initial_loss=initial,parts=parts,accepted=nacc,iterations=80,seconds=time.time()-start,body_in_loss=body is not None,scale=1.,no_GT=True,HOLDOUT=False);save(str(folder.relative_to(R)/'FINAL.json'),f);save('results/'+arm+'.json',f);return f

def main():
 global BODY_ALLOWED
 guard_optimizer();sys.addaudithook(no_body_hook);assert load(R/'metrics/RING_CURVE_PROJECTION_GRADIENT_GATE.json')['all_passed'];assert(R/'provenance/SYMMETRIC_FEATURES_FROZEN.json').exists();v=load(R/'config/VIEWS.json');ids=[x['id']for x in v if x['video']=='005'and x['role']=='FIT'];hist=load(R/'config/HISTORICAL_CANDIDATES.json');Roma=np.asarray(next(x['T']for x in hist if x['tag']=='HISTORICAL_FULL_RoMa'));save('results/R0.json',dict(arm='R0',T=Roma,origin='unchanged historical full RoMa, no yaw projection',body_in_loss=False));save('provenance/BEFORE_OPTIMIZATION_FREEZE.json',dict(epoch=time.time(),source=[asset(p)for p in(R/'code').glob('*.py')],protocol=asset(R/'config/PROTOCOL.json'),views=asset(R/'config/VIEWS.json'),RoMa=Roma,HOLDOUT=False,body=False))
 for arm in ['R1','R2','R3','R3_MASK_ONLY','R3_INNER_OUTER']:run(arm,'CROSS',ids,Roma)
 run('NEGATIVE_R3','NEGATIVE',load(R/'config/NEGATIVE_SPLIT.json')['target_fit'],np.eye(4));save('provenance/NO_BODY_PREDICTIONS_FROZEN.json',dict(epoch=time.time(),files=[asset(p)for p in(R/'results').glob('*.json')],body_never_read_in_main=True,HOLDOUT=False,GT=False))
 # R4 is permitted only after all independent no-body endpoints are immutable.
 BODY_ALLOWED=True
 spec=importlib.util.spec_from_file_location('renderer019_control',P19/'code/renderer019.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);body=mod.FrozenRenderer(ids);run('R4','CROSS',ids,Roma,body)
 save('provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json',dict(epoch=time.time(),files=[asset(p)for p in(R/'results').glob('*.json')],HOLDOUT=False,GT=False,body_in_R4_only=True));print('ALL020_POSES_FROZEN',flush=True)
if __name__=='__main__':main()
