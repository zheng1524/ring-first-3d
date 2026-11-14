"""One real Ceres problem per joint group; camera blocks, shared H and XYZ together."""
from ceres_backend import *
from analytic_visibility import torus_polynomial
from visible_arcs import qualified
class Joint:
 def __init__(self,group,arm,initial=None,one=None):
  self.group=group;self.arm=arm;self.p=load(N/'config/PROTOCOL.json');self.views=[v for v in load(N/'config/VIEWS.json')if v['group']==group];self.vd={v['id']:v for v in self.views};self.fit=[v for v in self.views if v['role']=='FIT'];self.one=one;self.tracks=[t for t in load(N/'config/TRACKS.json')if t['group']==group and t['role']=='TRACK_FIT'];self.local={v['id']:np.zeros(6)for v in self.views};self.H={video:np.zeros(6)for video in {v['video']for v in self.views}};self.H0={video:np.array(next(v['H0']for v in self.views if v['video']==video))for video in self.H};self.X={t['track_id']:np.array(t['X0'],float)for t in self.tracks};self.X0={k:x.copy()for k,x in self.X.items()};self.caches={v['id']:PoseCache(v['RF_native'],v['H0'])for v in self.views};self.ringobs={};self.ringN={};self.constraints=[]
  for v in self.fit:
   r,_=qualified(v);self.ringobs[v['id']]={k:np.asarray(r[k])[np.linspace(0,len(r[k])-1,min(self.p['ring_observation_max_per_curve'],len(r[k])),dtype=int)]if len(r[k])else np.empty((0,2))for k in ['inner','outer']}
  self.obs=[]
  for t in self.tracks:
   obs=[o for o in t['observations']if o['view']in self.vd and self.vd[o['view']]['role']=='FIT'];videos=collections.Counter(self.vd[o['view']]['video']for o in obs);blocks=collections.Counter((self.vd[o['view']]['video'],self.vd[o['view']].get('direction_block',self.vd[o['view']].get('direction_block019','UNKNOWN')))for o in obs)
   for o in obs:
    video=self.vd[o['view']]['video'];block=(video,self.vd[o['view']].get('direction_block',self.vd[o['view']].get('direction_block019','UNKNOWN')));nblock=sum(b[0]==video for b in blocks);w=.2/max(1,len(self.tracks))/len(videos)/nblock/blocks[block];self.obs.append(o|dict(track_id=t['track_id'],weight=w,cross=t['cross_video']))
  self.anchors={video:next(v['id']for v in self.fit if v['video']==video)for video in self.H};self.nobs=collections.Counter(o['view']for o in self.obs)
  if initial:
   for k,v in initial['local'].items():self.local[k][:]=v
   for k,v in initial['H_delta'].items():self.H[k][:]=v
   for k,v in initial.get('X',{}).items():
    if int(k)in self.X:self.X[int(k)][:]=v
  self.weights={}
  for video in self.H:
   ff=[v for v in self.fit if v['video']==video];bc=collections.Counter(v.get('direction_block',v.get('direction_block019','UNKNOWN'))for v in ff)
   for v in ff:self.weights[v['id']]=1/len(self.H)/len(bc)/bc[v.get('direction_block',v.get('direction_block019','UNKNOWN'))]
 def C(self,cid):v=self.vd[cid];return self.caches[cid].get(self.local[cid],self.H[v['video']])[0]
 def actual(self):
  parts=dict(Torus=0.,SIFT=0.,pose_prior=0.,landmark_prior=0.,relative_motion_prior=0.)
  if self.arm!='B1':
   for v in self.fit:
    cid=v['id'];cp=correspondence(self.C(cid),np.array(v['K']),self.ringobs[cid],self.p['torus_samples']);co=RingCost(self.caches[cid],v['K'],cp,self.weights[cid]);r,_=co.values(self.local[cid],self.H[v['video']]);parts['Torus']+=r@r/2
  os=[o for o in self.obs if(self.arm!='B2'or o['cross'])and(self.one is None or o['view']==self.one)]
  for o in os:
   v=self.vd[o['view']];uv,z=projection(self.X[o['track_id']][None],self.C(o['view']),np.array(v['K']));err=np.linalg.norm(uv[0]-o['uv'])/3.;parts['SIFT']+=o['weight']*(.5*err*err if err<=1 else err-.5)
  for v in self.fit:
   if self.one is not None and v['id']!=self.one:continue
   parts['pose_prior']+=.5*np.sum(self.local[v['id']]**2)*.01/6/len(self.fit)
  for video,h in self.H.items():parts['pose_prior']+=.5*np.sum(h*h)*.01/6
  if self.arm=='B3':
   for k,x in self.X.items():parts['landmark_prior']+=.5*np.sum((x-self.X0[k])**2)*.001/max(1,len(self.X))
   for video in self.H:
    ff=[v for v in self.fit if v['video']==video]
    for a,b in zip(ff[:-1],ff[1:]):parts['relative_motion_prior']+=.5*np.sum((self.local[b['id']]-self.local[a['id']])**2)*.01/6/max(1,len(ff)-1)
  return float(sum(parts.values())),parts
 def physical(self):
  for v in self.views:
   C=self.C(v['id']);B=np.array(v['T']);ds=np.linalg.norm(C[:3,3]-B[:3,3]);rr=np.degrees(Rotation.from_matrix(C[:3,:3]@B[:3,:3].T).magnitude());cr=curves(C,np.array(v['K']));X=cr['X'].reshape(-1,3);vis=torus_polynomial(C[:3,3],X);_,z=projection(X,C,np.array(v['K']))
   if ds>self.p['camera_center_bound_mm']or rr>self.p['rotation_bound_deg']or z.min()<=0 or (vis['states']!=0).any():return False,dict(reason='CAMERA_OR_TORUS_DOMAIN',view=v['id'],center_mm=float(ds),rotation_deg=float(rr),minimum_depth_mm=float(z.min()),nonvisible_curve_N=int((vis['states']!=0).sum()))
  if max(np.linalg.norm(x-self.X0[k])for k,x in self.X.items())>self.p['point_displacement_bound_mm']:return False,dict(reason='LANDMARK_3MM_BOUND')
  return True,{}
 def build(self):
  prob=ce.Problem();keep=[];losses=[];ms=[]
  def add(c,params,loss=None):keep.append(c);losses.append(loss);prob.add_residual_block(c,loss,params)
  if self.arm!='B1':
   for v in self.fit:
    cid=v['id'];cp=correspondence(self.C(cid),np.array(v['K']),self.ringobs[cid],self.p['torus_samples']);add(RingCost(self.caches[cid],v['K'],cp,self.weights[cid]),[self.local[cid],self.H[v['video']]])
  os=[o for o in self.obs if(self.arm!='B2'or o['cross'])and(self.one is None or o['view']==self.one)]
  for o in os:
   cid=o['view'];v=self.vd[cid];w=o['weight'];add(Reprojection(self.caches[cid],v['K'],o['uv'],w),[self.local[cid],self.H[v['video']],self.X[o['track_id']]],ce.HuberLoss(np.sqrt(w)))
  for v in self.fit:
   cid=v['id']
   if self.one is not None and cid!=self.one:continue
   if not prob.has_parameter_block(self.local[cid]):continue
   add(Prior(np.zeros(6),np.ones(6)*np.sqrt(.01/6/len(self.fit))),[self.local[cid]])
   if self.arm=='B2'or cid==self.anchors[v['video']]or self.nobs[cid]<6:prob.set_parameter_block_constant(self.local[cid])
   elif self.arm=='B3':m=ce.SubsetManifold(6,[5]);ms.append(m);prob.set_manifold(self.local[cid],m)
   for j in range(6):prob.set_parameter_lower_bound(self.local[cid],j,-1.);prob.set_parameter_upper_bound(self.local[cid],j,1.)
  for video,h in self.H.items():
   if not prob.has_parameter_block(h):continue
   add(Prior(np.zeros(6),np.ones(6)*np.sqrt(.01/6)),[h])
   if video=='004'or self.arm=='B1':prob.set_parameter_block_constant(h)
   for j in range(6):prob.set_parameter_lower_bound(h,j,-1.);prob.set_parameter_upper_bound(h,j,1.)
  for k,x in self.X.items():
   if not prob.has_parameter_block(x):continue
   if self.arm=='B3':add(Prior(self.X0[k],np.ones(3)*np.sqrt(.001/max(1,len(self.X)))),[x])
   else:prob.set_parameter_block_constant(x)
  if self.arm=='B3':
   for video in self.H:
    ff=[v for v in self.fit if v['video']==video]
    for a,b in zip(ff[:-1],ff[1:]):add(RelativePrior(np.ones(6)*np.sqrt(.01/6/max(1,len(ff)-1))),[self.local[a['id']],self.local[b['id']]])
  self.keep=keep;self.losses=losses;self.ms=ms;return prob
 def state(self):return dict(local={k:v.copy()for k,v in self.local.items()},H_delta={k:v.copy()for k,v in self.H.items()},X={k:v.copy()for k,v in self.X.items()})
 def restore(self,s):
  for k,v in s['local'].items():self.local[k][:]=v
  for k,v in s['H_delta'].items():self.H[k][:]=v
  for k,v in s['X'].items():self.X[int(k)][:]=v
 def serialize(self,status='FROZEN_NUMERIC_JOINT'):
  loss,parts=self.actual();return dict(group=self.group,arm=self.arm,status=status,poses={cid:self.C(cid)for cid in self.vd},**self.state(),H_absolute={k:exp(v)@self.H0[k]for k,v in self.H.items()},loss=loss,parts=parts,physical=self.physical(),SIFT_tracks_N=len(self.tracks),SIFT_observations_N=len(self.obs),HERO_body_GT_in_loss=False,depth_status='POSE_CHANGED_DEPTH_NOT_REINFERRED',solver='Ceres2.2LM_DENSE_SCHUR'if self.arm=='B3'else'Ceres2.2LM_DENSE_QR',scale=1.,world='native004Ringmillimeters',source=asset(Path(__file__)))
 def run(self,label):
  out=N/'results'/label/'FINAL.json'
  if out.exists():return load(out)
  trace=[];start=time.time();initial=self.actual()[0]
  for outer in range(self.p['outer_iterations']):
   before,parts=self.actual();old=self.state();prob=self.build();d=solver(prob,label+'/OUTER_'+str(outer),self.p['inner_iterations'],self.arm=='B3');new=self.state();accepted=False;trials=[]
   for j in range(self.p['backtracks']):
    a=.5**j;trial={k:{key:np.array(old[k][key])+a*(np.array(new[k][key])-old[k][key])for key in old[k]}for k in old};self.restore(trial);valid,why=self.physical();cost,pp=self.actual()if valid else(None,None);ok=valid and cost<=before+1e-10;trials.append(dict(alpha=a,physical=valid,reason=why,true_cost=cost,accepted=ok))
    if ok:accepted=True;break
   if not accepted:self.restore(old)
   trace.append(dict(outer=outer,before=before,after=self.actual()[0],accepted=accepted,Ceres=d,trials=trials));save('optimization/'+label+'/TRACE.json',trace);print('JOINT_OUTER',label,outer,accepted,before,self.actual()[0],flush=True)
   if not accepted:break
  result=self.serialize();result.update(initial_loss=initial,seconds=time.time()-start,accepted_outer=sum(r['accepted']for r in trace),outer_iterations=len(trace));save('results/'+label+'/FINAL.json',result);freeze('results/'+label+'/FROZEN.json',[out],before_HERO_body_HOLDOUT=True);return result

def main(group):
 fit_guard();checkfreeze('provenance/INPUTS_FROZEN.json');assert load(N/'STAGE_A_GATE.json')['PASS'];freeze('provenance/'+group+'_CODE_BEFORE_OPTIMIZATION.json',list((N/'code').glob('*.py'))+[N/'config/PROTOCOL.json'],HERO=False,body=False,GT=False)
 base=Joint(group,'B3');r=base.serialize('FROZEN_RING_FIRST_BASELINE');r['arm']='B0';save('results/'+group+'/B0/FINAL.json',r)
 # IndependentB1 is deliberately not calledjointBA. Everycamera hasfixedXYZ.
 merged={cid:np.array(v['T'])for cid,v in base.vd.items()};summ=[]
 for v in base.fit:
  obj=Joint(group,'B1',one=v['id']);cid=v['id']
  if cid==obj.anchors[v['video']]:summ.append(dict(id=cid,status='ANCHOR_FIXED',pose=merged[cid]));continue
  rr=obj.run(group+'/B1_LOCAL/'+cid);merged[cid]=np.array(rr['poses'][cid]);summ.append(dict(id=cid,status=rr['status'],initial_loss=rr['initial_loss'],final_loss=rr['loss'],seconds=rr['seconds']))
 save('results/'+group+'/B1/FINAL.json',dict(group=group,arm='B1',poses=merged,status='INDEPENDENT_LOCAL_NOT_JOINT_BA',per_view=summ,H_absolute=r['H_absolute'],scale=1.,depth_status='POSE_CHANGED_DEPTH_NOT_REINFERRED'))
 if group=='G01':b2=Joint(group,'B2').run(group+'/B2')
 else:b2=None;save('results/'+group+'/B2/FINAL.json',dict(group=group,arm='B2',status='NOT_APPLICABLE_NO_VERIFIED_CROSS_VIDEO',poses=None))
 obj=Joint(group,'B3',initial=b2);obj.run(group+'/B3');save('results/'+group+'/B4/FINAL.json',dict(group=group,arm='B4',status='PENDING_B3_INDEPENDENT_GEOMETRY_GATE',poses=None))
 freeze('provenance/'+group+'_MAIN_POSES_FROZEN.json',[N/'results'/group/m/'FINAL.json'for m in METHODS],HERO_GT_body_HOLDOUT_used=False);print('GROUP_MAIN_BA_FROZEN',group,flush=True)
if __name__=='__main__':main(sys.argv[1])
