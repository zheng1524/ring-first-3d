"""Compose original 019, native RF/PnP, MAX qualification and support kernels.

No historical solved artifact is allowed. Original FEATURE_HELD is diagnostic:
it excludes PnP updates but not upstream map/seed construction.
"""
import ast,os,sys,time,types,json,hashlib,traceback,itertools
from pathlib import Path
import numpy as np,cv2
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from historical_io import H,W,E,sha,load,firewall,adapt_constants
MAX=H/'TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code'
CORE=Path('/home/liu/ring-first-hero-core/src')
sys.path.insert(0,str(CORE))
from ring_first_hero import camera,rgb,_kernels
from ring_first_hero.geometry import project

def extract(file,names,ns,major=5.6):
 tree=ast.parse(file.read_text());body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 assert set(n.name for n in body)==set(names),(file,names)
 for fn in body:
  if fn.name=='observe':
   for node in ast.walk(fn):
    if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='recover':node.args[2]=ast.copy_location(ast.Constant(2*(major-.6)),node.args[2])
 exec(compile(adapt_constants(ast.Module(body=body,type_ignores=[]),major),str(file),'exec'),ns)
 return ns

def run(R,cfg):
 os.environ['E4_RUN_DIR']=str(R)
 c=load('common019',R,alias='common');f=load('features019',R)
 seed=np.load(R/'predictions/C_F980_0.npz');K=seed['K'];P=seed['c2w'];views=[]
 for i,C in enumerate(P):
  image=cv2.imread(str(R/f'inputs/images/{i:03d}.jpg'));lab=cv2.imread(str(R/f'inputs/masks/{i:03d}.png'),0)
  image=cv2.cvtColor(cv2.resize(image,(640,360),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2RGB);lab=cv2.resize(lab,(640,360),interpolation=cv2.INTER_NEAREST)
  cache=R/f'inputs/view_{i:03d}.npz';np.savez_compressed(cache,RGB=image,labels=lab,T=C,K=K)
  views.append(dict(id=f'view_{i:03d}',index=i,raw_frame=cfg['raw_frames'][i],video=cfg['video_id'],group=cfg['group'],role='FIT',cache=str(cache),T=C.tolist(),K=K.tolist(),RGB_SHA256=hashlib.sha256(image.tobytes()).hexdigest(),capture_type='VIDEO'))
 c.save('config/VIEWS.json',views)
 # Freeze evaluation scope before map fitting. No assertion of common independence.
 tr=np.load(R/'observations/tracks.npz');held=np.flatnonzero(~tr['train_track']&tr['holdout_eligible'])
 c.save('config/EVALUATION_SCOPE_FROZEN.json',dict(seed_holdout_track_ids=held,seed_track_sha256=sha(R/'observations/tracks.npz'),seed_holdout='pre-existing whole-track split; excluded from seed E/PnP/BA',native_feature_held='landmark index modulo 5; excluded only from native PnP, not upstream map; diagnostic',common_independent_RGB='NOT_EVALUABLE: V6 fitting exclusion not certified',native_independent_RGB='NOT_EVALUABLE: LK and SIFT feature identities not proven disjoint',frozen_before_landmarks=True))
 f.VIEWS={v['id']:v for v in views if np.isfinite(v['T']).all()};records=[];short=[]
 code=Path(f.__file__).read_text().splitlines();validline=next(i+1 for i,s in enumerate(code) if 'if not valid:continue' in s)
 trackline=next(i+1 for i,s in enumerate(code) if 'for tid,tr in enumerate(tracks)' in s)
 nonfiniteline=next(i+1 for i,s in enumerate(code) if 'if not np.isfinite(X).all():continue' in s)
 def trace(frame,event,arg):
  if frame.f_code.co_name!='landmarks' or event!='line':return trace
  d=frame.f_locals
  if frame.f_lineno==nonfiniteline and not np.isfinite(d['X']).all():
   records.append(dict(track=int(d['tid']),sources=[dict(view=s,feature_id=int(j),raw_frame=f.VIEWS[s]['raw_frame'])for s,j in d['tr']],track_length=len(d['tr']),qualified=False,rejection=['NONFINITE_INITIAL_TRIANGULATION'],category='not_evaluable'))
  if frame.f_lineno==trackline and not short:
   short.extend(dict(observations=sorted(d['members'][k]),reason='TRACK_LENGTH_LT_3') for k in d['parent'] if d['parent'][k]==k and len(d['members'][k])<3)
  if frame.f_lineno==validline:
   track=d['tr'];regions=[int(f.features(f.VIEWS[s])['region'][j])for s,j in track];z=d['z'];err=d['err'];X=d['X'];par=d['par']
   records.append(dict(track=int(d['tid']),sources=[dict(view=s,feature_id=int(j),uv=f.features(f.VIEWS[s])['xy'][j],raw_frame=f.VIEWS[s]['raw_frame'],camera=f.VIEWS[s]['T'])for s,j in track],triangulation_anchor_views=[track[d['i']][0],track[d['j']][0]],track_length=len(track),positive_depth_fraction=float((z>0).mean()),min_depth_mm=float(z.min()),reprojection_px=err,parallax_deg=float(par),X_mm=X,qualified=bool(d['valid']),rejection=[r for bad,r in [(not(z>0).all(),'NONPOSITIVE_DEPTH'),(err.max()>=2,'REPROJECTION_GE_2'),(par<=.5,'PARALLAX_LE_0.5'),(np.linalg.norm(X)>=300,'RADIUS_GE_300')]if bad],category='background'if all(x==0 for x in regions)else'polyp'if all(x==1 for x in regions)else'mixed'))
  return trace
 sys.settrace(trace)
 try:lm=f.landmarks(list(f.VIEWS),'INDEPENDENT_VIDEO')
 finally:sys.settrace(None)
 c.save('landmarks/BUILD_AUDIT.json',dict(tracks=records,short_tracks=short,views=views,reference_ids=list(f.VIEWS),query_ids=[v['id']for v in views],points=len(lm['X']),raw_independent=True,association='original mutual SIFT .72 / MAGSAC / known-pose epipolar / camera-disjoint union-find',spatial_bounds_mm=[lm['X'].min(0),lm['X'].max(0)]if len(lm['X'])else None))
 print('LANDMARKS',len(lm['X']),flush=True)
 # R5 changes only the physical major radius; no per-case solver/gate changes.
 cam=camera
 if cfg['R_mm']!=5.6:
  cam=types.ModuleType('ring_first_hero.camera_r5');cam.__package__='ring_first_hero'
  source=Path(camera.__file__);exec(compile(adapt_constants(ast.parse(source.read_text()),cfg['R_mm']),str(source),'exec'),cam.__dict__)
 import torch
 ns=dict(np=np,cv2=cv2,torch=torch,D=torch.float64,Rotation=Rotation,S=np.r_[np.full(3,.6),np.full(3,np.deg2rad(5))],N=R,K0=K,Path=Path,cKDTree=cKDTree,load=lambda p:json.loads(Path(p).read_text()),save=c.save,projection=project,stats=c.stats,types=types,sys=sys,hashlib=hashlib,importlib=__import__('importlib'),DXY=Path('/home/liu/new-polyp-dxy'))
 ns['torus_original']=lambda center,rot,K,n=1024:camera.bind(_kernels.torus_contours,{'np':np})(center,rot,K,R=cfg['R_mm'],r=.6,n=n)
 extract(MAX/'torus.py',['tt','skew','exp_t','exp','curves','nearest','project_dC'],ns,cfg['R_mm'])
 tm=types.ModuleType('torus');tm.__dict__.update(ns);sys.modules['torus']=tm
 extract(MAX/'context.py',['unit','angle'],ns)
 extract(MAX/'rgb.py',['features','mutual','errors'],ns);ns['BF']=cv2.BFMatcher(cv2.NORM_L2)
 # Keep native query features in a separate namespace from 019 masked features.
 native=R/'native';native.mkdir(exist_ok=True);(native/'features').mkdir(exist_ok=True)
 oldfeatures=ns['features'];feature_ns=dict(ns,N=native);ns['features']=types.FunctionType(oldfeatures.__code__,feature_ns)
 (R/'ring_evidence').mkdir(exist_ok=True)
 extract(MAX/'cameras.py',['edge','sample','observe','physical'],ns,cfg['R_mm'])
 extract(MAX/'register.py',['qualification'],ns)
 extract(MAX/'coverage.py',['support_pairs','direction_stats'],ns)
 out=[]
 for v in views:
  start=time.time();a=np.load(v['cache'])
  try:
   rr=rgb.pnp(a['RGB'],a['labels'],K,lm);rr['map_ancestry']='THIS RUN independent per-video RAW seed and 019 triangulation'
   c.save('inputs/'+v['id']+'/RGB_GEOMETRY.json',rr)
   r=cam.recover(a['labels'],K,rr,initial_pose=None);C=r['c2w_mm'];c.save('registration/'+v['id']+'/RECOVER.json',r)
   q=ns['qualification'](v,C);q['independent_validation']='DIAGNOSTIC map-held only; upstream observations reused'
   out.append(v|dict(C=C,**q,candidate_source=r['candidate_source'],numeric_status=r['status'],seconds=time.time()-start))
   print('CAMERA',v['id'],q['formal'],q.get('qualification_reasons'),flush=True)
  except Exception as e:
   out.append(v|dict(C=None,formal=False,HERO_target_eligible=False,status='RECOVERY_FAILED',error=repr(e),traceback=traceback.format_exc(),seconds=time.time()-start));print('CAMERA_FAILED',v['id'],repr(e),flush=True)
 c.save('registration/CAMERAS.json',out)
 usable=[v for v in out if v['formal']];supports=[];plans=[]
 # Execute original support-selection loop verbatim, only over our fixed target pool.
 tree=ast.parse((MAX/'coverage.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
 loop=next(n for n in main.body if isinstance(n,ast.For)and isinstance(n.iter,ast.Name)and n.iter.id=='selected')
 loop.body=[n for n in loop.body if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='print')]
 local=dict(ns,g=cfg['group'],vs=usable,selected=usable,supports=supports,plans=plans,rows=[dict(id=v['id'],rank=i+1)for i,v in enumerate(usable)])
 exec(compile(ast.Module(body=[loop],type_ignores=[]),str(MAX/'coverage.py'),'exec'),local)
 c.save('selection/SUPPORTS.json',supports);c.save('selection/HERO_PLAN.json',plans[:cfg['HERO_budget_per_video']])
 c.save('metrics/RECOVERY_SUMMARY.json',dict(requested=16,numeric=sum(v['C']is not None for v in out),qualified=len(usable),legal_targets=len(plans),legal_support_links=sum(x['support_N']for x in supports),landmarks=len(lm['X']),directions=ns['direction_stats'](usable),HERO_budget=cfg['HERO_budget_per_video'],HERO_selected=len(plans[:cfg['HERO_budget_per_video']]),source='original RF/PnP + original MAX qualification and support; no later cross-video Ceres/Body selection'))
 print('RECOVERY_COMPLETE',len(out),len(usable),len(plans),flush=True)

def main():
 R=W/'runs/m2f12_historical004/H004_RAW_BASELINE'/sys.argv[1];cfg=json.loads((R/'config.json').read_text());sys.dont_write_bytecode=True
 os.environ['MPLCONFIGDIR']=str(R/'runtime/mpl');events=firewall(R,[cfg['video']],[str(W/'runtime/extra_packages')]);start=time.time();result=dict(stage='recover',status='STARTED')
 try:run(R,cfg);result['status']='COMPLETED'
 except Exception as ex:result.update(status='FAILED',error=repr(ex),traceback=traceback.format_exc());print(result['traceback'],flush=True)
 result.update(seconds=time.time()-start,consumers=events,code={str(p):sha(p)for p in [Path(__file__),Path(camera.__file__),Path(rgb.__file__),*MAX.glob('*.py')]})
 (R/'STAGE_recover.json').write_text(json.dumps(result,indent=2))
 if result['status']!='COMPLETED':raise SystemExit(1)
if __name__=='__main__':main()
