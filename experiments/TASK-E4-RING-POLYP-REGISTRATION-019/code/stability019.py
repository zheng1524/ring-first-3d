"""Fixed FIT-only subset yaw sensitivity; uses cached exact P3D silhouettes, not new rendering."""
from common import *
from renderer019 import yaw_matrix

def hubn(x):return np.where(abs(x)<1,.5*x*x,abs(x)-.5)
def score_feature(H,scope,target_subset=None,point_parity=None):
 vv={v['id']:v for v in load(R/'config/VIEWS.json')};E={};P={}
 for a in load(R/'features'/(scope+'_EPI.json')):
  if target_subset is not None and a['b']not in target_subset:continue
  x,y=vv[a['a']],vv[a['b']];C=H@np.asarray(y['T']);A=np.linalg.inv(C)@np.asarray(x['T']);t=A[:3,3];S=np.array([[0,-t[2],t[1]],[t[2],0,-t[0]],[-t[1],t[0],0]]);F=np.linalg.inv(y['K']).T@S@A[:3,:3]@np.linalg.inv(x['K']);p,q=np.asarray(a['p']),np.asarray(a['q'])
  if point_parity is not None:p,q=p[point_parity::2],q[point_parity::2]
  if not len(p):continue
  pp=np.c_[p,np.ones(len(p))];qq=np.c_[q,np.ones(len(q))];fp=pp@F.T;fq=qq@F;res=np.sum(qq*fp,axis=1)/np.sqrt(np.maximum(np.sum(fp[:,:2]**2,axis=1)+np.sum(fq[:,:2]**2,axis=1),1e-20));E.setdefault(a['b'],[]).append(float(hubn(res/3).mean()))
 for a in load(R/'features'/(scope+'_PNP.json')):
  if not a['success']or(target_subset is not None and a['target']not in target_subset):continue
  v=vv[a['target']];X=np.asarray(a['landmark_X']);u=np.asarray(a['uv'])
  if point_parity is not None:X,u=X[point_parity::2],u[point_parity::2]
  if not len(X):continue
  C=H@v['T'];Pcam=(X-C[:3,3])@C[:3,:3];pp=Pcam@np.asarray(v['K']).T;uv=pp[:,:2]/np.maximum(pp[:,2:],1e-6);L=np.where((Pcam[:,2]>0)[:,None],hubn((uv-u)/3),100.);P.setdefault(a['target'],[]).append(float(L.mean()))
 channels=[np.mean([np.mean(x)for x in d.values()])for d in [E,P]if d];return float(np.mean(channels))if channels else None

def main():
 assert(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json').exists();out=[];profiles=[]
 for scope in ['CROSS','NEGATIVE']:
  grid=load(R/'metrics'/(scope+'_FULL_SEARCH.json'));ids=list(dict.fromkeys(x['view']for x in grid[0]['per_frame']));ids=sorted(ids);sets=[('ALL',None,None),('TARGET_ALTERNATING_0',set(ids[::2]),None),('TARGET_ALTERNATING_1',set(ids[1::2]),None),('SIFT_MATCH_HALF_0',None,0),('SIFT_MATCH_HALF_1',None,1)];base=load(R/'results'/(scope+'_SEARCH_SELECTION.json'))['A4'];err=[]
  for name,chosen,half in sets:
   rows=[]
   for r in grid:
    selected=[x for x in r['per_frame']if chosen is None or x['view']in chosen];W=sum(x['weight']for x in selected);mask=sum(x['polyp_loss']*x['weight']for x in selected)/W;f=score_feature(np.asarray(r['T']),scope,chosen,half)
    if name=='ALL':err.append(abs(f-r['feature']))
    rows.append(dict(scope=scope,subset=name,yaw_deg=r['yaw_deg'],parity=r['parity'],polyp=mask,feature=f,total=mask+.05*f,T=r['T']))
   best=min(rows,key=lambda r:r['total']);out.append(dict(best,base_continuous_yaw=base['yaw_deg'],angular_difference_deg=abs((best['yaw_deg']-base['yaw_deg']+180)%360-180),same_parity=best['parity']==base['parity'],diagnostic='fixed 5deg grid yaw subset sensitivity; NOT extra6DoF hyperparameter search or final model selection'));profiles+=rows
  assert max(err)<1e-5,(scope,max(err))
 save('metrics/FIT_ONLY_SUBSET_STABILITY.json',dict(selected=out,profiles=profiles,GT=False,HOLDOUT=False,subsets='lexicographic alternating frozen FIT IDs / alternating fixed SIFT correspondences; not cherry-picked by outcomes',six_DoF_stability='all three main A5 initializations reported separately',numpy_vs_official_feature_loss_equivalence_max=max(err)));table('metrics/FIT_ONLY_SUBSET_STABILITY.csv',out);print('FIT_ONLY_SUBSET_STABILITY_COMPLETE',flush=True)
if __name__=='__main__':main()
