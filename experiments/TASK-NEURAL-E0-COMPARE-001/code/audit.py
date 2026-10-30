"""Bounded P0 audit. No model execution, GT, new camera fit or old-output writes."""
from pathlib import Path
import ast, csv, datetime, hashlib, importlib.metadata, importlib.util, json
import os, shutil, subprocess, sys, traceback
R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
GROW = Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
PART = Path('/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001')
INC = Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
OLD = Path('/home/liu/polyp_research/ring_anchor_3d/experiments')
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['MPLCONFIGDIR'] = str(R/'runtime/mpl')
sys.path.insert(0, str(REPO))
import numpy as np
import cv2
from PIL import Image
from visualization import real_p0_renderer as vis

def guard(event, args):
    if event != 'open' or not isinstance(args[0], (str, bytes)): return
    p = Path(os.fsdecode(args[0])).resolve(); s = str(p); n = p.name.lower()
    if n.endswith('.blend') or n.startswith('gt_') or 'oracle' in n or any(x in s for x in ['/private_gt/', '/gt_mapping/', '/evaluation_exports/', '/evaluation_only/', '/new-polyp-dxy/']):
        raise PermissionError('GT/DXY_ACCESS_DENIED: '+s)
    mode = args[1] if len(args)>1 and isinstance(args[1], str) else ''
    flags = args[2] if len(args)>2 and isinstance(args[2], int) else 0
    if any(x in mode for x in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
        if s.startswith('/home/liu/') and not p.is_relative_to(R):
            raise PermissionError('TASK_OUTPUT_ONLY: '+s)
sys.addaudithook(guard)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20), b''): h.update(b)
    return h.hexdigest()
def load(p): return json.loads(Path(p).read_text())
def normal(v):
    if isinstance(v,dict): return {str(k):normal(x) for k,x in v.items()}
    if isinstance(v,(tuple,list)): return [normal(x) for x in v]
    if isinstance(v,np.ndarray): return normal(v.tolist())
    if isinstance(v,np.generic): return normal(v.item())
    if isinstance(v,float) and not np.isfinite(v): return None
    return v
def save(name, data):
    p=R/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(normal(data),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(name,rows):
    p=R/name; p.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,keys,lineterminator='\n'); w.writeheader()
        for r in rows:w.writerow({k:json.dumps(normal(v),ensure_ascii=False) if isinstance(v,(dict,list,tuple,np.ndarray)) else normal(v) for k,v in r.items()})
def run(cmd):
    p=subprocess.run(cmd,text=True,capture_output=True,timeout=40)
    return dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
def protected():
    roots=[Path('/home/liu/polyp_research'),*sorted(Path('/home/liu').glob('ring_first_3d*'))]
    rows=[]
    for root in roots:
        if root==REPO or not (root/'.git').exists():continue
        head=run(['git','-C',str(root),'rev-parse','HEAD'])['stdout'].strip()
        status=run(['git','-C',str(root),'status','--porcelain','-uno'])['stdout']
        files={}
        for l in status.splitlines():
            p=root/l[3:]
            if p.is_file():files[l[3:]]=sha(p)
        rows.append(dict(root=str(root),HEAD=head,status=status,modified_sha256=files))
    return rows

def environment():
    import torch
    rows={}
    for name in ['torch','torchvision','numpy','opencv-python','trimesh','pyhocon','scikit-image','tensorboard','hydra-core','uniception','huggingface-hub','natsort','safetensors','tinycudann']:
        try:rows[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:rows[name]=None
    d=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=sys.version,executable=sys.executable,packages=rows,CUDA_build=torch.version.cuda,CUDA_available=torch.cuda.is_available(),nvidia_smi=run(['nvidia-smi']),disk_usage=shutil.disk_usage(REPO)._asdict(),df=run(['df','-h',str(REPO)]),nvcc=shutil.which('nvcc'),cmake=shutil.which('cmake'),ninja=shutil.which('ninja'),driver_changed=False,CPU_model_fallback=False)
    start=__import__('time').monotonic()
    try:
        x=torch.arange(8,device='cuda');torch.cuda.synchronize()
        d.update(cuda_tensor_values=x.cpu().tolist(),cuda_tensor_status='PASS',gpu=torch.cuda.get_device_name(0),cuda_free_total_bytes=torch.cuda.mem_get_info())
    except Exception:d.update(cuda_tensor_status='FAILED',cuda_error=traceback.format_exc())
    d['cuda_probe_seconds']=__import__('time').monotonic()-start
    roots=[Path('/home/liu/.cache/huggingface/hub'),Path('/home/liu/.cache/torch'),Path('/home/liu/polyp_research/.hf_cache')]
    d['cache_roots']=[dict(path=str(p),exists=p.exists(),matching_model_directories=[str(x) for x in p.rglob('*') if x.is_dir() and any(k in x.name.lower() for k in ['map-anything','monosdf','neus2','sparserecon'])]) for p in roots]
    save('provenance/ENVIRONMENT_CHECK.json',d)
    return d

def extract(path,names,ns):
    tree=ast.parse(Path(path).read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
    return ns

def audit_inputs():
    cases=load(INC/'provenance/CASES.json')+load(PART/'provenance/NEW_CASES.json')+load(GROW/'provenance/NEW_CASES.json')
    assert len(cases)==36 and len({x['id']for x in cases})==36
    views=load(PART/'metrics/view_distribution.json'); byid={v['id']:v for v in views}
    file_rows={};view_rows=[]
    def file(p,role):
        p=Path(p);key=str(p)
        if key not in file_rows:
            r=dict(path=key,exists=p.is_file(),roles=[role])
            if r['exists']:r.update(bytes=p.stat().st_size,sha256=sha(p))
            file_rows[key]=r
        elif role not in file_rows[key]['roles']:file_rows[key]['roles'].append(role)
        return file_rows[key]
    for v in views:
        r=dict(v)
        for k in ['RGB','Mask']:
            if v.get(k):r[k+'_audit']=file(v[k],k)
        if r.get('RGB_audit',{}).get('exists'):
            im=np.asarray(Image.open(v['RGB']).convert('RGB'));r['decoded_RGB_SHA256']=hashlib.sha256(im.tobytes()).hexdigest();r['image_shape']=im.shape
        view_rows.append(r)
    byid={v['id']:v for v in view_rows}
    src=[];tests=[]
    unproject=extract(OLD/'ring_first_v1/scripts/common.py',['unproject'],dict(np=np))['unproject']
    for c in cases:
        sid=c['group']+'_'+c['video']; r=dict(c,scene_id=sid,coord_frame=sid+'_LOCAL_RING_MM',depth_type='camera_axial_Z',xyz_unit='mm',GT_access='DENY',role='HISTORICAL_INPUT_ONLY_E0_NOT_RUN')
        r['files']={k:file(c[k],k) for k in ['RGB','Mask','pack','mesh','source_points','camera_file']}
        if not all(x['exists']for x in r['files'].values()):
            r['input_status']='NOT_EVALUABLE_MISSING_FILE';src.append(r);continue
        with np.load(c['pack']) as p:
            K=p['K'];pose=p['pose'];depth=p['depth_mm'];labels=p['labels'];r.update(K_raw=K,K_after_resize=K,c2w_mm=pose,depth_shape=depth.shape,distortion='NOT_IN_PACK_PINHOLE_ASSUMPTION_NO_NEW_UNDISTORT',pose_status=c.get('camera_identity','FROZEN_ARCHIVED_CONDITIONAL'),original_frame_id=c.get('raw_frame'),frame_binding=c.get('frame_binding','archived reference metadata; G01_004 raw sequential identity unverified' if sid=='G01_004' else 'archived index/raw ledger'),HERO_source_list_recorded='sources'in p)
            sources=p['sources'].tolist() if 'sources'in p else []
            native=Path(str(p['native_source'].item())) if 'native_source'in p else None
        if native is None and c.get('new_reference'):native=Path(c['pack']).parent/'HERO_native.npz'
        # Three legacy display packs dropped dependency metadata. Recover only
        # from their hashable raw-point provenance, never infer source frames.
        if native is None:
            with np.load(c['source_points']) as zz:
                if 'source_depth_path' in zz:
                    native=Path(zz['source_depth_path'].item())
                    r['native_origin_evidence']='source_points.source_depth_path'
                    with np.load(native) as raw:
                        if 'sources' in raw:
                            sources=raw['sources'].tolist()
                            r['HERO_source_list_recorded']=True
                            r['HERO_source_list_recovered_from_native']=True
        r['native_depth']=file(native,'native_depth') if native else dict(exists=False,reason='native origin not recorded in pack')
        r['HERO_sources_recorded']=sources
        depids=[];unknown=[]
        ref=next((v for v in views if v.get('source_id')==c['group']+'_video'+c['video'] and v.get('index')==c['reference_index']),None)
        if ref:depids.append(ref['id'])
        else:unknown.append('reference index absent')
        for s in sources:
            if isinstance(s,int):v=next((v for v in views if v.get('source_id')==c['group']+'_video'+c['video'] and v.get('index')==s),None)
            else:v=byid.get(s)
            if v:depids.append(v['id'])
            else:unknown.append(str(s))
        deps=[byid[x]for x in dict.fromkeys(depids)]
        r['HERO_input_views']=[dict(id=v['id'],RGB=v['RGB'],sha256=byid[v['id']].get('RGB_audit',{}).get('sha256'))for v in deps]
        r['HERO_dependency_complete']=bool(r['HERO_source_list_recorded'] and not unknown and all(v['sha256']for v in r['HERO_input_views']))
        r['HERO_dependency_unknown']=unknown if r['HERO_source_list_recorded'] else ['legacy source list absent']
        r['source_alias_hashes']=[x['sha256']for x in r['HERO_input_views'] if x['sha256']]
        clean=GROW/f'local_results/cleaned/{c["id"]}.npz'
        r['cleaned_flags']=file(clean,'cleaned_flags')
        z=np.load(c['source_points']);P=z['XYZ_mm'] if 'XYZ_mm' in z else z['points_mm']
        uv=next((z[k] for k in ['source_uv','pixel_uv','uv'] if k in z),None)
        if uv is None:uv=np.c_[z['source_u'],z['source_v']]
        uv=uv.astype(int);rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));mask=np.asarray(Image.open(c['Mask']))
        reproj,Z=vis.project_camera(P,K,pose);back=unproject(depth[uv[:,1],uv[:,0]],pose,uv,K)
        native_resize_error=None
        if r['native_depth']['exists']:
            nz=np.load(r['native_depth']['path']);n=nz['depth_mm'] if 'depth_mm'in nz else None
            if n is not None:native_resize_error=float(np.max(abs(cv2.resize(np.squeeze(n).astype(float),(depth.shape[1],depth.shape[0]),interpolation=cv2.INTER_LINEAR)-depth)))
        Ksmall=vis.scaled_intrinsics(K,(640,360),(320,180));ps,zz=vis.project_camera(P,Ksmall,pose)
        pm=pose.copy();pm[:3,3]/=1000;uvm,zm=vis.project_camera(P/1000,K,pm)
        ring=OLD/'surface_fusion_v2/inputs/R10_ring.obj' if c['ring']=='R10' else OLD.parent/'assets/ring_R5.obj';r['Ring_CAD']=file(ring,'Ring_CAD')
        import trimesh
        mesh=trimesh.load(c['mesh'],process=False);cad=trimesh.load(ring,process=False);ruv,rz=vis.project_camera(cad.vertices,K,pose)
        t=dict(source=c['id'],point_N=len(P),mesh_vertex_N=len(mesh.vertices),source_UV_reprojection_max_px=float(np.max(abs(reproj-uv))),legacy_unproject_max_mm=float(np.max(abs(back-P))),axial_Z_error_max_mm=float(np.max(abs(Z-depth[uv[:,1],uv[:,0]]))),ray_distance_minus_Z_median_mm=float(np.median(np.linalg.norm(P-pose[:3,3],axis=1)-Z)),pose_det=float(np.linalg.det(pose[:3,:3])),pose_orthogonality_max=float(np.max(abs(pose[:3,:3].T@pose[:3,:3]-np.eye(3)))),positive_Z_fraction=float((Z>0).mean()),RGB_Mask_labels_equal=bool(np.array_equal(mask,labels)),RGB_depth_shape_equal=rgb.shape[:2]==depth.shape,raw_XYZ_mesh_max_mm=float(np.max(abs(P-np.asarray(mesh.vertices)))),mm_to_m_reprojection_max_px=float(np.max(abs(uvm-reproj))),mm_to_m_depth_error_max_m=float(np.max(abs(zm-Z/1000))),resize_K_reprojection_max_px=float(np.max(abs(ps-((reproj+.5)*.5-.5)))),native_bilinear_resize_max_mm=native_resize_error,Ring_positive_Z_fraction=float((rz>0).mean()),Ring_CAD_watertight=bool(cad.is_watertight))
        t['contract_pass']=bool(t['source_UV_reprojection_max_px']<1e-6 and t['legacy_unproject_max_mm']<1e-6 and t['axial_Z_error_max_mm']<1e-6 and abs(t['pose_det']-1)<1e-6 and t['RGB_Mask_labels_equal'] and t['RGB_depth_shape_equal'] and t['raw_XYZ_mesh_max_mm']<1e-5 and t['resize_K_reprojection_max_px']<1e-6)
        r['input_status']='STATIC_GEOMETRY_PASS_CONDITIONAL_CAMERA'if t['contract_pass']else'NOT_EVALUABLE_CONTRACT_FAILED'
        src.append(r);tests.append(t)
    targets=load(GROW/'provenance/EVALUATION_TARGETS_FROZEN.json')['targets'];leaks=[]
    for t in targets:
        v=byid[t['target']];h=v.get('RGB_audit',{}).get('sha256');scene=[r for r in src if r['scene_id']==t['scene']]
        known=[r['id']for r in scene if h and h in r.get('source_alias_hashes',[])]
        unknown=[r['id']for r in scene if not r.get('HERO_dependency_complete')]
        tier='HOLDOUT_RECON_ONLY' if not known and not unknown and t['scene'] not in ['G01_004','G08_005'] else 'DIAGNOSTIC_ONLY'
        if 'UNQUALIFIED'in v.get('condition',''):tier='DIAGNOSTIC_ONLY_UNQUALIFIED_CAMERA'
        leaks.append(dict(scene=t['scene'],target=t['target'],RGB=v['RGB'],RGB_SHA256=h,Mask_SHA256=v.get('Mask_audit',{}).get('sha256'),known_HERO_input_of=known,unresolved_HERO_batches=unknown,holdout_tier=tier,strict_holdout=False,strict_reason='historical protocol exposure; no E0-blind test certification' if not known and not unknown else 'known source overlap or unresolved dependency',role='EVALUATION_ONLY_NOT_MODEL_INPUT',target_Polyp_pixels=v.get('Mask_polyp_N',v.get('observed_Polyp_pixels'))))
    save('provenance/INPUT_ELIGIBILITY.json',dict(physical_groups=4,video_scenes=5,references=src,views=view_rows,targets=leaks,GT_access='DENY',model_predictions_generated=0))
    table('provenance/SOURCE_SHA_LEDGER.csv',list(file_rows.values()));table('provenance/SOURCE_LEAKAGE_LEDGER.csv',leaks)
    save('provenance/FRAME_CONVENTION_TESTS.json',tests)
    edges=[dict(reference=r['id'],scene=r['scene_id'],input_view=x['id'],RGB_SHA256=x['sha256']) for r in src for x in r['HERO_input_views']]
    table('provenance/HERO_DEPENDENCY_EDGES.csv',edges)
    frame_roles=[]
    for v in view_rows:
        h=v.get('RGB_audit',{}).get('sha256')
        frame_roles.append(dict(view=v['id'],historical_role=v.get('role'),RGB_SHA256=h,used_by_HERO=[r['id']for r in src if h and h in r['source_alias_hashes']],strict_holdout=False))
    table('provenance/ALL_FRAME_HERO_MEMBERSHIP.csv',frame_roles)
    expected={}
    for manifest in [GROW/'provenance/FINAL_ACTUAL_SOURCE_INPUTS.json',PART/'provenance/INPUTS_FROZEN.json',GROW/'provenance/INPUTS_FROZEN.json']:
        for f in load(manifest).get('files',[]):
            if f['path'] in file_rows:expected.setdefault(f['path'],set()).add(f['sha256'])
    comparisons=[dict(path=p,expected_SHA256=sorted(h),actual_SHA256=file_rows[p].get('sha256'),match=file_rows[p].get('sha256') in h) for p,h in expected.items()]
    save('metrics/HISTORICAL_MANIFEST_CHECK.json',comparisons)
    groups=[]
    for sid in dict.fromkeys(r['scene_id']for r in src):
        rr=[r for r in src if r['scene_id']==sid];tt=[l for l in leaks if l['scene']==sid]
        groups.append(dict(group=sid[:3],scene=sid,condition=rr[0]['condition'],reference_N=len(rr),static_geometry_pass_N=sum(r['input_status']=='STATIC_GEOMETRY_PASS_CONDITIONAL_CAMERA'for r in rr),complete_HERO_dependencies_N=sum(r['HERO_dependency_complete']for r in rr),historical_target_N=len(tt),strict_holdout_N=0,new_arm_success_N=0,Arm_S='NOT_RUN_RESOURCE_GATE',Arm_M='NOT_RUN_RESOURCE_GATE'))
    table('metrics/FOUR_GROUP_READINESS.csv',groups)
    failures=[x for x in load(GROW/'metrics/new_HERO_sources.json') if not x.get('success')]
    save('provenance/HISTORICAL_GPU_FAILURES.json',failures)
    print('AUDIT',len(src),'sources',sum(t['contract_pass']for t in tests),'contracts pass;',len(leaks),'targets; dependencies complete',sum(r['HERO_dependency_complete']for r in src),flush=True)
    return src,leaks,tests

def code_reuse():
    entries=[
      ('camera_frame_inventory',Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/inventory.py'),['camera_frame_inventory']),
      ('HERO_loader',OLD/'surface_fusion_v1/scripts/run_mvs_adapter3.py',['load_official']),
      ('XYZ_and_mesh',OLD/'ring_first_v1/scripts/common.py',['unproject','depth_mesh']),
      ('camera',GROW/'code/common.py',['source','target_source']),
      ('cleaning',Path('/home/liu/ring_first_3d_grazing/experiments/TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/cleaning.py'),[]),
      ('MASt3R_matching',PART/'code/matching.py',[]),
      ('candidate_registration',PART/'code/registration.py',[]),
      ('Ring_CAD_audit',GROW/'code/cad_audit.py',['main']),
      ('real_A_to_B',GROW/'code/geometry.py',['projection','metric','common_metric']),
      ('renderer',REPO/'visualization/real_p0_renderer.py',['view','project_camera','draw_rgb_points','scaled_intrinsics']),
      ('same_camera',REPO/'visualization/same_camera_scene.py',['SameCameraScene']),
      ('GLB_and_source_index',GROW/'code/evaluate.py',['unique_points','export'])]
    rows=[]
    for role,path,names in entries:
        tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and(not names or n.name in names)]
        rows.append(dict(role=role,path=str(path),file_SHA256=sha(path),entrypoints=[dict(name=n.name,line=n.lineno,signature=ast.unparse(n.args)if isinstance(n,ast.FunctionDef)else'class',AST_SHA256=hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest()) for n in nodes],dependencies=[ast.unparse(n)for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))],adapter_needed='format/units/source support only; no camera, depth, backprojection or rendering replacement'))
    save('provenance/CODE_REUSE_EXECUTED.json',rows)
    weights=[OLD/'surface_fusion_v1/weights/mvsanywhere_hero_full.ckpt',OLD/'ring_first_v9_ring_guided_recovery/weights/MASt3R_official.pth']
    save('provenance/FROZEN_WEIGHT_LOCAL_SHA.json',[dict(path=str(p),exists=p.exists(),bytes=p.stat().st_size,sha256=sha(p),read_only=True,used_for_new_forward=False)for p in weights if p.exists()])

if __name__=='__main__':
    if not (R/'provenance/PROTECTED_START.json').exists():save('provenance/PROTECTED_START.json',protected())
    env=environment();audit_inputs();code_reuse()
    before=load(R/'provenance/PROTECTED_START.json');after=protected();save('provenance/PROTECTED_END.json',after)
    save('metrics/PROTECTION_CHECK.json',dict(equal=before==after,old_files_modified_by_task=False))
    assert before==after,'protected workspace changed; inspect external changes'
