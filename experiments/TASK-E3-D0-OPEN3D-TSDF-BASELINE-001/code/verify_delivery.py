"""Meaningful replay, unit/mask integrity and read-only contract checks.
Failures remain failures; this does not replace the failed preregistered gate.
"""
from hero_tsdf_adapter import *
def main():
    tests=[]
    def check(name,ok,detail):tests.append(dict(test=name,status='PASS'if bool(ok)else 'FAIL',detail=detail))
    manifest=load(R/'HERO_TSDF_INPUT_MANIFEST.json');mismatch=[]
    for r in manifest['sources']:
        for a in r['assets'].values():
            if sha(a['path'])!=a['sha256']:mismatch.append(a['path'])
        s=source(r['source_id']);ad=HEROToTSDFAdapter.from_source(s,cfg()['depth_trunc_mm']);labels=cv2.resize(s['labels'],(640,352),interpolation=cv2.INTER_NEAREST);rgbd=ad.rgbd();dep=np.asarray(rgbd.depth)
        check(r['source_id']+'_MASK_AND_UNITS',np.array_equal(dep,ad.depth_m)and np.all(dep[labels!=1]==0)and np.isfinite(dep).all()and np.all(dep[ad.valid]>0),dict(valid_N=int(ad.valid.sum()),Ring_included_N=int((dep[labels==2]>0).sum()),background_included_N=int((dep[labels==0]>0).sum())))
        v,u=np.nonzero(ad.valid);uv=np.c_[u,v];X=unproject(s['depth'][v,u],s['T'],uv,s['Kn']);p=np.c_[X*.001,np.ones(len(X))]@ad.w2c_m.T;z=s['depth'][v,u]*.001;check(r['source_id']+'_METRIC_W2C',np.max(abs(p[:,2]-z))<1e-8,float(np.max(abs(p[:,2]-z))))
    check('ALL_INPUT_SHA_UNCHANGED',not mismatch,dict(source_count=6,checked_assets=sum(len(r['assets'])for r in manifest['sources']),mismatch=mismatch))
    # Independent official re-integration from local masked replay, without reloading HERO data.
    vol=volume()
    for cid in cfg()['G0']:
        r=np.load(R/'local_results/RGBD_REPLAY'/(cid+'.npz'));K=r['K_native'];h,w=r['depth_m'].shape;rgbd=o3d.geometry.RGBDImage.create_from_color_and_depth(o3d.geometry.Image(r['RGB']),o3d.geometry.Image(r['depth_m']),depth_scale=1.,depth_trunc=cfg()['depth_trunc_mm']*.001,convert_rgb_to_intensity=False)
        intr=o3d.camera.PinholeCameraIntrinsic(w,h,K[0,0],K[1,1],K[0,2],K[1,2]);vol.integrate(rgbd,intr,r['w2c_m'])
    mesh=vol.extract_triangle_mesh();P=np.asarray(mesh.vertices)*1000;F=np.asarray(mesh.triangles);old=output_mesh('G0');ds=np.r_[distance(mesh_scene(old.vertices,old.faces),P),distance(mesh_scene(P,F),old.vertices)]
    check('OFFICIAL_G0_MASKED_RGBD_REPLAY',len(F)==len(old.faces)and len(P)==len(old.vertices)and np.max(ds)<1e-4,dict(vertex_count=len(P),face_count=len(F),surface_max_mm=float(ds.max()),source_RGBD_only=True))
    for name in ['SINGLE','G0','G1','SINGLE_RESOLUTION_CONTROL']:
        band=np.load(R/'local_results'/name/'tsdf_observed_band.npz');f=band['tsdf_normalized'];check(name+'_TSDF_REAL_OBSERVED_BAND',len(f)>0 and np.isfinite(f).all()and np.all((f>=-.981)&(f<=.981)),dict(sample_count=len(f),normalized_min=float(f.min()),normalized_max=float(f.max()),full_voxel_weights_available=False))
        p=R/'previews'/(name+'_mm.glb');scene=trimesh.load(p,force='scene',process=False);faces=sum(len(m.faces)for m in scene.geometry.values());expect=len(output_mesh(name).faces)+len(ringmesh().faces);check(name+'_ACTUAL_PREVIEW_FACES',faces==expect,dict(preview_faces=faces,expected_full_output_plus_CAD=expect))
    before=load(R/'config/PROTECTED_START.json');after=protected_state();save('config/PROTECTED_END.json',after);check('ALL_HISTORICAL_WORKTREES_UNCHANGED',before==after,dict(worktrees=len(after)))
    first=load(R/'config/SINGLE_FIRST_ATTEMPT_FAILURE.json');diag=load(R/'config/SINGLE_DIAGNOSIS.json')
    check('PREREGISTERED_SINGLE_GATE',first['engineering_pass'],dict(primary='FAIL retained; 89.56% native hits',unit_max_mm=diag['unit_surface_max_mm'],threshold_mm=.002,thresholds_changed=False))
    check('CPU_ONLY_RUNTIME','torch'not in sys.modules and str(o3d.core.Tensor([1]).device)=='CPU:0',dict(CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),official_runtime=o3d.__version__,neural_imports=False))
    save('VALIDATION_RESULTS.json',dict(tests=tests,pass_N=sum(t['status']=='PASS'for t in tests),fail_N=sum(t['status']=='FAIL'for t in tests),scientific_acceptance=False,adapter_formally_frozen=False,GT_read=False,neural_training=0,GPU_use=0,original_input_mutation=0,accessed_external_files=sorted(ACCESSED),denied_geometry_reads=DENIALS))
    table('VALIDATION_RESULTS.csv',tests)
    # Complete local evidence index; TSDF export limitation explicitly retained.
    files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()]
    save('LOCAL_RESULTS_INDEX.json',dict(local_root=R/'local_results',bytes=sum(a['bytes']for a in files),files=files,serialization='Mesh + official observed TSDF band (weight>0, -0.98<=tsdf<0.98) + full masked RGBD replay and ordered config; complete ScalableTSDFVolume weights not Python-exposed',raw_assets_copied=False))
    save('config/OPEN3D_RUNTIME_PROVENANCE.json',dict(version=o3d.__version__,CPU_tensor_device=str(o3d.core.Tensor([1]).device),installed_module=o3d.__file__,examples=[asset(VENDOR/'open3d/examples/reconstruction_system/integrate_scene.py'),asset(VENDOR/'open3d/examples/benchmark/benchmark_tsdf.py')],source_urls=['https://raw.githubusercontent.com/isl-org/Open3D/v0.19.0/cpp/open3d/pipelines/integration/ScalableTSDFVolume.cpp','https://raw.githubusercontent.com/isl-org/Open3D/v0.19.0/cpp/open3d/pipelines/integration/UniformTSDFVolume.cpp']))
    print('VALIDATED',sum(t['status']=='PASS'for t in tests),'PASS',sum(t['status']=='FAIL'for t in tests),'FAIL (preserved)',flush=True)
if __name__=='__main__':main()
