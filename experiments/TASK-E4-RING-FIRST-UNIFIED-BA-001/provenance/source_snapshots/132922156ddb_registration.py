from v8_common import *
sys.path.insert(0,str(V7/'scripts'));from photo_registration import epi,tri
from itertools import combinations
def getpair(method,a,b):
 p=R/f'observations/{method}_{a}__{b}.npz';reverse=False
 if not p.exists():p=R/f'observations/{method}_{b}__{a}.npz';reverse=True
 if not p.exists():return None
 n=dict(np.load(p))
 if reverse:n['p'],n['q']=n['q'],n['p']
 return n
def spin(base,yaw,flip=False):
 t=np.eye(4);t[:3,:3]=Rotation.from_euler('z',yaw).as_matrix()@(Rotation.from_euler('x',np.pi).as_matrix() if flip else np.eye(3));return t@base
def third_checks(method,source_ids,target,pose,kt,views):
 rows=[]
 for sa,sb in combinations(source_ids,2):
  a,b,d=getpair(method,sa,target),getpair(method,sb,target),getpair(method,sa,sb)
  if a is None or b is None or d is None:continue
  ib=np.flatnonzero(b['held']);di=np.flatnonzero(d['usable']);ia=np.flatnonzero(a['held'])
  if not len(ib) or not len(di) or not len(ia):continue
  dist,j=cKDTree(b['q'][ib]).query(a['q'][ia]);dd,ii=cKDTree(d['p'][di]).query(a['p'][ia]);err=[];positive=[];pars=[]
  for k in np.flatnonzero((dist<=2)&(dd<=2)):
   ai=ia[k];bi=ib[j[k]];si=di[ii[k]]
   if np.linalg.norm(d['q'][si]-b['p'][bi])>2:continue
   ap,bp=np.array(views[sa]['pose']),np.array(views[sb]['pose']);x=tri(ap,bp,a['p'][ai:ai+1],b['p'][bi:bi+1],K,K);qa,za=project(x,ap,K);qb,zb=project(x,bp,K);r=x[0]-ap[:3,3];s=x[0]-bp[:3,3];par=np.degrees(np.arccos(np.clip(r@s/max(np.linalg.norm(r)*np.linalg.norm(s),1e-12),-1,1)))
   if min(za[0],zb[0])<=0 or max(np.linalg.norm(qa[0]-a['p'][ai]),np.linalg.norm(qb[0]-b['p'][bi]))>3 or par<.5:continue
   qt,zt=project(x,pose,kt);err.append(float(np.linalg.norm(qt[0]-a['q'][ai])));positive.append(zt[0]>0);pars.append(par)
  rows.append(dict(source_pair=[sa,sb],target=target,n=len(err),error_px=stats(err),positive=float(np.mean(positive)) if positive else 0.,parallax_deg=stats(pars)))
 return rows
def main():
 views={x['id']:x for x in load('inputs/matching_views.json')};photo=old.load('predictions/photo_ring_candidates.json');src4=['004_03','004_08','004_13'];src5=['v005_00057','v005_00459'];allrows=[];formal={};freeze('registration_protocol',[Path(__file__),R/'config.json',V7/'scripts/photo_registration.py'],GT_role='no GT')
 for method in ['SIFT','MASt3R']:
  if not (R/f'metrics/matching_{method}.json').exists():continue
  tasks=[dict(id='004_to005_shared',sources=src4,targets=src5,focal=490.,shared=True)]
  for target in ['photo_003','photo_001']:
   for scope,sources in [('004',src4),('005',src5)]:
    for foc in cfg()['photo_focals'] if target=='photo_003' else [490.]:tasks.append(dict(id=target+'_'+scope+f'_f{int(foc)}',sources=sources,targets=[target],focal=foc,shared=False))
  for task in tasks:
   kt=K.copy();kt[0,0]=kt[1,1]=task['focal'];pairs=[]
   for s in task['sources']:
    for t in task['targets']:
     d=getpair(method,s,t)
     if d is None:continue
     ix=np.flatnonzero(d['train']);ix=ix[np.linspace(0,len(ix)-1,min(400,len(ix)),dtype=int)] if len(ix) else ix
     if len(ix)>=8:pairs.append(dict(s=s,t=t,d=d,ix=ix))
   fits=[];ntr=sum(len(x['ix']) for x in pairs)
   if ntr>=16:
    bases=[None] if task['shared'] else [np.array(c['c2r']) for c in next(x for x in photo if x['id']==task['targets'][0] and x['focal_px']==task['focal'])['candidates']]
    def target_pose(base,angle,flip,t):return spin(np.array(views[t]['pose']) if task['shared'] else base,angle,flip)
    def residual(base,angle,flip):
     rr=[]
     for x in pairs:
      p,q=x['d']['p'][x['ix']],x['d']['q'][x['ix']];e=epi(np.array(views[x['s']]['pose']),target_pose(base,angle,flip,x['t']),p,q,K,kt);rr.extend(e/np.sqrt(len(e)))
     return np.array(rr)
    seeds=[]
    for bi,base in enumerate(bases):
     for flip in [False,True]:
      for angle in np.linspace(-np.pi,np.pi,144,endpoint=False):
       rr=residual(base,angle,flip);score=float(np.mean(2*(np.sqrt(1+rr**2)-1)));seeds.append((score,bi,flip,angle))
    seeds.sort();chosen=[]
    for x in seeds:
     if all(x[1:3]!=y[1:3] or abs(np.angle(np.exp(1j*(x[3]-y[3]))))>.3 for y in chosen):chosen.append(x)
     if len(chosen)==3:break
    for init in chosen:
     _,bi,flip,angle=init;base=bases[bi];f=least_squares(lambda x:residual(base,float(x[0]),flip),[angle],loss='soft_l1',max_nfev=100);res=residual(base,float(f.x[0]),flip);poses={t:target_pose(base,float(f.x[0]),flip,t) for t in task['targets']};fits.append(dict(training_objective=float(np.mean(2*(np.sqrt(1+res**2)-1))),branch=bi,flip=flip,yaw=float(f.x[0]),poses=poses))
    fits.sort(key=lambda x:x['training_objective'])
   rec=dict(method=method,task=task['id'],training_pair_count=len(pairs),training_matches_used=ntr,numeric=bool(fits),accepted=False,focal=task['focal'],fixed_Ring_5DoF=True,K490_primary=task['focal']==490.,sensitivity_only=task['focal']!=490.,source_poses_frozen=True)
   if fits:
    best=fits[0];errs=[];pos=[];ringerrs=[];checks=[];spreads=[]
    for target,po in best['poses'].items():
     C=np.array([x['poses'][target][:3,3] for x in fits]);spreads.append(float(np.linalg.norm(C[:,None]-C[None,:],axis=2).max()));ob=dict(np.load((V6 if task['shared'] else V7)/f'observations/{target}_ring.npz'));qheld=ob.get('q_held',ob.get('ring_heldout'));cur=prev.contours(po,n=2048,K0=kt);ringerrs.extend(cKDTree(cur.reshape(-1,2)).query(qheld)[0]);checks.extend(third_checks(method,task['sources'],target,po,kt,views))
     for source in task['sources']:
      d=getpair(method,source,target)
      if d is None:continue
      p,q=d['p'][d['held']],d['q'][d['held']];ap=np.array(views[source]['pose']);X=tri(ap,po,p,q,K,kt);ua,za=project(X,ap,K);ub,zb=project(X,po,kt);errs.extend(np.r_[np.linalg.norm(ua-p,axis=1),np.linalg.norm(ub-q,axis=1)]);pos.extend((za>0)&(zb>0))
    hh=stats(errs);rh=stats(ringerrs);ipass=any(c['n']>=8 and c['error_px']['MAE']<=3 and c['error_px']['p95']<=6 and c['positive']>=.95 for c in checks);positive=float(np.mean(pos)) if pos else 0.;spread=max(spreads);rec.update(held_pair_reprojection_px=hh,positive_fraction=positive,held_Ring_self_contour_px=rh,center_spread_mm=spread,third_source=checks,training_best=best)
    rec['accepted']=bool(len(pos)>=8 and hh['MAE']<=3 and hh['p95']<=6 and rh['MAE']<=3 and rh['p95']<=6 and positive>=.95 and spread<=2 and ipass and task['focal']==490.)
   name=method+'_'+task['id'];formal[name]=dict(targets=task['targets'],poses=best['poses'] if rec['accepted'] else {t:np.full((4,4),np.nan) for t in task['targets']});allrows.append(rec);save('metrics/registration.json',allrows);print('REGISTER',method,task['id'],'train',ntr,'pass',rec['accepted'],'3viewmax',max([x['n'] for x in rec.get('third_source',[])],default=0),flush=True)
 save('predictions/formal_registration.json',formal);np.savez_compressed(R/'predictions/formal_registration.npz',case=np.array(list(formal)),pose=np.array([list(x['poses'].values())[0] for x in formal.values()]),accepted=np.array([x['accepted'] for x in allrows]));freeze('registration_predictions',[R/'metrics/registration.json',R/'predictions/formal_registration.json',R/'predictions/formal_registration.npz']);print('REGISTRATION_DONE',flush=True)
if __name__=='__main__':main()
