"""Reuse actual Ceres LM/Schur: shared source transform and supported full6 camera/XYZ.
The 005 direct-PnP initialization already uses004RGB map; H is a refinement,
not a claimed independent005SfM recovery. No Body/HERO pixels or XYZ enter BA.
"""
from cameras import *
from ceres_backend import *

class Bundle:
 def __init__(self,g,vs,mode,selected):
  self.g=g;self.vs={v['id']:v for v in vs if v.get('C')is not None};self.mode=mode;self.sel=selected;self.q={c:np.zeros(6)for c in self.vs};self.H={s:np.zeros(6)for s in ['004','005','PHOTO']};self.pc={c:PoseCache(v['C'],np.eye(4))for c,v in self.vs.items()};self.obs=[];self.ring={};self.mp=rgb_map(g);self.X={};self.X0={}
  for c in selected:
   v=self.vs[c];rr=load(v.get('rgb_geometry_path',N/'inputs'/c/'RGB_GEOMETRY.json'));self.ring[c]=observe(v)
   # Frozen uniform grid of actual RGB inlier IDs, no distance-based identity.
   for r in sample(rr['fit_pnp_inliers'],48):
    k=r['landmark'];self.X.setdefault(k,np.array(r['X'],float));self.obs.append(dict(cid=c,k=k,uv=r['uv'],source=v['video']))
  self.X0={k:x.copy()for k,x in self.X.items()};count=collections.Counter((o['k'],o['source'])for o in self.obs);trvid=collections.defaultdict(set)
  for o in self.obs:trvid[o['k']].add(o['source'])
  for o in self.obs:o['w']=.2/max(1,len(self.X))/len(trvid[o['k']])/count[o['k'],o['source']]
  self.anchor=next((c for c in selected if self.vs[c]['video']=='004'),None)
 def C(self,c):v=self.vs[c];return self.pc[c].get(self.q[c],self.H[v['video']])[0]
 def objective(self):
  parts=dict(Ring=0.,RGB=0.,pose_prior=0.,XYZ_prior=0.)
  for c in self.sel:
   C=self.C(c);ob=self.ring[c];parts['Ring']+=score(C,ob)/max(1,len(self.sel))
  for o in self.obs:
   uv,z=projection(self.X[o['k']][None],self.C(o['cid']),K0);d=np.linalg.norm(uv[0]-o['uv'])/3.;parts['RGB']+=o['w']*(.5*d*d if d<=1 else d-.5)
  parts['pose_prior']=.01/12*(sum(q@q for q in self.q.values())/max(1,len(self.sel))+sum(h@h for h in self.H.values()))
  parts['XYZ_prior']=.001/max(1,len(self.X))*sum(np.sum((self.X[k]-self.X0[k])**2)/2 for k in self.X)
  return float(sum(parts.values())),parts
 def physical(self):
  for c in self.sel:
   C=self.C(c);B=np.array(self.vs[c]['C']);delta=np.linalg.norm(C[:3,3]-B[:3,3]);rot=np.degrees(Rotation.from_matrix(C[:3,:3]@B[:3,:3].T).magnitude());f=physical(self.vs[c],C,self.ring[c])
   if not f['physical_valid']or delta>1.2 or rot>10:return False,dict(cid=c,center_delta_mm=delta,rotation_delta_deg=rot,physical=f)
  if self.X and max(np.linalg.norm(self.X[k]-self.X0[k])for k in self.X)>3:return False,dict(reason='XYZ3mmBound')
  return True,{}
 def build(self):
  p=ce.Problem();keep=[];loss=[]
  def add(c,params,l=None):keep.append(c);loss.append(l);p.add_residual_block(c,l,params)
  for c in self.sel:
   v=self.vs[c];ob=self.ring[c];cp=correspondence(self.C(c),K0,{k:ob.get(k,np.empty((0,2)))for k in ['inner','outer']});
   if len(cp['theta']):add(RingCost(self.pc[c],K0,cp,1/max(1,len(self.sel))),[self.q[c],self.H[v['video']]])
  for o in self.obs:add(Reprojection(self.pc[o['cid']],K0,o['uv'],o['w']),[self.q[o['cid']],self.H[self.vs[o['cid']]['video']],self.X[o['k']]],ce.HuberLoss(np.sqrt(o['w'])))
  for c in self.sel:
   if not p.has_parameter_block(self.q[c]):continue
   add(Prior(np.zeros(6),np.ones(6)*np.sqrt(.01/6/max(1,len(self.sel)))),[self.q[c]])
   # Complete6D is released only when independent RGB matrix has rank6.
   if self.mode=='SHARED_SE3'or c==self.anchor or self.vs[c].get('RGB_inliers_N',0)<10:p.set_parameter_block_constant(self.q[c])
   for j in range(6):p.set_parameter_lower_bound(self.q[c],j,-1.);p.set_parameter_upper_bound(self.q[c],j,1.)
  for s,h in self.H.items():
   if not p.has_parameter_block(h):continue
   add(Prior(np.zeros(6),np.ones(6)*np.sqrt(.01/6)),[h])
   # PHOTO independent localfull6, no meaningless shared transform among3photos.
   if s in ['004','PHOTO']:p.set_parameter_block_constant(h)
   for j in range(6):p.set_parameter_lower_bound(h,j,-1.);p.set_parameter_upper_bound(h,j,1.)
  for k,x in self.X.items():
   if not p.has_parameter_block(x):continue
   if self.mode=='SHARED_SE3':p.set_parameter_block_constant(x)
   else:add(Prior(self.X0[k],np.ones(3)*np.sqrt(.001/max(1,len(self.X)))),[x])
  self.keep=keep;self.loss=loss;return p
 def state(self):return dict(q={k:v.copy()for k,v in self.q.items()},H={k:v.copy()for k,v in self.H.items()},X={k:v.copy()for k,v in self.X.items()})
 def restore(self,s):
  for key in ['q','H','X']:
   for k,v in s[key].items():getattr(self,key)[k][:]=v
 def run(self):
  history=[];initial=self.objective();start=time.time()
  for it in range(2):
   old=self.state();before=self.objective()[0];p=self.build();d=solver(p,self.g+'/'+getattr(self,'label',self.mode)+'/'+str(it),12,self.mode!='SHARED_SE3');new=self.state();trials=[];accepted=False
   for b in range(8):
    a=.5**b;self.restore({key:{k:old[key][k]+a*(new[key][k]-old[key][k])for k in old[key]}for key in old});valid,why=self.physical();cost=self.objective()[0]if valid else None;ok=valid and cost<=before+1e-10;trials.append(dict(alpha=a,physical=valid,why=why,cost=cost,accepted=ok))
    if ok:accepted=True;break
   if not accepted:self.restore(old)
   history.append(dict(outer=it,accepted=accepted,before=before,after=self.objective(),trials=trials,Ceres=d));save('registration/'+self.g+'/'+getattr(self,'label',self.mode)+'_TRACE.json',history)
   if not accepted:break
  result=dict(group=self.g,mode=self.mode,selected=self.sel,initial_objective=initial,final_objective=self.objective(),poses={c:self.C(c)for c in self.vs},**self.state(),source_H={k:exp(v)for k,v in self.H.items()},accepted=sum(h['accepted']for h in history),seconds=time.time()-start,sharedXYZ_N=len(self.X),realRGB_N=len(self.obs),complete6_local=self.mode=='JOINT_FULL6',physical=self.physical(),GT_HERO_Body_in_loss=False,source='actualCeres2.2LM Schur (backend copied from U)',parameterization='left SE3 exp with fixed metric S; sameworld004;anchor004fixed;H004I;HphotoI;noSim3;005directPnPinitial explicitly already004anchored')
  save('registration/'+self.g+'/'+getattr(self,'label',self.mode)+'_FINAL.json',result);return result

def select_for_BA(vs):
 usable=[v for v in vs if v.get('C')is not None and v['role']=='FIT'and v.get('RGB_inliers_N',0)>=10 and v.get('Ring',{}).get('physical_valid',False)];chosen=[]
 # source-balanced6degree quantized direction then greedy maxmin; noHOLDOUT/HERO.
 for s in ['004','005','PHOTO']:
  a=[v for v in usable if v['video']==s];out=[]
  if a:out=[max(a,key=lambda v:v['RGB_inliers_N'])]
  while len(out)<12 and len(out)<len(a):
   cand=[v for v in a if v not in out];v=max(cand,key=lambda v:min(angle(v['C'][:3][3]if False else np.array(v['C'])[:3,3],np.array(o['C'])[:3,3])for o in out)+.1*np.log1p(v['RGB_inliers_N']));out.append(v)
  chosen+=out
 return [v['id']for v in chosen]

def qualification(v,C):
 if C is None:return dict(formal=False,HERO_target_eligible=False,status='NO_NUMERIC_POSE')
 if v['role']=='HOLDOUT':return dict(formal=False,HERO_target_eligible=False,status='PROTECTED_HOLDOUT')
 rp=Path(v.get('rgb_geometry_path',N/'inputs'/v['id']/'RGB_GEOMETRY.json'));rr=load(rp)if rp.exists()else dict(matches=[],fit_pnp_inliers=[]);ob=observe(v);em=errors(v,C,rr);f=physical(v,C,ob);js=[]
 for r in rr['fit_pnp_inliers']:
  uv,J,z=__import__('torus').project_dC(np.array(r['X']),C,K0);d=-np.eye(3);from scipy.spatial.transform import Rotation as Rot
  # numerical camera perturbation only for rank evidence, no inverse modeling.
  jj=[]
  for k in range(6):
   q=np.zeros(6);q[k]=1e-5;p1=projection(np.array(r['X'])[None],exp(q)@C,K0)[0][0];q[k]=-1e-5;p0=projection(np.array(r['X'])[None],exp(q)@C,K0)[0][0];jj.append((p1-p0)/2e-5)
  js.append(np.array(jj).T)
 sv=np.linalg.svd(np.concatenate(js),compute_uv=False)if js else np.array([]);rank=int((sv>sv[0]*1e-5).sum())if len(sv)else 0
 reasons=[];hc=em['FEATURE_HELD'];fc=em['FIT'];med=[f[k]['median']for k in ['inner','outer']if f[k]['N']]
 if not f['physical_valid']:reasons.append('PHYSICAL_INVALID')
 if len(rr['fit_pnp_inliers'])<10 or em['FIT_cells']<4 or rank<6:reasons.append('RGB_6DOF_INSUFFICIENT')
 if hc['N']<4:reasons.append('INDEPENDENT_RGB_FEATURES_TOO_FEW')
 elif hc['median']>8 or hc['p95']>20:reasons.append('INDEPENDENT_RGB_RESIDUAL_LARGE')
 if f['Ring_IoU']<.35 or not med or max(med)>10:reasons.append('RING_MASK_TYPED_ARC_WEAK')
 formal=not reasons;return dict(formal=formal,HERO_target_eligible=formal,status='METRIC_POSE_VALIDATED_CONDITIONAL'if formal else'NUMERIC_EXPLORATORY_ONLY',qualification_reasons=reasons,RGB_evaluation=em,Ring=f,RGB_rank=rank,RGB_singular_values=sv,RGB_condition=float(sv[0]/sv[-1])if len(sv)and sv[-1]>0 else None,calibrated_camera_truth=False,independent_validation='held descriptor trackIDs excludeupdates;map/canonical ancestry historical conditional')

def main(g):
 vs=load(N/'config'/ (g+'_INITIAL_CAMERAS.json'));selected=select_for_BA(vs);save('registration/'+g+'/BA_SCOPE_FROZEN.json',dict(selected=selected,source='FIT RGB count/direction only',GT=False));snapshot_read([Path(__file__),N/'code/ceres_backend.py',N/'code/torus.py',N/'config/NUMERICAL_PROTOCOL.json'],'BA_CODE_'+g+'.json')
 shared=Bundle(g,vs,'SHARED_SE3',selected).run()if selected else None;joint=Bundle(g,vs,'JOINT_FULL6',selected).run()if selected else None
 # All candidate prediction files frozen before held RGB and coverage geometry.
 raw={v['id']:v.get('C')for v in vs};save('registration/'+g+'/ORIGINAL_RF_RGB_POOL.json',raw);result=joint if joint else shared;poses=result['poses']if result else raw;save('registration/'+g+'/PRIMARY_POSES.json',dict(poses=poses,selection='fixed JOINT_FULL6 route; no held/HERO ranking',fallback_only_no_numeric_BA=not bool(result)))
 freeze('provenance/'+g+'_CAMERAS_FROZEN_BEFORE_HELD_HERO.json',[N/'registration'/g/'PRIMARY_POSES.json']+[N/'registration'/g/(mode+'_FINAL.json')for mode in ['SHARED_SE3','JOINT_FULL6']if(N/'registration'/g/(mode+'_FINAL.json')).exists()],GT=False,HERO=False,held=False)
 out=[]
 for v in vs:
  C=poses.get(v['id']);q=qualification(v,np.array(C)if C is not None else None);out.append(v|dict(C=C,**q))
 save('config/'+g+'_CAMERAS.json',out);table('metrics/'+g+'_CAMERA_QUALITY.csv',out);print('REGISTERED',g,len(out),'formal',sum(v['formal']for v in out),flush=True)
if __name__=='__main__':main(sys.argv[1])
