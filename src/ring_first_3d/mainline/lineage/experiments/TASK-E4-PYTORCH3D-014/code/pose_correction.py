"""Video-shared SE(3), Ring + independent static-background RGB observations only."""
from expand_cameras import *
from scipy.optimize import least_squares
import importlib.util

def torus_projection(T,K,radius,wire):
 p=Path('/home/liu/polyp_research/ring_anchor_3d/scripts/geometry.py');ns=dict(np=np,cv2=cv2)
 import ast
 node=next(x for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='torus_contours');exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),ns)
 return ns['torus_contours'](T[:3,3],T[:3,:3],K,R=radius,r=wire,n=256).reshape(-1,2)

def delta(x):
 D=np.eye(4);D[:3,:3]=Rotation.from_rotvec(x[:3]).as_matrix();D[:3,3]=x[3:];return D

def build_matches(A,B):
 lm,pr=landmarks(A);data=[]
 for v in B:
  f=features(v);mm=matches(lm['des'],f['des'])
  if not len(mm):continue
  X=lm['X'][mm[:,0]];uv=f['xy'][mm[:,1]];cells=(uv//[80,60]).astype(int);held=(cells.sum(1)%4==0)
  # Entire every-third B image is independent of the fit as well as spatially held features.
  imageheld=(B.index(v)%3==2)
  for j in range(len(mm)):data.append(dict(view=v['id'],X=X[j],uv=uv[j],held=bool(held[j]or imageheld),image_held=imageheld))
 return data,pr

def ring_data(B):
 out=[]
 for v in B:
  lab=np.array(Image.open(v['Mask_source']));rm=lab==2;ct=contour(rm);px=np.clip(ct.astype(int),[0,0],[639,359]);near=cv2.dilate((lab==1).astype(np.uint8),np.ones((5,5),np.uint8));ct=ct[near[px[:,1],px[:,0]]==0]
  if len(ct):out.append(dict(id=v['id'],q=ct[np.linspace(0,len(ct)-1,min(len(ct),128)).astype(int)]))
 return out

def solve(A,B,label,case):
 data,pairs=build_matches(A,B);by={v['id']:v for v in B};rg=ring_data(B);fit=[d for d in data if not d['held']];held=[d for d in data if d['held']];cfg=load(R/'config/PROTOCOL.json')['B1'];records=[]
 def bg(x,rows):
  if not rows:return np.empty((0,2))
  D=delta(x);ret=[]
  for cid in sorted(set(d['view']for d in rows)):
   dd=[d for d in rows if d['view']==cid];v=by[cid];pu,z=project(np.array([d['X']for d in dd]),D@np.array(v['T']),np.array(v['K']));ret.extend(pu-np.array([d['uv']for d in dd]))
  return np.asarray(ret)
 def ring(x):
  D=delta(x);ret=[]
  for d in rg:
   v=by[d['id']]
   try:cr=torus_projection(D@np.array(v['T']),np.array(v['K']),case['R_mid_mm'],case['wire_mm']);qq=cKDTree(cr).query(d['q'])[0];ret.extend(qq/np.sqrt(len(d['q'])*len(rg)))
   except Exception:ret.extend(np.full(len(d['q']),100./np.sqrt(len(d['q'])*len(rg))))
  return np.array(ret)*4
 prior=np.r_[np.deg2rad([cfg['tilt_prior_deg'],cfg['tilt_prior_deg'],cfg['yaw_prior_deg']]),np.full(3,cfg['translation_prior_mm'])]
 def residual(x):return np.r_[bg(x,fit).ravel()*np.sqrt(80/max(1,len(fit))),ring(x),x/prior]
 # A lack of measured RGB evidence is an explicit unobservable result, never Ring-yaw certification.
 cells=len(set((int(d['uv'][0]//80),int(d['uv'][1]//60))for d in fit));enough=len(fit)>=cfg['fit_BG_min']and len(held)>=cfg['held_BG_min']and cells>=cfg['minimum_image_cells']
 if enough:
  for yaw in cfg['seeds_yaw_deg']:
   x=np.zeros(6);x[2]=np.deg2rad(yaw);lo=np.r_[np.deg2rad([-10,-10,-181]),[-3]*3];hi=-lo
   z=least_squares(residual,x,bounds=(lo,hi),loss='soft_l1',f_scale=2,max_nfev=cfg['max_nfev'],ftol=1e-7,xtol=1e-7,gtol=1e-7)
   ss=np.linalg.svd(z.jac[:2*len(fit)],compute_uv=False);score=float(np.mean(2*(np.sqrt(1+(residual(z.x)/2)**2)-1)));records.append(dict(yaw_seed=yaw,x=z.x,Delta_T=delta(z.x),fit_score=score,fit_background_px=stats(np.linalg.norm(bg(z.x,fit),axis=1)),held_background_px=stats(np.linalg.norm(bg(z.x,held),axis=1)),BG_jacobian_singular=ss,rank=int((ss>ss[0]*cfg['observability_rank_relative']).sum())if len(ss)else 0,nfev=z.nfev))
  records.sort(key=lambda d:d['fit_score']);best=records[0];x=np.array(best['x']);near=[r for r in records if r['fit_score']<best['fit_score']*1.05+.02];spread=max(np.linalg.norm(np.asarray(r['x'])-x)for r in near)
  zero=stats(np.linalg.norm(bg(np.zeros(6),held),axis=1));after=best['held_background_px'];supported=best['rank']==6 and spread<.1 and after['MAE']<zero['MAE']*.95
 else:x=np.zeros(6);best=None;spread=None;zero=stats(np.linalg.norm(bg(x,held),axis=1));supported=False
 out=dict(label=label,fit_BG_N=len(fit),held_BG_N=len(held),image_cells=cells,original_held_BG_px=zero,candidates=records,selected_FIT_only=best,near_optimum_parameter_spread=spread,status='SUPPORTED_CORRECTION_CANDIDATE'if supported else'INSUFFICIENT_INDEPENDENT_EVIDENCE',apply=supported,Delta_T=delta(x)if supported else np.eye(4),unapplied_candidate=delta(x),Ring_before=stats(ring(np.zeros(6))/4),Ring_candidate=stats(ring(x)/4),Polyp_HERO_in_pose_objective=False,main_A_identity=True,no_scale=True,B2='NOT_EVALUABLE_UNLESS_B1_SUPPORTED',BG_observations=data)
 save('metrics/pose/'+label+'.json',out);table('metrics/pose/'+label+'_MATCHES.csv',data);print('POSE',label,out['status'],len(fit),len(held),flush=True);return out

def main():
 vv=load(R/'config/EXISTING_VIEWS.json');case=load(R/'config/CASE_LOCK.json')[0];A=[v for v in vv if v['sid']=='G01_v004'];B=[v for v in vv if v['sid']=='G01_v005'];out=solve(A,B,'G01_004_TO_005',case);reverse=solve(B,A,'G01_005_TO_004_DIAGNOSTIC',case)
 A=sorted(A,key=lambda v:float(v['raw_frame'])if v['raw_frame']is not None else float(np.asarray(v['T'])[0,3]));mid=len(A)//2;negative=solve(A[:mid],A[mid:],'G01_004_TIME_SPLIT_NEGATIVE',case)
 save('config/VIDEO_CORRECTIONS.json',dict(G01_v004=np.eye(4),G01_v005=out['Delta_T']));save('provenance/POSE_CORRECTION_FREEZE.json',dict(epoch=time.time(),code=asset(Path(__file__)),cross=out['status'],negative=negative['status'],background_only=True,Mesh_frozen=True))
if __name__=='__main__':main()
