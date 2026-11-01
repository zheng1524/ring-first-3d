"""E3-B: strict original-HERO whitelist, exact historical camera/geometry helpers."""
from pathlib import Path
from functools import lru_cache
import os,sys,ast,json,csv,hashlib,datetime,subprocess
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
A=REPO/'experiments/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001'
OLD=Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
E0=Path('/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001')
GROW=Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
PART=Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
SPARSE=Path('/home/liu/ring_first_3d/experiments/TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001')
VENDOR=OLD/'surface_fusion_v3/vendor'
for d in ['runtime/tmp','local_results','provenance','metrics','config','figures']:(R/d).mkdir(parents=True,exist_ok=True)
os.environ.update(CUDA_VISIBLE_DEVICES='',MPLCONFIGDIR=str(R/'runtime/mpl'),XDG_CACHE_HOME=str(R/'runtime/cache'),TMPDIR=str(R/'runtime/tmp'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode=True;ACCESSED=set();REUSE=[]
ns=ast.parse((E1/'code/common.py').read_text());names=['guard','sha','load','clean','save','table','stats','extract','asset','git','protected_state','ring']
exec(compile(ast.Module(body=[n for n in ns.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),str(E1/'code/common.py'),'exec'),globals())
_prior_guard=guard;ALLOWED_GEOMETRY=set();DENIALS=[]
def guard(event,args):
    _prior_guard(event,args)
    if event=='import'and str(args[0]).startswith(('torch','tensorflow','mast3r','mapanything.models','model.network')):raise PermissionError('E3B_NO_NEURAL_RUNTIME')
    if event=='open'and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve();s=str(p)
        if p.suffix.lower()in['.pt','.pth','.ckpt','.safetensors']:raise PermissionError('E3B_NO_CHECKPOINT')
        forbidden=('/local_results/glb/'in s or'/pointcloud_blocks/'in s or'_Joint_sources'in s or'/local_results/scenes/'in s or'/local_results/sdf_scene/'in s)
        if forbidden and p.suffix.lower()in['.npz','.ply','.obj','.glb','.json']:
            DENIALS.append(s);raise PermissionError('FUSION_OUTPUT_NOT_ALLOWED_AS_INPUT: '+s)
        if p.suffix.lower()in['.npz','.ply','.obj','.glb']and s.startswith('/home/liu/')and not p.is_relative_to(R)and s not in ALLOWED_GEOMETRY:
            DENIALS.append(s);raise PermissionError('E3B_GEOMETRY_NOT_ON_NATIVE_WHITELIST: '+s)
sys.addaudithook(guard)
import numpy as np,cv2,trimesh
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0,str(REPO));from visualization import real_p0_renderer as vis
from visualization.same_camera_scene import SameCameraScene
unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'])['unproject']
top=extract(SPARSE/'code/run.py',['face_components','edge_counts']);face_components=top['face_components'];edge_counts=top['edge_counts']
D=load(E1/'provenance/INPUT_ELIGIBILITY.json');CC={c['id']:c for c in D['references']};VV={v['id']:v for v in D['views']}
original_points=extract(E0/'code/evidence.py',['points'],dict(globals()))['points']
ROLES=load(A/'provenance/SOURCE_ROLES.json');ORG=load(A/'provenance/SOURCE_ORGANIZATION.json');ROI=load(A/'config/GLOBAL_ROI_FROZEN.json')
IDS=[s for o in ORG for s in o['reference_screened_sources']];REP=[s for o in ORG for s in o['representative_sources']]
def cfg():return load(R/'config/PROTOCOL_FROZEN.json')
def rows(path):return list(csv.DictReader(Path(path).open()))
def freeze(name,extra=None):save('provenance/'+name,dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],config=[asset(p)for p in sorted((R/'config').glob('*.json'))],extra=extra,GT_read=False,GPU_use=0,optimizer_step=0))
def register(path,expected=None):
    p=Path(path).resolve();ALLOWED_GEOMETRY.add(str(p))
    try:
        a=asset(p,expected=expected);assert a['status']=='AVAILABLE'and a.get('hash_match',True),a
    except Exception:ALLOWED_GEOMETRY.discard(str(p));raise
    return a
def allow_manifest():
    m=load(R/'HERO_NATIVE_INPUT_MANIFEST.json')
    for r in m['sources']:
        for a in r['assets'].values():ALLOWED_GEOMETRY.add(str(Path(a['path']).resolve()))
    return m
@lru_cache(None)
def manifest_row(cid):return next(r for r in allow_manifest()['sources']if r['source_id']==cid)
@lru_cache(None)
def source(cid):
    r=manifest_row(cid);c=CC[cid]
    for a in r['assets'].values():register(a['path'],a['sha256'])
    z=np.load(r['assets']['native_depth']['path']);p=np.load(c['pack']);q=np.load(c['source_points']);m=trimesh.load(c['mesh'],process=False);cl=np.load(c['cleaned_flags']['path'])
    P,C,F,uv=original_points(cid);original=q['original_faces']if'original_faces'in q else cl['original_faces']
    assert np.array_equal(F,original)and np.allclose(P,m.vertices,rtol=0,atol=1e-5),'RAW_ORIGINAL_FACE_IDENTITY_MISMATCH'
    native=z['depth_mm'];K=np.asarray(r['K_full']);Kn=np.asarray(r['K_native']);T=np.asarray(r['c2w']);labels=cv2.imread(c['Mask'],0)
    back=unproject(p['depth_mm'][uv[:,1],uv[:,0]],T,uv,K);assert np.max(abs(back-P))<=1e-6,'RAW_XYZ_NOT_DIRECT_ARCHIVED_DEPTH'
    resized=cv2.resize(native.astype(float),(labels.shape[1],labels.shape[0]),interpolation=cv2.INTER_LINEAR)
    zraw=(P-T[:3,3])@T[:3,2];err=np.max(abs(zraw-resized[uv[:,1],uv[:,0]]));assert err<=cfg()['ancestry_mm'],'RAW_XYZ_NOT_DIRECT_NATIVE_RESIZE'
    # Only original arrays retained. Cleaned flags never modify these arrays.
    for a in [P,F,uv,native,K,Kn,T,labels]:a.setflags(write=False)
    return dict(id=cid,c=c,row=r,P=P,F=F,uv=uv,K=K,Kn=Kn,T=T,depth=native,labels=labels,clean=cl,area=trimesh.triangles.area(P[F]),ancestry_error_mm=float(err),RGB=np.asarray(Image.open(c['RGB']).convert('RGB')))
@lru_cache(None)
def scene(cid):
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    s=source(cid);sc=o3d.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o3d.core.Tensor(s['P'].astype(np.float32)),o3d.core.Tensor(s['F'].astype(np.uint32)));return sc
def cast(cid,uv):
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    s=source(cid);r=scene(cid).cast_rays(o3d.core.Tensor(vis.camera_rays(uv,s['K'],s['T']).astype(np.float32)));return r['t_hit'].numpy(),r['primitive_ids'].numpy().astype(np.int64)
@lru_cache(None)
def camera(cid):
    s=source(cid);return SameCameraScene(ring(s['c']['ring']),s['K'],s['T'],(640,360),VENDOR)
def closest(cid,X):
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    r=scene(cid).compute_closest_points(o3d.core.Tensor(np.asarray(X,np.float32)));return r['points'].numpy().astype(float),r['primitive_ids'].numpy().astype(np.int64),r['primitive_uvs'].numpy()
def in_roi(cid,X):
    r=ROI[CC[cid]['scene_id']];return ((X>=np.array(r['minimum_mm']))&(X<=np.array(r['maximum_mm']))).all(1)

def initialize():
    assert git(REPO,'rev-parse','HEAD')=='8f5f7ea59efb32a0f633409386431811444ee399'
    assert len(IDS)==17 and len(REP)==12
    if(R/'provenance/PROTECTED_START.json').exists():assert load(R/'provenance/PROTECTED_START.json')==protected_state()
    else:save('provenance/PROTECTED_START.json',protected_state())
    save('config/PROTOCOL_FROZEN.json',dict(band_mm=.25,ordering_epsilon_mm=.002,ancestry_mm=2e-5,zero_mm=2e-5,native_zero_mm=1e-6,
        domain_grid_N=25,pair_sample_faces_max=2048,coverage_voxel_mm=.5,normal_azimuth_N=12,normal_elevation_N=6,
        normal_coherence_min=.85,incidence_abs_min=.2,barycentric_interior_min=1e-5,competing_centroid_candidates=32,competition_distance_gap_mm=.02,
        boundary_rule='faces incident to boundary vertices cannot assert sign; original boundary retained',
        sign_qualification='local camera-facing conditional only; no global inside/outside; k32 competition screen incomplete for arbitrary far-centroid large triangles',
        mesh_geometry_policy='retain every original vertex/face; raw-distance channel independent of legal-visibility validity',
        native_depth_sampling='nearest native pixel, half-pixel K conversion, no depth interpolation or hole filling',
        free_space='conditional trusted source first-surface segment; never assume ROI entrance outside; no CAD contradiction',
        maximum_CPU_seconds_per_scene=600,max_RAM_GiB=8,CPU_threads=2,source_selection='exact E3-A roles/order; CORE then BRIDGE then RESERVED; no reselection',
        GPU=0,new_inference=0,global_fit=0,geometry_deletion=0,GT=False))
    # Only two E3-A aliases require stepping back through the audited package script.
    aliases={'G01_005_raw00057':OLD/'ring_first_v6_local_reconstruction/raw/005_supported_ref00057.npz','G01_005_raw00459':OLD/'ring_first_v6_local_reconstruction/raw/005_supported_ref00459.npz'}
    result=[];audited_hashes={x['path']:x.get('sha256')for x in load(A/'provenance/INPUT_HASHES.json')['files']}
    for cid in IDS:
        c=CC[cid];native=aliases.get(cid,Path(c['E1_actual_native']['path']));assets={}
        for key,path in dict(native_depth=native,raw_XYZ=c['source_points'],raw_Mesh=c['mesh'],archived_direct_depth_pack=c['pack'],RGB=c['RGB'],Mask=c['Mask'],Cleaned_labels_only=c['cleaned_flags']['path'],CAD=c['Ring_CAD']['path'],camera_metadata=c['camera_file']).items():assets[key]=register(path,audited_hashes.get(str(path)))
        for i,v in enumerate(c['HERO_input_views']):assets['HERO_RGB_'+str(i)]=register(v['RGB'],v['sha256'])
        z=np.load(native);p=np.load(c['pack']);K=p['K'];Kn=vis.scaled_intrinsics(K,(640,360),(z['depth_mm'].shape[1],z['depth_mm'].shape[0]));stored=next((z[k]for k in ['K_index_native','K_index']if k in z),None)
        if stored is not None:assert np.allclose(Kn,stored,atol=1e-10,rtol=0),'NATIVE_K_CONVENTION_MISMATCH'
        result.append(dict(source_id=cid,scene=c['scene_id'],physical_group=c['group'],role=ROLES[cid],source_family=next(r['source_family']for r in rows(A/'metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv')if r['source_id']==cid),
            reference=c['reference'],HERO_upstream_RGB=c['HERO_input_views'],K_full=K,K_native=Kn,c2w=p['pose'],world_frame=c['coord_frame'],depth_unit='mm camera axial Z',native_shape=z['depth_mm'].shape,
            E3A_native_alias=c['E1_actual_native']['path'],alias_followed_to_raw=str(native)!=c['E1_actual_native']['path'],
            input_generation='native -> historical bilinear display resize -> exact original unproject/depth_mesh -> raw indexed geometry; no fusion or SE3 geometry correction',
            original_Mesh_fused_or_deformed=False,qualification='E3A_REFERENCE_SCREENED_CONDITIONAL',parent_camera_candidate_N=sum(bool(VV[v['id']].get('camera_candidate_only'))for v in c['HERO_input_views']),assets=assets))
    banned=[dict(kind=k,status='FUSION_OUTPUT_NOT_ALLOWED_AS_INPUT',path_pattern=p)for k,p in [('F1','multi-source union geometry'),('F2','*/pointcloud_blocks/*'),('F3','*/local_results/glb/*_Joint_sources.npz'),('adjusted_mesh','historical SE3-adjusted geometry'),('crossvideo','cross-video transformed/fused geometry'),('MonoSDF','E2.7 predicted surface')]]
    save('HERO_NATIVE_INPUT_MANIFEST.json',dict(task=R.name,parent_commit='8f5f7ea59efb32a0f633409386431811444ee399',sources=result,forbidden=banned,source_N=17,representative_source_ids=REP,
        generation_code=[asset(p)for p in [GROW/'code/hero_adapter.py',PART/'code/hero_new.py',OLD/'ring_first_v6_local_reconstruction/scripts/package_surfaces.py',OLD/'ring_first_v1/scripts/common.py']],
        alias_note='two G01_005 E3-A native pointers were direct resized source packages, not fused; E3-B B0 follows them to existing 352x640 raw inference output, exact resize equality required'))
    freeze('BEFORE_FIELD_EXECUTION.json');print('NATIVE_WHITELIST_FROZEN',17,flush=True)
if __name__=='__main__':initialize()
