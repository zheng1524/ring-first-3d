"""Separate generator/predictor/evaluator stages for 001 regression and V3 Ring noise."""
from common2 import *
from scipy.spatial.transform import Rotation
from ring_first_3d.sim.geometry import transform,scene,closest,pose_error
from solver2 import solve_methods,ring_residual
from real2 import triangulate
from metrics2 import bidirectional,summarize
BASE_CONDS=['V0','V1']+['V2_'+str(s)for s in CFG['seeds']]
CONDS=BASE_CONDS+['V3_'+str(s)for s in CFG['seeds']]

def prepare():
 out=RUN/'control';stage_freeze('GENERATE',out,[VRUN/'GENERATION_FREEZE.json']);(out/'public').mkdir(exist_ok=False);frames=read(VRUN/'tracks/ADAPTER.json')['frames'];frames=[dict(f,side='A'if f['video']=='004'else'B')for f in frames];save(out/'public/FRAMES.json',frames);tr=dict(np.load(VRUN/'tracks/observations/tracks005.npz'));np.savez_compressed(out/'public/TRACKS.npz',**tr);private={}
 for condition in CONDS:
  base=condition.replace('V3_','V2_');data=read(VRUN/'public/conditions'/(base+'.json'));ring=data['ring']['005'];c=np.array(ring['center']);n=np.array(ring['normal']);cov=np.zeros((5,5));status='EXACT'
  if condition.startswith('V3'):
   rng=np.random.default_rng(int(condition.split('_')[1])+CFG['v3_seed_offset']);dc=rng.normal(0,.1,3);dr=rng.normal(0,np.deg2rad(.3),3);private[condition]=dict(center_noise=dc,rotvec_noise=dr);c=c+dc;n=Rotation.from_rotvec(dr).apply(n);cov=np.diag([.1**2]*3+[np.deg2rad(.3)**2]*2);status='ESTIMATED'
  poses={f['id']:np.array(f['C'])for f in data['frames']};C=np.array([poses[f['id']]for f in frames]);xyz,_,details=triangulate(frames,C,tr);old=np.load(VRUN/'predictions'/base/'LANDMARKS.npz');fit=np.zeros(len(xyz),bool);fit[old['track_ids'][~old['held']]]=True
  np.testing.assert_allclose(xyz[old['track_ids']],old['points'],atol=1e-7);np.savez_compressed(out/'public'/(condition+'.npz'),xyz=xyz,fit=fit,c2w=C);save(out/'public'/(condition+'.json'),dict(condition=condition,source_condition=base,all_cameras=data['frames'],ring=dict(center=c,normal=n,covariance=cov,status=status,radius_mm=5.6),ideal_depth='CONTROLLED_MEASUREMENT_SYNTHETIC_HERO_PROXY'))
 save(out/'private/V3_INJECTION.json',private);save(out/'INPUT_FREEZE.json',[dict(path=str(p),sha256=sha(p))for p in (out/'public').glob('*')]);print('CONTROL INPUTS',len(CONDS),flush=True)

def guard():
 import sys
 def hook(event,args):
  if event=='open'and isinstance(args[0],(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(args[0])).resolve()
   if 'private'in p.parts or p.name=='virtual_GT.npz' or (VRUN/'public/conditions')in p.parents:raise PermissionError('CONTROL_GT_OR_INJECTION_DENIED '+str(p))
 sys.addaudithook(hook)

def predict():
 guard();out=RUN/'control';verify(read(out/'INPUT_FREEZE.json'))
 for c in CONDS:
  resource();folder=out/'predictions'/c;stage_freeze('PREDICT',folder,[out/'INPUT_FREEZE.json']);a=np.load(out/'public'/(c+'.npz'));r=read(out/'public'/(c+'.json'))['ring'];fit=a['fit'];results=solve_methods(a['xyz'][fit,0],a['xyz'][fit,1],r);save(folder/'PREDICTIONS.json',results);save(folder/'FREEZE.json',dict(prediction_sha256=sha(folder/'PREDICTIONS.json'),input_freeze_sha256=sha(out/'INPUT_FREEZE.json')));print('CONTROL',c,{k:v['quality']for k,v in results.items()},flush=True)

def evaluate():
 out=RUN/'control';verify(read(out/'INPUT_FREEZE.json'));frames=read(out/'public/FRAMES.json');tr=np.load(out/'public/TRACKS.npz');gt=np.load(VRUN/'private/GT_TARGETS.npz');truth=read(VRUN/'private/TRUTH.json');allframes=read(VRUN/'public/FRAMES.json');P=gt['P'];domain=gt['visible004']|gt['visible005'];overlap=gt['visible004']&gt['visible005'];results=[]
 for condition in CONDS:
  resource();folder=out/'predictions'/condition;assert sha(folder/'PREDICTIONS.json')==read(folder/'FREEZE.json')['prediction_sha256'];a=np.load(out/'public'/(condition+'.npz'));public=read(out/'public'/(condition+'.json'));base=public['source_condition'];data=read(folder/'PREDICTIONS.json');first=next(f['id']for f in allframes if f['video']=='005');D=np.array(truth['injections'][base][first]['D']);data['EVAL_TRUE_D_INVERSE']=dict(T=np.linalg.inv(D),quality='EVALUATION_ONLY_NOT_LOWER_BOUND',numerical='REFERENCE');poses={r['id']:np.array(r['C'])for r in public['all_cameras']}
  for method,rec in data.items():
   t=np.array(rec['T']);bidi,detail=bidirectional(frames,a['c2w'],tr,a['xyz'],t);error=pose_error(t@D);ring=public['ring'];drift=ring_residual(t,np.array(ring['center']),np.array(ring['normal']));Qs={}
   for video in ['004','005']:
    vertices=[];faces=[];offset=0
    for f in allframes:
     if f['role']!='FIT'or f['video']!=video:continue
     mesh=np.load(VRUN/'public/meshes'/(f['id']+'.npz'));C=poses[f['id']];C=t@C if video=='005'else C;V=transform(mesh['V'],C);vertices.append(V);faces.append(mesh['F']+offset);offset+=len(V)
    V=np.concatenate(vertices);F=np.concatenate(faces);Q,_,_=closest(scene(V,F),P);Qs[video]=Q
   distances=np.minimum(np.linalg.norm(Qs['004']-P,axis=1),np.linalg.norm(Qs['005']-P,axis=1));hold=[]
   for f in allframes:
    if f['role']=='FIT'or f['video']!='005':continue
    X=P[gt[f['id']]];Ctrue=np.array(truth['frames'][f['id']]['C']);C=t@poses[f['id']];K=np.array(f['K']);c1=(X-Ctrue[:3,3])@Ctrue[:3,:3];c2=(X-C[:3,3])@C[:3,:3];q1=c1@K.T;q2=c2@K.T;err=np.linalg.norm(q1[:,:2]/q1[:,2:]-q2[:,:2]/q2[:,2:],axis=1);err[c2[:,2]<=0]=np.inf;hold.extend(err)
   r=dict(condition=condition,method=method,**error,pose_pass=error['rotation_deg']<=.5 and error['translation_mm']<=.2,observed_ring_center_drift_mm=float(np.linalg.norm(drift[:3])),observed_normal_drift_deg=float(np.rad2deg(np.linalg.norm(drift[3:]))),physical_ring_center_error_mm=float(np.linalg.norm((t@D)[:3,3])),physical_normal_error_deg=float(np.rad2deg(np.arccos(np.clip((t@D)[2,2],-1,1)))),surface_median_mm=float(np.median(distances[domain])),surface_p95_mm=float(np.quantile(distances[domain],.95)),coverage=float((distances[domain]<=.2).mean()),surface_N=int(domain.sum()),overlap_p95_mm=float(np.quantile(np.linalg.norm(Qs['004'][overlap]-Qs['005'][overlap],axis=1),.95)),bidir=bidi,held005=summarize(hold),numerical=rec['numerical'],quality=rec['quality']);results.append(r)
  save(T/'evidence/CONTROL_RESULTS.json',results);print('EVALUATED',condition,flush=True)
 # D-inverse only cancels coordinate D, not frame errors. V2/V3 must coincide.
 for seed in CFG['seeds']:
  a=next(r for r in results if r['condition']=='V2_'+str(seed)and r['method']=='EVAL_TRUE_D_INVERSE');b=next(r for r in results if r['condition']=='V3_'+str(seed)and r['method']=='EVAL_TRUE_D_INVERSE');assert a['surface_p95_mm']==b['surface_p95_mm']and a['held005']==b['held005']and a['bidir']==b['bidir']
if __name__=='__main__':
 import sys
 {'prepare':prepare,'predict':predict,'evaluate':evaluate}[sys.argv[1]]()
