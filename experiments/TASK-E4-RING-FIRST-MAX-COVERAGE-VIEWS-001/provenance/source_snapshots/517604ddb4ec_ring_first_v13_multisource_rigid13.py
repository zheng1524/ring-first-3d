"""One bounded diagnostic: does preserving erroneous Ring5DoF block cross-video registration?"""
from common13 import *
from register13 import obs,Ring_score,ring_residual
from register_sparse13 import third,passed_third
def main():
 freeze('bounded_rigid_protocol',[Path(__file__),R/'config.json',R/'metrics/sparse_registration.json'],role='Same frozen2D observations/gates. One global rigid transform of005, no scale/Polyp deformation.3starts100nfev,delta bounds20deg/2mm inherited first3D arm. Photos may seed but cannot certify geometry.')
 views={v['id']:dict(v,pose=v.get('poses',{}).get('0',np.eye(4))) for v in load('inputs/views.json')};prior_rows=load('metrics/sparse_registration.json');rows=[];bridges=[];sources=['004_03','004_08','004_13'];targets=load('config.json')['fit005'];obs5={t:obs(t) for t in targets}
 for method in ['RoMa','LightGlue','MASt3R']:
  direct=next(x for x in prior_rows if x['method']==method and x['shared']);rec=dict(method=method,numeric=False,accepted=False,formal_H=np.full((4,4),np.nan));data=[]
  for s in sources:
   for t in targets:
    d=pair(method,s,t)
    if d is None:continue
    ii=np.flatnonzero(d['train']);ii=ii[np.linspace(0,len(ii)-1,min(len(ii),400),dtype=int)] if len(ii) else ii
    if len(ii)>=8:data.append((s,t,d,ii))
  if not direct['numeric']:rows.append(rec);continue
  def residualH(H):
   ff=np.concatenate([epi(np.array(views[s]['pose']),H@np.array(views[t]['pose']),d['p'][ii],d['q'][ii],K,K) for s,t,d,ii in data]);rr=np.concatenate([ring_residual(H@np.array(views[t]['pose']),obs5[t],K0=K) for t in targets]);return np.r_[ff,rr*np.sqrt(len(ff)/len(rr))]
  seeds=[dict(H=np.array(x['H']),origin='direct_yaw') for x in direct['all_initializations']]
  for photo in ['photo_001','photo_003','photo_002']:
   a=next((x for x in prior_rows if x['method']==method and x['target']==photo and x['scope']=='004' and x['focal']==490),None);b=next((x for x in prior_rows if x['method']==method and x['target']==photo and x['scope']=='005' and x['focal']==490),None);br=dict(method=method,photo=photo,numeric=False,accepted=False,formal_H=np.full((4,4),np.nan),photo002_consumed_as_seed_not_final_holdout=photo=='photo_002')
   if a and b and a['numeric'] and b['numeric']:
    H=np.array(a['training_best']['H'])@np.linalg.inv(np.array(b['training_best']['H']));seeds.append(dict(H=H,origin=photo+'_bridge'));br.update(numeric=True,H_candidate=H,individual_photo_scopes_verified=bool(a['accepted'] and b['accepted']))
   bridges.append(br)
  for seed in seeds:
   rr=residualH(seed['H']);seed['training_score']=float(np.mean(2*(np.sqrt(1+rr*rr)-1)))
  seeds.sort(key=lambda x:x['training_score']);chosen=[]
  for x in seeds:
   center=(x['H']@np.array(views['v005_00459']['pose']))[:3,3]
   if all(np.linalg.norm(center-(y['H']@np.array(views['v005_00459']['pose']))[:3,3])>1 for y in chosen):chosen.append(x)
   if len(chosen)==3:break
  fits=[]
  for seed in chosen:
   def decode(x):
    H=np.eye(4);H[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix();H[:3,3]=x[3:];return H@seed['H']
   def rr(x):return np.r_[residualH(decode(x)),x[:3]/np.deg2rad(15),x[3:]/2]
   bound=np.r_[np.full(3,np.deg2rad(20)),np.full(3,2.)];fit=least_squares(rr,np.zeros(6),bounds=(-bound,bound),loss='soft_l1',f_scale=1.,max_nfev=100,diff_step=1e-5);r=rr(fit.x);fits.append(dict(H=decode(fit.x),origin=seed['origin'],training_objective=float(np.mean(2*(np.sqrt(1+r*r)-1))),nfev=fit.nfev,parameters=fit.x))
  fits.sort(key=lambda x:x['training_objective']);best=fits[0];H=best['H'];current={id:dict(v,pose=H@np.array(v['pose']) if id.startswith('v005') else np.array(v['pose'])) for id,v in views.items()};checks=[]
  for t in ['v005_00834','v005_00860']:checks+=third(method,['004_07','004_10'],t,current[t]['pose'],K,current)
  for t in ['004_07','004_10']:checks+=third(method,['v005_00834','v005_00860'],t,current[t]['pose'],K,current)
  testerrors=[];positive=[]
  for s,t,d,_ in data:
   ii=np.flatnonzero(d['held'])
   if not len(ii):continue
   ap,po=current[s]['pose'],current[t]['pose'];X=tri(ap,po,d['p'][ii],d['q'][ii],K,K);a,za=project(X,ap,K);b,zb=project(X,po,K);testerrors.extend((np.linalg.norm(a-d['p'][ii],axis=1)+np.linalg.norm(b-d['q'][ii],axis=1))/2);positive.extend((za>0)&(zb>0))
  rings=[Ring_score(current[t]['pose'],t,K) for t in targets];cs=np.array([(x['H']@np.array(views['v005_00459']['pose']))[:3,3] for x in fits]);spread=float(np.linalg.norm(cs[:,None]-cs[None,:],axis=2).max());hh=stats(testerrors);pos=float(np.mean(positive)) if positive else 0.;passed=hh['n']>=8 and hh['MAE']<=3 and hh['p95']<=6 and pos>=.95 and spread<=2 and all(x['MAE']<=3 and x['p95']<=6 for x in rings) and any(passed_third(x) for x in checks if x['target'].startswith('v005')) and any(passed_third(x) for x in checks if x['target'].startswith('004'))
  rec.update(numeric=True,accepted=bool(passed),training=sum(len(x[3]) for x in data),held_error_px=hh,positive_fraction=pos,Ring=rings,independent_checks=checks,center_spread_mm=spread,all_initializations=fits,training_best=best,formal_H=H if passed else np.full((4,4),np.nan));rows.append(rec);save('metrics/bounded_rigid_registration.json',rows);print('RIGID13',method,passed,'held',hh,'Ring',rings,'third',checks,flush=True)
 save('metrics/sparse_photo_bridges.json',bridges);save('metrics/bounded_rigid_registration.json',rows);freeze('bounded_rigid_results',[Path(__file__),R/'metrics/bounded_rigid_registration.json',R/'metrics/sparse_photo_bridges.json']);print('RIGID13_DONE',flush=True)
if __name__=='__main__':main()
