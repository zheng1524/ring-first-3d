"""H004_DIAGNOSTIC: rebuild from historical cameras; never a RAW claim."""
import os,sys,json,hashlib,time
from pathlib import Path
from historical_io import E,H,W,load,common,sha
import numpy as np,cv2
R=W/'runs/m2f12_historical004/H004_DIAGNOSTIC/rebuild019';R.mkdir(parents=True,exist_ok=True)
os.environ['E4_RUN_DIR']=str(R);sys.dont_write_bytecode=True
c=load('common019',R,alias='common');f=load('features019',R)
old=H/'TASK-E4-RING-POLYP-REGISTRATION-019';views=json.loads((old/'config/VIEWS.json').read_text());vv=[]
for v in views:
 if v['video']!='004' or v['role']!='FIT':continue
 v=dict(v);p=Path(v['cache']);candidates=[p,W/'assets/retained_sources'/str(p).removeprefix('/home/liu/'),old/'inputs/G01'/(v['id']+'.npz'),W/'assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-HERO-BODY-ADAPT-018/inputs/G01'/(v['id']+'.npz')]
 q=next((x for x in candidates if x.is_file()),None)
 if q is None:raise FileNotFoundError(candidates)
 a=np.load(q);assert np.allclose(a['T'],v['T']) and np.allclose(a['K'],v['K'])
 for key,field in [('RGB','RGB_content_sha'),('labels','Mask_content_sha')]:
  if field in v:assert hashlib.sha256(a[key].tobytes()).hexdigest()==v[field],v['id']+':'+field
  v[field+'_observed']=hashlib.sha256(a[key].tobytes()).hexdigest()
 v['cache']=str(q);v['cache_sha256']=sha(q);vv.append(v)
f.VIEWS={v['id']:v for v in vv};records=[]
def trace(frame,event,arg):
 if frame.f_code.co_name=='landmarks' and event=='line' and frame.f_lineno==53:
  d=frame.f_locals;tr=d['tr'];regions=[int(f.features(f.VIEWS[s])['region'][j])for s,j in tr];z=d['z'];err=d['err'];X=d['X'];par=d['par']
  records.append(dict(track=int(d['tid']),sources=[dict(view=s,feature_id=int(j),uv=f.features(f.VIEWS[s])['xy'][j].tolist(),camera=f.VIEWS[s]['T'],cache=f.VIEWS[s]['cache'],raw_frame=f.VIEWS[s].get('raw_frame'))for s,j in tr],track_length=len(tr),positive_depth_fraction=float((z>0).mean()),min_depth_mm=float(z.min()),reprojection_px=err.tolist(),parallax_deg=float(par),X_mm=X.tolist(),qualified=bool(d['valid']),rejection=[reason for bad,reason in [(not(z>0).all(),'NONPOSITIVE_DEPTH'),(err.max()>=2,'REPROJECTION_GE_2'),(par<=.5,'PARALLAX_LE_0.5'),(np.linalg.norm(X)>=300,'RADIUS_GE_300')]if bad],category='background'if all(x==0 for x in regions)else'polyp'if all(x==1 for x in regions)else'mixed'))
 return trace
sys.settrace(trace);start=time.time();lm=f.landmarks(list(f.VIEWS),'G01_004_REBUILT');sys.settrace(None)
original=np.load(old/'landmarks/CROSS_004.npz');same_shape=lm['X'].shape==original['X'].shape
out=dict(status='HISTORICAL_CAMERA_CONDITIONED_REBUILD',sources=vv,seconds=time.time()-start,tracks=records,points=len(lm['X']),original_points=len(original['X']),same_shape=same_shape,X_max_abs=float(abs(lm['X']-original['X']).max())if same_shape else None,descriptor_equal=bool(np.array_equal(lm['des'],original['des'])),original_map_sha256=sha(old/'landmarks/CROSS_004.npz'),raw_independent=False)
c.save('REBUILD_AUDIT.json',out);print('DIAGNOSTIC_REBUILD',len(vv),len(lm['X']),out['X_max_abs'],out['descriptor_equal'],flush=True)
# Check V4->V5 native observation identity on an original native image/label pair.
Q=W/'runs/m2f12_historical004/H004_DIAGNOSTIC/observation_contract';Q.mkdir(parents=True,exist_ok=True)
common(Q);adapter=load('adapter',Q);oldinput=E/'ring_first_v2_real_ba/runs/continuous16';im=cv2.imread(str(oldinput/'inputs/images/008.jpg'));lab=cv2.imread(str(oldinput/'inputs/masks/008.png'),0)
ob,status=adapter.adapt(im,lab,'real-8');orig=np.load(E/'ring_first_v5_real_validation/observations/native_008.npz')
checks={k:dict(shape_equal=ob[k].shape==orig[k].shape,array_equal=bool(np.array_equal(ob[k],orig[k])))for k in ob if k in orig}
(Q/'CHECK.json').write_text(json.dumps(dict(checks=checks,all_equal=all(x['array_equal']for x in checks.values()),old_keys=orig.files,new_keys=list(ob)),indent=2));print('V4_NATIVE_CONTRACT',all(x['array_equal']for x in checks.values()),len(checks),flush=True)
