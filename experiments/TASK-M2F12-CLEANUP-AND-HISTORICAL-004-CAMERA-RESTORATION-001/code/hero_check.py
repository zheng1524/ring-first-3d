"""Frozen equal-budget official HERO diagnostic, evaluated after prediction.
V6 is read only; its solved inputs are used solely in the named V6 diagnostic.
"""
import os,sys,json,time,hashlib,ast,types,traceback
from pathlib import Path
import numpy as np,cv2
from historical_io import W,sha
HERE=Path(__file__).resolve().parent;T=HERE.parent;BASE=W/'runs/m2f12_historical004';CORE=Path('/home/liu/ring-first-hero-core')
sys.path.insert(0,str(CORE/'src'))
from ring_first_hero.io import save_json
from ring_first_hero.geometry import native_rgb_labels
REPRO=W/'src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py'
def read(p):return json.loads(Path(p).read_text())
def inference_state(output):
 if(output/'INFERENCE.json').exists()and(output/'HERO_native.npz').exists():return'REUSE'
 if any((output/name).exists()for name in ['INFERENCE_STARTED.json','INFERENCE.json','HERO_native.npz']):return'SPENT'
 return'NEW'
def freeze():
 protocol=T/'evidence/HERO_PROTOCOL.json'
 assert protocol.exists(),'Budget must predate inference'
 assert(BASE/'BASELINE_FROZEN.json').exists(),'Finish and freeze all ten baseline cases first'
 frozen=BASE/'HERO_PLANS_FROZEN.json'
 if frozen.exists():
  old=read(frozen);assert old['protocol_sha256']==sha(protocol),'Frozen budget changed';return old['plans']
 plans=[]
 for row in read(T/'evidence/INPUT_REGISTRY.json'):
  case=row['case'];R=BASE/'H004_RAW_BASELINE'/case;p=R/'selection/HERO_PLAN.json'
  hp=read(p)if p.exists()else[]
  plans.append(dict(case=case,route='H004_RAW_BASELINE',status='READY'if hp else'NO_LEGAL_TARGET',plan=hp[0]if hp else None,source_plan=str(p),source_plan_sha256=sha(p)if p.exists()else None,ring_inner_mm=row['ring_inner_mm']))
  # Final V6 attempt is fixed by M2F10, not selected by HERO quality.
  state=row['V6_states'][-1];V=Path(state['path']).parent;L=read(V/'inputs/ledger005.json');cs=read(V/'inputs/MVS_supported_cases.json');cs=[c for c in cs if len(c['sources'])==3]
  cs=sorted(enumerate(cs),key=lambda z:(L[z[1]['reference']]['raw_frame'],z[0]));c=cs[0][1]if cs else None
  val=read(V/'metrics/local_validation.json');vr=next(x for x in val['versions']if x['version']==val['primary'])['per_frame']
  plans.append(dict(case=case,route='V6_LIMITED_DIAGNOSTIC',status='READY'if c else'NO_LEGAL_SUPPORT_TUPLE',plan=c,v6_root=str(V),RUN_STATE=state,source_plan=str(V/'inputs/MVS_supported_cases.json'),source_plan_sha256=sha(V/'inputs/MVS_supported_cases.json'),ring_inner_mm=row['ring_inner_mm'],target_own_validated=vr[c['reference']]['status']=='VALIDATED'if c else None,support_own_validated=[vr[i]['status']=='VALIDATED'for i in c['sources']]if c else[]))
 save_json(BASE/'HERO_PLANS_FROZEN.json',dict(protocol=read(protocol),protocol_sha256=sha(protocol),baseline_freeze_sha256=sha(BASE/'BASELINE_FROZEN.json'),epoch=time.time(),plans=plans,source_code_sha256=sha(__file__)))
 return plans
def frames(row):
 p=row['plan'];out=[]
 if row['route']=='H004_RAW_BASELINE':
  for v in [p['target']]+p['support_views']:
   a=np.load(v['cache']);out.append(dict(RGB=a['RGB'],labels=a['labels'],K=np.array(v['K']),c2w_mm=np.array(v['C']),id=v['id'],raw_frame=v['raw_frame']))
 else:
  R=Path(row['v6_root']);L=read(R/'inputs/ledger005.json');primary=read(R/'predictions/local005_primary.json')['primary_version'];cam=np.load(R/f'predictions/local005_camera_{primary}.npz')
  for i in [p['reference']]+p['sources']:
   v=L[i];assert sha(v['RGB_path'])==v['RGB_SHA256']and sha(v['Mask_path'])==v['Mask_SHA256']
   out.append(dict(RGB=cv2.cvtColor(cv2.imread(v['RGB_path']),cv2.COLOR_BGR2RGB),labels=cv2.imread(v['Mask_path'],0),K=np.array(v['K']),c2w_mm=cam['c2w'][i],id=v['id'],raw_frame=v['raw_frame']))
 return out
def evaluate(row,fs,O):
 import open3d as o3d
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 ring=W/'runs/m2f5_unified/cad'/('R10.npz'if row['ring_inner_mm']==10 else'R5.npz');a=np.load(ring);scene=o3d.t.geometry.RaycastingScene(nthreads=2);scene.add_triangles(o3d.core.Tensor(a['V'].astype(np.float32)),o3d.core.Tensor(a['F'].astype(np.uint32)))
 ns=dict(np=np,o3d=o3d)
 source=W/'src/ring_first_3d/sim/geometry.py';node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='camera_rays');exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
 ns.update(vis=types.SimpleNamespace(camera_rays=ns['camera_rays']),cad_scene=lambda _:scene)
 tree=ast.parse(REPRO.read_text());body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ['render','evaluate','neutral']];exec(compile(ast.Module(body=body,type_ignores=[]),str(REPRO),'exec'),ns)
 z=np.load(O/'HERO_native.npz');depth=z['depth_mm'];K=z['K_index_native'];C=z['reference_pose_mm'];rgb,labels,_=native_rgb_labels(fs[0]['RGB'],fs[0]['labels'],fs[0]['K'])
 h,w=depth.shape;y,x=np.mgrid[:h,:w];rays=ns['camera_rays'](np.c_[x.ravel(),y.ravel()],K,C);cad=scene.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy().reshape(h,w)
 observed=labels==2;valid=np.isfinite(depth)&(depth>0);common=observed&valid&np.isfinite(cad)&(cad>0)
 d=abs(depth[common]-cad[common]);ratio=depth[common]/cad[common]
 rm=dict(observed_ring_pixels=int(observed.sum()),CAD_common_pixels=int(common.sum()),coverage=float(common.sum()/max(1,observed.sum())),MAE_mm=float(d.mean())if len(d)else None,p95_mm=float(np.quantile(d,.95))if len(d)else None,ratio_median=float(np.median(ratio))if len(ratio)else None,native_valid_fraction=float(valid.mean()),Ring_CAD=str(ring),Ring_CAD_sha256=sha(ring),conditional_on_camera=True)
 m=np.load(O/'RAW_NATIVE_MESH.npz');uv=m['uv'].astype(int);colors=rgb[uv[:,1],uv[:,0]]/255.;B=fs[1]
 pred=ns['render'](m['V'],m['F'],colors,B['K'],B['c2w_mm'],np.eye(4),'R10'if row['ring_inner_mm']==10 else'R5');np.savez_compressed(O/'A_TO_B_PREDICTION.npz',**pred)
 metrics,mae,common_b=ns['evaluate'](pred,B['RGB'],B['labels']);metrics.update(A=fs[0]['id'],B=B['id'],B_is_HERO_support=True,independent_holdout=False,renderer=str(REPRO),renderer_sha256=sha(REPRO))
 save_json(O/'EVALUATION.json',dict(ring=rm,a_to_b=metrics,pose_GT='NOT_EVALUABLE',paired_camera_causal_comparison=False))
 fig,axs=plt.subplots(2,3,figsize=(13,7));axs[0,0].imshow(fs[0]['RGB']);axs[0,0].set_title('A actual RAW image')
 im=axs[0,1].imshow(depth,cmap='viridis',vmin=10,vmax=70);axs[0,1].set_title('Native HERO axial Z [mm]');fig.colorbar(im,ax=axs[0,1],fraction=.04)
 heat=np.where(common,abs(depth-cad),np.nan);im=axs[0,2].imshow(heat,cmap='magma',vmin=0,vmax=5);axs[0,2].set_title('Observed Ring |HERO - CAD| [mm]');fig.colorbar(im,ax=axs[0,2],fraction=.04)
 axs[1,0].imshow(B['RGB']);axs[1,0].set_title('B actual RGB (used as HERO support)');axs[1,1].imshow(ns['neutral'](pred['RGBA']));axs[1,1].set_title('A original triangles + A RGB projected to B')
 im=axs[1,2].imshow(np.where(common_b,mae,np.nan),cmap='magma',vmin=0,vmax=80);axs[1,2].set_title('Common-region RGB MAE [0..255]');fig.colorbar(im,ax=axs[1,2],fraction=.04)
 for ax in axs.flat:ax.set_xlabel('x [pixel]');ax.set_ylabel('y [pixel]')
 fig.suptitle(row['case']+' / '+row['route']+'\nRing physical inner diameter '+str(row['ring_inner_mm'])+' mm; pose/shape GT NOT_EVALUABLE; fixed color scales',fontsize=10);fig.tight_layout();fig.savefig(O/'HERO_A_TO_B.png',dpi=100);plt.close(fig)
 return rm,metrics
def main():
 plans=freeze();rt=read(CORE/'site_config.local.json');sys.path[:0]=rt['readonly_dependency_paths'];OBASE=BASE/'HERO_LIMITED';OBASE.mkdir(exist_ok=True)
 for k in ['HF_HOME','HF_MODULES_CACHE','TORCH_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']:os.environ[k]=str(OBASE/'runtime'/k)
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1');sys.dont_write_bytecode=True
 import torch
 from ring_first_hero.hero import load_official,infer
 torch.set_num_threads(4);torch.manual_seed(20261115);model=None;results=[]
 for row in plans:
  rec={k:v for k,v in row.items()if k!='plan'};O=OBASE/row['route']/row['case'];O.mkdir(parents=True,exist_ok=True)
  if row['status']=='READY':
   try:
    assert sha(row['source_plan'])==row['source_plan_sha256'],'Frozen source plan changed'
    fs=frames(row);frozen_input=dict(plan=row,frames=[dict(id=f['id'],raw_frame=f['raw_frame'],RGB_sha256=hashlib.sha256(f['RGB'].tobytes()).hexdigest(),Mask_sha256=hashlib.sha256(f['labels'].tobytes()).hexdigest(),K=f['K'].tolist(),C=f['c2w_mm'].tolist())for f in fs])
    if(O/'INPUT_FROZEN.json').exists():assert read(O/'INPUT_FROZEN.json')==frozen_input,'Frozen input changed'
    else:save_json(O/'INPUT_FROZEN.json',frozen_input)
    state=inference_state(O)
    if state=='SPENT':raise RuntimeError('INFERENCE_BUDGET_ALREADY_SPENT_OR_INTERRUPTED: no second inference')
    if state=='NEW':
     if model is None:model,receipt=load_official(rt['mvs_root'],rt['checkpoint'],rt['dino_root'],read(CORE/'provenance/upstream/SOURCE_COMPARISON.json'));save_json(OBASE/'MODEL_RECEIPT.json',receipt)
     save_json(O/'INFERENCE_STARTED.json',dict(epoch=time.time(),budget=1,code_sha256=sha(__file__),input_sha256=sha(O/'INPUT_FROZEN.json')))
     rec['inference']=infer(model,fs,O);save_json(O/'PREDICTION_SHA256.json',dict(sha256=sha(O/'HERO_native.npz')))
    else:
     rec['inference']=read(O/'INFERENCE.json')
     if(O/'PREDICTION_SHA256.json').exists():assert sha(O/'HERO_native.npz')==read(O/'PREDICTION_SHA256.json')['sha256']
    rec['ring'],rec['a_to_b']=evaluate(row,fs,O);rec['status']='COMPLETED'
   except Exception as ex:rec.update(status='FAILED',error=repr(ex),traceback=traceback.format_exc());print(rec['traceback'],flush=True)
  results.append(rec);save_json(OBASE/'RESULTS.json',results);print('HERO_CHECK',row['case'],row['route'],rec['status'],flush=True)
if __name__=='__main__':main()
