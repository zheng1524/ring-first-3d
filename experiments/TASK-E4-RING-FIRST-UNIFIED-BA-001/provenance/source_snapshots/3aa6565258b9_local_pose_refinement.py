from v9_common import *
from selection import pairdata
import inspect
sys.path.insert(0,str(V8/'scripts'));import registration_v2 as legacy
sys.path.insert(0,str(V7/'scripts'));from photo_registration import epi,tri
def main():
 freeze('local_pose_refinement_protocol',[Path(__file__),R/'config.json',R/'inputs/selected_view_groups.json'],GT_role='No GT; Ring-preserving axial yaw and normal-flip candidates only; shared100nfev, same72yaw grid')
 views={x['id']:x for x in load('inputs/graph_views.json')};ns=dict(legacy.__dict__);ns['getpair']=pairdata;exec(inspect.getsource(legacy.third_checks),ns);third=ns['third_checks'];out=[];cache={}
 for g in load('inputs/selected_view_groups.json'):
  ref=g['reference'];rp=np.array(views[ref]['pose'])
  for mode in ['S0','S1','S2','S3']:
   for method in ['SIFT','MASt3R']:
    trials=[]
    for target in sorted(g[mode]):
     key=(ref,target,method);dd=pairdata(method,ref,target);tpose=np.array(views[target]['pose']);train=np.flatnonzero(dd['train']);train=train[np.linspace(0,len(train)-1,min(400,len(train)),dtype=int)] if len(train) else train
     if key not in cache:
      fits=[]
      if len(train)>=8:
       def res(yaw,flip):return epi(rp,legacy.spin(tpose,float(yaw),flip),dd['p'][train],dd['q'][train],K,K)
       seeds=[]
       for flip in [False,True]:
        for yaw in np.linspace(-np.pi,np.pi,72,endpoint=False):
         e=res(yaw,flip);seeds.append((float(np.mean(2*(np.sqrt(1+e**2)-1))),yaw,flip))
       seeds.sort();chosen=[]
       for seed in seeds:
        p=legacy.spin(tpose,seed[1],seed[2])
        if all(np.linalg.norm(p[:3,3]-legacy.spin(tpose,y[1],y[2])[:3,3])>1 for y in chosen):chosen.append(seed)
        if len(chosen)==3:break
       for _,yaw,flip in chosen:
        f=least_squares(lambda x:res(x[0],flip),[yaw],loss='soft_l1',max_nfev=100);e=res(f.x[0],flip);fits.append(dict(pose=legacy.spin(tpose,f.x[0],flip),score=float(np.mean(2*(np.sqrt(1+e**2)-1))),nfev=f.nfev))
       fits.sort(key=lambda x:x['score'])
      cache[key]=fits
     fits=cache[key];rec=dict(target=target,numeric=bool(fits),accepted=False,train=len(train))
     if fits:
      po=fits[0]['pose'];p,q=dd['p'][dd['held']],dd['q'][dd['held']];X=tri(rp,po,p,q,K,K);a,za=project(X,rp,K);b,zb=project(X,po,K);hh=stats(np.r_[np.linalg.norm(a-p,axis=1),np.linalg.norm(b-q,axis=1)]);pos=float(((za>0)&(zb>0)).mean()) if len(p) else 0.;cc=third(method,sorted([ref]+[x for x in g[mode] if x!=target]),target,po,K,views);ob=np.load(R/f'observations/{target}_ring.npz');qheld=ob['q_held'] if 'q_held' in ob else ob['ring_heldout'];rh=stats(cKDTree(prev.contours(po,n=2048,K0=K).reshape(-1,2)).query(qheld)[0]);centers=np.array([x['pose'][:3,3] for x in fits]);spread=float(np.linalg.norm(centers[:,None]-centers[None,:],axis=2).max());thirdpass=any(x['n']>=8 and x['error_px']['MAE']<=3 and x['error_px']['p95']<=6 and x['positive']>=.95 for x in cc);passed=bool(hh['n']>=16 and hh['MAE']<=3 and hh['p95']<=6 and pos>=.95 and rh['MAE']<=3 and rh['p95']<=6 and spread<=2 and thirdpass);rec.update(accepted=passed,held_px=hh,positive=pos,Ring_held_px=rh,center_spread_mm=spread,third_source=cc,training_best=po,formal_pose=po if passed else np.full((4,4),np.nan),all_initializations=fits)
     trials.append(rec)
    out.append(dict(dataset=g['dataset'],mode=mode,matcher=method,accepted=all(x['accepted'] for x in trials),reference_fixed=True,targets=trials,does_not_modify_frozen_MVS_inputs=True));save('metrics/local_pose_refinement.json',out);print('LOCAL_POSE',g['dataset'],mode,method,'pass',all(x['accepted'] for x in trials),[x['accepted'] for x in trials],flush=True)
 save('predictions/local_formal_poses.json',[dict(dataset=x['dataset'],mode=x['mode'],matcher=x['matcher'],reference_fixed=True,targets=[dict(id=t['target'],accepted=t['accepted'],pose=t.get('formal_pose',np.full((4,4),np.nan))) for t in x['targets']]) for x in out]);freeze('local_pose_refinement_results',[Path(__file__),R/'metrics/local_pose_refinement.json',R/'predictions/local_formal_poses.json']);print('LOCAL_POSE_DONE',flush=True)
if __name__=='__main__':main()
