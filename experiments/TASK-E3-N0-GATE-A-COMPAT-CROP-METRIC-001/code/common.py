"""N0: exact historical functions, six original HERO sources, task-local writes."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
D0=REPO/'experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001'
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');VENDOR=OLD/'surface_fusion_v3/vendor'
NF=R/'runtime/neuralfusion_official';NF_COMMIT='4f0c14f67ad9d2368b68cbeb78c237a6328971e5'
for d in ['runtime/tmp','local_results','config','figures','docs']:(R/d).mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),XDG_CACHE_HOME=str(R/'runtime/cache'),TMPDIR=str(R/'runtime/tmp'),HF_HUB_OFFLINE='1')
sys.dont_write_bytecode=True;ACCESSED=set();REUSE=[];DENIALS=[]
tree=ast.parse((E1/'code/common.py').read_text());names=['sha','load','clean','save','table','stats','extract','asset','git','protected_state']
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
IDS=['G01_004_ref08','G01_004_ref13','G01_004_ref03','G01_004_growth_r04','G01_004_new_r00','G01_004_growth_r14'];CORE=IDS[:3]
MANIFEST=load(D0/'HERO_TSDF_INPUT_MANIFEST.json');assert set(IDS)=={r['source_id']for r in MANIFEST['sources']}
CC={c['id']:c for c in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']if c['id']in IDS}
CAD=Path(MANIFEST['CAD']['path']);ALLOWED={str(Path(a['path']).resolve())for r in MANIFEST['sources']for a in r['assets'].values()};ALLOWED.add(str(CAD))
def guard(event,args):
    if event in ['socket.connect','socket.getaddrinfo']:raise PermissionError('N0_OFFLINE_EXECUTION_AFTER_VERIFIED_FETCH')
    if event=='import'and (str(args[0]).startswith(('training','pytorch_lightning','graphics','dataset'))):
        DENIALS.append('IMPORT:'+str(args[0]));raise PermissionError('N0_GT_TRAINING_ENTRYPOINT_BLOCKED')
    if event!='open'or not isinstance(args[0],(str,bytes)):return
    p=Path(os.fsdecode(args[0])).resolve();s=str(p);mode=args[1]if len(args)>1 and isinstance(args[1],str)else '';flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;writing=any(v in mode for v in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
    if writing and s.startswith('/home/liu/')and not p.is_relative_to(R):raise PermissionError('N0_TASK_LOCAL_WRITE_ONLY:'+s)
    if not p.is_relative_to(R):
        if p.name.lower().startswith('gt_')or p.suffix.lower()=='.blend'or any(v in s.lower()for v in ['/new-polyp-dxy/','/private_gt/','/oracle/','/evaluation_only/']):
            DENIALS.append(s);raise PermissionError('N0_GT_ORACLE_DXY_BLOCKED')
        if s.startswith('/home/liu/')and p.suffix.lower()in ['.npz','.npy','.obj','.ply','.glb','.ckpt','.pt','.pth']and s not in ALLOWED:
            DENIALS.append(s);raise PermissionError('N0_SOURCE_NOT_ON_SIX_HERO_WHITELIST:'+s)
        if not writing and s.startswith('/home/liu/'):ACCESSED.add(s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']
extract(D0/'code/common.py',['source','mesh_scene','cast','distance','ringmesh','ringscene'],globals())
extract(D0/'code/hero_tsdf_adapter.py',['HEROToTSDFAdapter'],globals())
def native(cid):
    s=source(cid);a=HEROToTSDFAdapter.from_source(s,load(D0/'TSDF_CONFIG.json')['depth_trunc_mm']);h,w=s['depth'].shape
    labels=cv2.resize(s['labels'],(w,h),interpolation=cv2.INTER_NEAREST);rgb=cv2.resize(s['RGB'],(w,h),interpolation=cv2.INTER_AREA)
    valid=(labels==1)&np.isfinite(s['depth'])&(s['depth']>0);assert np.array_equal(valid,a.valid),'D0_VALIDITY_DIFFERENCE'
    v,u=np.nonzero(valid);uv=np.c_[u,v];X=unproject(s['depth'][v,u].astype(float),s['T'],uv,s['Kn'])
    return dict(**s,native_labels=labels,native_RGB=rgb,valid=valid,native_uv=uv,native_id=v*w+u,X=X)
def config():return load(R/'config/GATE_A_PREREGISTERED.json')
def affine_uv(uv,A):return np.c_[uv,np.ones(len(uv))]@np.asarray(A)[:2].T
def summarize(a):
    a=np.asarray(a,float);ok=np.isfinite(a);d=stats(a);d.update(total_N=len(a),nonfinite_N=int((~ok).sum()));return d
