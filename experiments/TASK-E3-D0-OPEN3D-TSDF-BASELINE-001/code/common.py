"""Read-only historical assets; task-local outputs; exact reused camera helpers."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
VENDOR=OLD/'surface_fusion_v3/vendor'
for p in ['runtime/tmp','config','local_results','figures','previews']:(R/p).mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',MPLCONFIGDIR=str(R/'runtime/mpl'),XDG_CACHE_HOME=str(R/'runtime/cache'),TMPDIR=str(R/'runtime/tmp'))
sys.dont_write_bytecode=True; ACCESSED=set(); REUSE=[]
names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state']
tree=ast.parse((E1/'code/common.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
parent_guard=guard
D=load(E1/'provenance/INPUT_ELIGIBILITY.json');CC={c['id']:c for c in D['references']if c['scene_id']=='G01_004'}
ALLOWED={str(Path(c[k]).resolve())for c in CC.values()for k in ['pack','source_points','mesh','camera_file']}
ALLOWED.update(str(Path(c['E1_actual_native']['path']).resolve())for c in CC.values())
CAD=Path(next(iter(CC.values()))['Ring_CAD']['path']);ALLOWED.add(str(CAD))
DENIALS=[]
def guard(event,args):
    parent_guard(event,args)
    if event=='import'and str(args[0]).startswith(('torch','tensorflow','mast3r','model.network','transformers.models')):raise PermissionError('NO_MODEL_RUNTIME')
    if event=='open'and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve()
        if p.suffix.lower()in ['.pth','.pt','.ckpt','.safetensors']:raise PermissionError('NO_MODEL_WEIGHTS')
        if str(p).startswith('/home/liu/')and p.suffix.lower()in ['.npz','.obj','.ply','.glb']and not p.is_relative_to(R)and str(p)not in ALLOWED:
            DENIALS.append(str(p));raise PermissionError('NOT_AN_ORIGINAL_HERO_INPUT: '+str(p))
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
sys.path.insert(0,str(VENDOR));import open3d as o3d
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']
CORE=['G01_004_ref03','G01_004_ref08','G01_004_ref13']
G1=CORE+['G01_004_growth_r04','G01_004_new_r00','G01_004_growth_r14']
def cfg():return load(R/'TSDF_CONFIG.json')
def checked_asset(p,expected=None):
    a=asset(p,expected=expected);assert a['status']=='AVAILABLE'and a.get('hash_match',True),a;return a
@lru_cache(None)
def source(cid):
    c=CC[cid];z=np.load(c['E1_actual_native']['path']);p=np.load(c['pack']);q=np.load(c['source_points'])
    P=np.asarray(q['points_mm']if'points_mm'in q else q['XYZ_mm']); F=q['original_faces'];uv=q['uv']if'uv'in q else q['source_uv']
    K=p['K'];T=p['pose']; native=z['depth_mm'];labels=np.asarray(Image.open(c['Mask']));rgb=np.asarray(Image.open(c['RGB']).convert('RGB'))
    Kn=vis.scaled_intrinsics(K,(labels.shape[1],labels.shape[0]),(native.shape[1],native.shape[0]))
    stored=next((z[k]for k in ['K_index_native','K_index']if k in z),None)
    assert stored is None or np.allclose(Kn,stored,rtol=0,atol=1e-10),'NATIVE_K'
    assert np.allclose(T,np.asarray(c['c2w_mm']),rtol=0,atol=1e-10),'MANIFEST_POSE'
    camera=np.load(c['camera_file']);assert np.allclose(T,camera['c2w'][c['reference_index']],rtol=0,atol=1e-10),'CAMERA_IDENTITY'
    nt=next((z[k]for k in ['reference_pose_mm','pose']if k in z),None)
    assert nt is None or np.allclose(nt,T,rtol=0,atol=1e-10),'NATIVE_POSE'
    assert np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-10)and np.linalg.det(T[:3,:3])>0
    arch=cv2.resize(native.astype(float),(labels.shape[1],labels.shape[0]),interpolation=cv2.INTER_LINEAR)
    ancestry=float(np.max(abs(arch[uv[:,1],uv[:,0]]-p['depth_mm'][uv[:,1],uv[:,0]])))
    exact=float(np.max(abs(unproject(p['depth_mm'][uv[:,1],uv[:,0]],T,uv,K)-P)))
    assert ancestry<=2e-5 and exact<=1e-6,('NOT_DIRECT_NATIVE',ancestry,exact)
    raw=trimesh.load(c['mesh'],process=False);assert np.array_equal(F,raw.faces)and np.max(abs(P-raw.vertices))<1e-5
    for a in [P,F,uv,K,Kn,T,native,labels,rgb]:a.setflags(write=False)
    return dict(id=cid,c=c,P=P,F=F,uv=uv,K=K,Kn=Kn,T=T,depth=native,labels=labels,RGB=rgb,area=trimesh.triangles.area(P[F]),ancestry_mm=ancestry,XYZ_roundtrip_mm=exact)
def mesh_scene(P,F):
    s=o3d.t.geometry.RaycastingScene(nthreads=2);s.add_triangles(o3d.core.Tensor(np.asarray(P,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)));return s
def cast(scene,uv,K,T):
    r=scene.cast_rays(o3d.core.Tensor(vis.camera_rays(np.asarray(uv),K,T).astype(np.float32)));return r['t_hit'].numpy().astype(float),r['primitive_ids'].numpy().astype(np.int64)
def distance(scene,X):return scene.compute_distance(o3d.core.Tensor(np.asarray(X,np.float32))).numpy().astype(float)
@lru_cache(None)
def ringmesh():return trimesh.load(CAD,process=False)
@lru_cache(None)
def ringscene():return mesh_scene(ringmesh().vertices,ringmesh().faces)
def output_mesh(name):return trimesh.load(R/'local_results'/name/'mesh_mm.ply',process=False)
def face_samples(s,n=None):
    # Fixed original face IDs, evenly spaced in original indexing; no output-dependent selection.
    n=n or cfg()['evaluation']['max_faces_per_source'];f=np.unique(np.linspace(0,len(s['F'])-1,min(n,len(s['F'])),dtype=int));return f,s['P'][s['F'][f]].mean(1)
def snapshot(name):save('config/'+name+'.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],config=asset(R/'TSDF_CONFIG.json'),selection=asset(R/'VIEW_COVERAGE_SELECTION.csv'),manifest=asset(R/'HERO_TSDF_INPUT_MANIFEST.json')))
