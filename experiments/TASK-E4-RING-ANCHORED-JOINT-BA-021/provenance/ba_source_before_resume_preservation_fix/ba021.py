"""Actual common-point BA: one shared pose plus one X per RGB identity, no body/HERO."""
from objective020 import *
import copy

class CommonPoints:
 def __init__(self,scope):
  self.tracks=load(R/'observations'/(scope+'_COMMON_TRACKS.json'));self.X0=tensor([t['X0']for t in self.tracks],torch.float64);self.W=tensor([t['whitener']for t in self.tracks],torch.float64);obs=[o for t in self.tracks for o in t['observations']];self.obs=obs;self.idx=tensor([o['track']for o in obs],torch.int64);self.C=tensor([o['native_C']for o in obs],torch.float64);self.K=tensor([o['K']for o in obs],torch.float64);self.uv=tensor([o['uv']for o in obs],torch.float64);self.side=tensor([o['side']for o in obs],torch.bool);self.w=tensor([o['weight']*self.tracks[o['track']]['track_weight']for o in obs],torch.float64);self.tw=tensor([t['track_weight']for t in self.tracks],torch.float64)
 def residual(self,H,X):
  C=torch.where(self.side[:,None,None],H[None]@self.C,self.C);p=torch.einsum('ni,nij->nj',X[self.idx]-C[:,:3,3],C[:,:3,:3]);q=torch.einsum('ni,nji->nj',p,self.K);return q[:,:2]/q[:,2:].clamp_min(1e-6)-self.uv,p[:,2]
 def term(self,H,X):
  d,z=self.residual(H,X);l=hub(d.square().sum(1).add(1e-12).sqrt()/3);return(l*self.w).sum(),z
 def point_prior(self,X):
  d=torch.einsum('kij,kj->ki',self.W,X-self.X0);return(d.square().mean(1)*self.tw).sum()

class Ring021(RingRenderer):
 def term(self,H,cid,curves=False):
  d=self.data[cid];C=canonical(H@d['T']);cam=self.camera(C,d['Ksmall']);fr=self.raster(self.ring,cameras=cam);alpha=self.shader(fr,self.ring,cameras=cam)[0,...,3];p=d['target'];known=d['known'];M=.5*(((1-alpha)**2*p).sum()/p.sum().clamp_min(1)+(alpha.square()*known*(1-p)).sum()/(known*(1-p)).sum().clamp_min(1));parts=dict(M=M,Ieps=C.sum()*0,Oeps=C.sum()*0)
  if curves:
   eps=load(R/'config/PROTOCOL.json')['epsilon_px'];segs=self.curves.segments(C.detach().cpu().numpy(),d['K'].cpu().numpy());e=d['evidence']
   for key,label in [('inner','Ieps'),('outer','Oeps')]:
    if not len(e[key])or not len(segs[key]):raise RuntimeError('NO_REAL_OR_CAD_CURVE:'+cid+':'+key)
    X=tensor(self.curves.V[segs[key]],torch.float64);pq=self.curves.project(X,C,d['K']);a,b=pq[:,0],pq[:,1];v=b-a;D=tensor(e[key],torch.float64)[:,None]-a[None];t=(D*v[None]).sum(-1)/v.square().sum(-1).clamp_min(1e-12);dist=(D-t.clamp(0,1)[...,None]*v[None]).square().sum(-1).min(-1).values.add(1e-12).sqrt();parts[label]=hub((dist-eps[key]).clamp_min(0)/3).mean()
  return parts

class BA:
 def __init__(self,scope,ids,arm):
  self.p=load(R/'config/PROTOCOL.json');self.points=CommonPoints(scope);self.ring=Ring021(ids);self.ids=ids;self.arm=arm;self.curves=arm.endswith('B3');self.scale=tensor(self.p['pose_scale'],torch.float64);b={cid:self.ring.data[cid]['meta']['direction_block019']for cid in ids};n=len(set(b.values()));self.w={cid:1/n/sum(v==b[cid]for v in b.values())for cid in ids}
 def transform(self,q,seed):return exp_se3(q*self.scale)@seed
 def evaluate(self,q,X,seed,grad=False):
  if grad:q.grad=None;X.grad=None
  parts=dict(M=0.,Ieps=0.,Oeps=0.,reprojection=0.,pose_prior=0.,point_prior=0.)
  for cid in self.ids:
   pp=self.ring.term(self.transform(q,seed),cid,self.curves);L=(pp['M']+self.p['lambda_curve']*(pp['Ieps']+pp['Oeps']))*self.w[cid]
   for k,v in pp.items():parts[k]+=float(v.detach())*self.w[cid]
   if grad:L.backward()
  F,z=self.points.term(self.transform(q,seed),X);prior=q.square().mean();xp=self.points.point_prior(X);tail=self.p['lambda_reprojection']*F+self.p['lambda_pose_prior']*prior+self.p['lambda_point_prior']*xp
  if grad:tail.backward()
  parts.update(reprojection=float(F.detach()),pose_prior=float(prior.detach()),point_prior=float(xp.detach()),minimum_observation_depth_mm=float(z.min().detach()));L=parts['M']+self.p['lambda_curve']*(parts['Ieps']+parts['Oeps'])+self.p['lambda_reprojection']*parts['reprojection']+self.p['lambda_pose_prior']*parts['pose_prior']+self.p['lambda_point_prior']*parts['point_prior'];return L,parts

def run(arm,scope,ids,seed):
 folder=R/'optimization'/arm;folder.mkdir(parents=True,exist_ok=True)
 if(folder/'FINAL.json').exists():return load(folder/'FINAL.json')
 obj=BA(scope,ids,arm);q=torch.zeros(6,device=device,dtype=torch.float64,requires_grad=True);X=obj.points.X0.clone().requires_grad_(True);joint=arm!='B1'and arm!='NEG_B1';params=[dict(params=[q],lr=obj.p['adam_pose_lr'])]
 if joint:params.append(dict(params=[X],lr=obj.p['adam_point_lr_mm']))
 opt=torch.optim.Adam(params);seed=tensor(seed,torch.float64);hist=[];nacc=0;start=time.time();initial,ip=obj.evaluate(q,X,seed);save(str(folder.relative_to(R)/'INITIAL.json'),dict(T=seed.detach().cpu().numpy(),X=X.detach().cpu().numpy(),loss=initial,parts=ip));start_it=0
 ck=list(folder.glob('ITER_*.pt'))
 if ck:
  cp=max(ck,key=lambda p:int(p.stem.split('_')[1]));st=torch.load(cp,map_location=device,weights_only=False)
  with torch.no_grad():q.copy_(st['q']);X.copy_(st['X'])
  opt.load_state_dict(st['Adam']);start_it=st['iteration'];hist=[h for h in load(folder/'HISTORY.json')if h['iteration']<=start_it];nacc=hist[-1]['accepted_total']
  save(str(folder.relative_to(R)/'RESUME.json'),dict(checkpoint=asset(cp),restored=['q','X','Adam','iteration'],new_segment_seconds=True))
 for it in range(start_it+1,obj.p['iterations']+1):
  L,p=obj.evaluate(q,X,seed,True);gq=q.grad.detach().clone();gx=X.grad.detach().clone();oldq=q.detach().clone();oldX=X.detach().clone();state=copy.deepcopy(opt.state_dict());opt.step();pq=q.detach().clone();pX=X.detach().clone()if joint else oldX;newstate=copy.deepcopy(opt.state_dict());accepted=False;reasons=[];alpha=0.;after=p
  with torch.no_grad():q.copy_(oldq);X.copy_(oldX)
  opt.load_state_dict(state)
  for k in range(obj.p['backtracks']):
   a=2.**-k;tq=oldq+a*(pq-oldq);tX=oldX+a*(pX-oldX);delta=exp_se3(tq*obj.scale);bad=[];white=torch.einsum('kij,kj->ki',obj.points.W,tX-obj.points.X0)
   if not torch.isfinite(tq).all()or not torch.isfinite(tX).all()or not torch.isfinite(gq).all()or not torch.isfinite(gx).all():bad+=['NONFINITE']
   if float(delta[:3,3].norm())>obj.p['translation_bound_mm']or float((tq[3:]*obj.scale[3:]).norm())>np.deg2rad(obj.p['rotation_bound_deg']):bad+=['LOCAL_SE3_BOUND']
   if float((tX-obj.points.X0).norm(dim=1).max())>obj.p['point_displacement_bound_mm']or float(white.norm(dim=1).max())>obj.p['point_whitened_bound']:bad+=['LANDMARK_DISPLACEMENT_BOUND']
   if not bad:
    with torch.no_grad():new,pp=obj.evaluate(tq,tX,seed)
    if pp['minimum_observation_depth_mm']<=0:bad+=['NEGATIVE_DEPTH']
    if new>L+obj.p['acceptance_tolerance']:bad+=['FULL_FIT_OBJECTIVE']
   if not bad:
    with torch.no_grad():q.copy_(tq);X.copy_(tX)
    opt.load_state_dict(newstate);accepted=True;nacc+=1;alpha=a;L=new;after=pp;break
   reasons+=bad
  if not accepted:
   with torch.no_grad():q.copy_(oldq);X.copy_(oldX)
   opt.load_state_dict(state)
  row=dict(iteration=it,accepted=accepted,accepted_total=nacc,loss=L,parts=after,alpha=alpha,reasons=sorted(set(reasons)),pose_gradient=gq.cpu().numpy(),point_gradient_norms=gx.norm(dim=1).cpu().numpy(),q=q.detach().cpu().numpy(),T=obj.transform(q,seed).detach().cpu().numpy(),X=X.detach().cpu().numpy(),max_point_displacement_mm=float((X-obj.points.X0).norm(dim=1).max().detach()),actual_pose_parameter_step=(q.detach()-oldq).cpu().numpy(),actual_X_step=(X.detach()-oldX).cpu().numpy());hist.append(row)
  if it%10==0 or it==1:
   save(str(folder.relative_to(R)/'HISTORY.json'),hist);torch.save(dict(q=q.detach().cpu(),X=X.detach().cpu(),Adam=opt.state_dict(),iteration=it,seed=seed.detach().cpu()),folder/('ITER_%03d.pt'%it));print('BA021',arm,it,nacc,round(L,6),'sec',round(time.time()-start,1),flush=True)
 loss,pp=obj.evaluate(q,X,seed);out=dict(arm=arm,scope=scope,T=obj.transform(q,seed).detach().cpu().numpy(),seed_T=seed.detach().cpu().numpy(),X=X.detach().cpu().numpy(),X0=obj.points.X0.cpu().numpy(),q=q.detach().cpu().numpy(),loss=loss,initial_loss=initial,parts=pp,accepted=nacc,iterations=obj.p['iterations'],joint_X_optimized=joint,body_in_loss=False,HERO_in_loss=False,scale=1.,seconds=time.time()-start);save(str(folder.relative_to(R)/'FINAL.json'),out);save('results/'+arm+'.json',out);return out

def main():
 frozen=R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json'
 if frozen.exists():
  assert all(sha(a['path'])==a['sha256']for a in load(frozen)['files']);print('021_ALL_POSES_ALREADY_FROZEN');return
 guard_optimizer()
 def forbid(event,args):
  if event=='open'and isinstance(args[0],(str,bytes)):
   p=str(Path(os.fsdecode(args[0])).resolve())
   if p.endswith('/BODY018.npz')or'/hero_fit/'in p or'/holdout/hero/'in p or('/TASK-E4-HERO-BODY-ADAPT-018/arms/'in p):raise PermissionError('NO_BODY_HERO_IN_021_BA:'+p)
 sys.addaudithook(forbid)
 assert load(R/'metrics/BA_GRADIENT_GATE.json')['all_passed'];vv=load(R/'config/VIEWS.json');ids=[v['id']for v in vv if v['video']=='005'and v['role']=='FIT'];h=load(R/'config/HISTORICAL_CANDIDATES.json');roma=next(x['T']for x in h if x['tag']=='HISTORICAL_FULL_RoMa');P20=REPO/'experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020'
 save('provenance/BEFORE_OPTIMIZATION_FREEZE.json',dict(epoch=time.time(),files=[asset(p)for p in(R/'code').glob('*.py')],inputs=asset(R/'provenance/INPUTS_AND_PROTOCOL_FROZEN.json'),protocol=asset(R/'config/PROTOCOL.json'),body=False,HERO=False,GT=False,HOLDOUT=False))
 for name,old in [('B0_RoMa','R0'),('B0_020_R2','R2'),('B0_020_R3','R3'),('B0_020_MASK','R3_MASK_ONLY')]:save('results/'+name+'.json',dict(arm=name,T=load(P20/'results'/(old+'.json'))['T'],origin=asset(P20/'results'/(old+'.json')),static=True))
 save('results/R0.json',load(R/'results/B0_RoMa.json'))
 for arm in ['B1','B2','B3']:run(arm,'CROSS',ids,roma)
 save('provenance/MAIN_ROUTES_FROZEN.json',dict(epoch=time.time(),files=[asset(R/'results'/(a+'.json'))for a in ['B1','B2','B3']],not_selected_by_HOLDOUT=True))
 for arm in ['NEG_B1','NEG_B2','NEG_B3']:run(arm,'NEGATIVE',load(R/'config/NEGATIVE_SPLIT.json')['target_fit'],np.eye(4))
 run('SENS_B2_LightGlue','CROSS',ids,next(x['T']for x in h if x['tag']=='HISTORICAL_FULL_LightGlue'));run('SENS_B2_020R2','CROSS',ids,load(P20/'results/R2.json')['T'])
 save('provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json',dict(epoch=time.time(),files=[asset(p)for p in(R/'results').glob('*.json')],body=False,HERO=False,HOLDOUT=False,GT=False));print('021_ALL_POSES_FROZEN',flush=True)
if __name__=='__main__':main()
