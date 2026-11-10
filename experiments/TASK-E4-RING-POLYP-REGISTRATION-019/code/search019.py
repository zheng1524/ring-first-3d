from objective019 import *
from geometry019 import proxies
from scipy.optimize import minimize_scalar
import math

def angular(a,b):return abs((a-b+180)%360-180)
def run(scope,ids,shapes):
 obj=PoseObjective(ids,scope);rows=[];start=time.time()
 for parity in [1,-1]:
  for angle in range(0,360,5):
   s=obj.score(tensor(yaw_matrix(angle,parity),torch.float64));rows.append(dict(scope=scope,yaw_deg=angle,parity=parity,T=yaw_matrix(angle,parity),source='FULL_GRID_5_DEG',**s))
  save('metrics/'+scope+'_FULL_SEARCH.json',rows);print('FULL_YAW_HALF',scope,parity,flush=True)
 # Competitive local minima are identified on FIT only, no HOLDOUT image is loaded.
 candidate=[]
 for key in ['polyp','feature','total']:
  best=[]
  for row in sorted(rows,key=lambda r:r[key]):
   if all(r['parity']!=row['parity']or angular(r['yaw_deg'],row['yaw_deg'])>=20 for r in best):best.append(row)
   if len(best)>=3:break
  for row in best:
   def scalar(a):return obj.score(tensor(yaw_matrix(a%360,row['parity']),torch.float64))[key]
   opt=minimize_scalar(scalar,bounds=(row['yaw_deg']-5,row['yaw_deg']+5),method='bounded',options=dict(xatol=.1,maxiter=16));ang=float(opt.x%360);candidate.append(dict(scope=scope,yaw_deg=ang,parity=row['parity'],T=yaw_matrix(ang,row['parity']),source='CONTINUOUS_'+key,**obj.score(tensor(yaw_matrix(ang,row['parity']),torch.float64))))
 if scope=='CROSS':
  for x in load(R/'config/HISTORICAL_CANDIDATES.json'):
   T=np.asarray(x['T']);ang=float(np.degrees(np.arctan2(T[1,0],T[0,0]))%360);candidate.append(dict(scope=scope,yaw_deg=ang,parity=1,T=yaw_matrix(ang),source='RING_PROJECTED_'+x['tag'],**obj.score(tensor(yaw_matrix(ang),torch.float64))))
  # Keep every geometric proposal; ambiguity is not converted into a unique truth.
  for x in shapes:
   candidate.append(dict(scope=scope,yaw_deg=x['yaw_deg'],parity=x['parity'],T=x['T'],source='GEOMETRY',shape_status=x['status'],direction_strength_proxy=x['direction_strength_proxy'],**obj.score(tensor(x['T'],torch.float64))))
 for x in obj.feature.pnp:
  T=np.asarray(x['T_candidate']);ang=float(np.degrees(np.arctan2(T[1,0],T[0,0]))%360);candidate.append(dict(scope=scope,yaw_deg=ang,parity=1,T=yaw_matrix(ang),source='SIFT_PNP_YAW_'+x['target'],**obj.score(tensor(yaw_matrix(ang),torch.float64))))
 allrows=rows+candidate;A1=min(allrows,key=lambda r:r['polyp']);A3=min(allrows,key=lambda r:r['feature']);A4=min(allrows,key=lambda r:r['total']);seeds=[]
 for x in sorted(allrows,key=lambda r:r['total']):
  if all(s['parity']!=x['parity']or angular(s['yaw_deg'],x['yaw_deg'])>=20 for s in seeds):seeds.append(x)
  if len(seeds)==3:break
 shape_rows=[x for x in candidate if x['source']=='GEOMETRY'];A2=min(shape_rows,key=lambda r:r['polyp'])if shape_rows else None;out=dict(scope=scope,A1=A1,A2=A2,A3=A3,A4=A4,refinement_seeds=seeds,seconds=time.time()-start,SIFT_available=bool(obj.feature.data or obj.feature.proj),A1_semantics='Ring-reduced silhouette angular search; Ring-only canonical yaw0 separate')
 save('metrics/'+scope+'_SEARCH_CANDIDATES.json',candidate);save('results/'+scope+'_SEARCH_SELECTION.json',out);table('metrics/'+scope+'_FULL_SEARCH.csv',[{k:v for k,v in x.items()if k not in ['T','per_frame']}for x in rows]);save('metrics/'+scope+'_SOURCE_WEIGHTS.json',obj.w);print('SEARCH_DONE',scope,[(k,None if out[k]is None else(round(out[k]['yaw_deg'],3),out[k]['parity'],round(out[k]['total'],5)))for k in ['A1','A2','A3','A4']],flush=True);return out

def main():
 gate=load(R/'metrics/PROJECTION_AND_POSE_GRADIENT_GATE.json');assert gate['all_passed'];v=load(R/'config/VIEWS.json');shapes=proxies();save('provenance/BEFORE_SEARCH_FREEZE.json',dict(epoch=time.time(),views=asset(R/'config/VIEWS.json'),protocol=asset(R/'config/PROTOCOL.json'),written_protocol=asset(R/'01_PROTOCOL.md'),source=[asset(p)for p in(R/'code').glob('*.py')],HOLDOUT=False,GT=False,body=asset(R/'inputs/G01/BODY018.npz')));run('CROSS',[x['id']for x in v if x['video']=='005'and x['role']=='FIT'],shapes);torch.cuda.empty_cache();neg=load(R/'config/NEGATIVE_SPLIT.json');run('NEGATIVE',neg['target_fit'],[])
if __name__=='__main__':main()
