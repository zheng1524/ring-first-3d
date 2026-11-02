"""Official Open3D integration. No custom weights, carving, mesh repair or deletion."""
from hero_tsdf_adapter import *
from scipy.spatial import cKDTree
import time

def integrate(name,ids,unit_mm=False,export=True,voxel_override=None):
    c=cfg();d=R/'local_results'/name;d.mkdir(parents=True,exist_ok=True)
    factor=1. if unit_mm else .001
    vol=o3d.pipelines.integration.ScalableTSDFVolume(voxel_length=(voxel_override or c['voxel_length_mm'])*factor,sdf_trunc=c['sdf_trunc_mm']*factor,color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8,volume_unit_resolution=c['volume_unit_resolution'],depth_sampling_stride=c['depth_sampling_stride'])
    log=[];t0=time.monotonic()
    for cid in ids:
        s=source(cid);a=HEROToTSDFAdapter.from_source(s,c['depth_trunc_mm'])
        if unit_mm:
            rgbd=o3d.geometry.RGBDImage.create_from_color_and_depth(o3d.geometry.Image(a.rgb),o3d.geometry.Image((a.depth_m*1000).astype(np.float32)),depth_scale=1.,depth_trunc=c['depth_trunc_mm'],convert_rgb_to_intensity=False)
            E=np.linalg.inv(s['T'])
        else:rgbd=a.rgbd();E=a.w2c_m
        vol.integrate(rgbd,a.intrinsic,E)
        log.append(dict(source_id=cid,valid_native_depth_N=int(a.valid.sum()),unknown_depth_exactly_zero=bool(np.all(a.depth_m[~a.valid]==0)),finite=bool(np.isfinite(a.depth_m).all()),native_shape=a.depth_m.shape,elapsed_s=time.monotonic()-t0))
        if export:
            replay=R/'local_results/RGBD_REPLAY';replay.mkdir(exist_ok=True)
            np.savez_compressed(replay/(cid+'.npz'),depth_m=a.depth_m,RGB=a.rgb,K_native=a.K,w2c_m=a.w2c_m,valid=a.valid)
        print(name,cid,'integrated',int(a.valid.sum()),flush=True)
    mesh=vol.extract_triangle_mesh();assert len(mesh.triangles)>0,'EMPTY_OFFICIAL_MESH'
    P=np.asarray(mesh.vertices).copy()/factor;F=np.asarray(mesh.triangles).copy()
    if export:
        # The actual unmodified Open3D Mesh, converted m->mm once. No smoothing/cleanup.
        mesh.vertices=o3d.utility.Vector3dVector(P);mesh.compute_vertex_normals()
        assert o3d.io.write_triangle_mesh(str(d/'mesh_mm.ply'),mesh,write_ascii=False)
        band=vol.extract_voxel_point_cloud()
        # Open3D 0.19 official debug export contains observed |TSDF|<0.98 only.
        # Full weights and distant/truncated voxels are NOT exposed by Python.
        xyz=np.asarray(band.points)/factor;gray=np.asarray(band.colors)
        np.savez_compressed(d/'tsdf_observed_band.npz',XYZ_mm=xyz,tsdf_normalized=gray[:,0]*2-1,tsdf_mm=(gray[:,0]*2-1)*c['sdf_trunc_mm'],observed=np.ones(len(xyz),bool))
        save(d/'INTEGRATION.json',dict(name=name,sources=ids,unit='mm mesh / native m internal',config=asset(R/'TSDF_CONFIG.json'),adapter=asset(R/'code/hero_tsdf_adapter.py'),logs=log,elapsed_s=time.monotonic()-t0,vertices=len(P),faces=len(F),observed_band_samples=len(xyz),serialization='actual extracted Mesh + official observed-band TSDF samples + complete masked RGBD replay; Python API does not expose full voxel weights or volume serialization',postprocess='normal calculation only; all extracted vertices/faces retained'))
    return P,F

def single_checks(P,F):
    c=cfg();s=source('G01_004_ref08');a=HEROToTSDFAdapter.from_source(s,c['depth_trunc_mm']);sc=mesh_scene(P,F)
    v,u=np.nonzero(a.valid);uv=np.c_[u,v];z=s['depth'][v,u];X=unproject(z,s['T'],uv,s['Kn']);rt,zrt=vis.project_camera(X,s['Kn'],s['T']);hit,_=cast(sc,uv,s['Kn'],s['T']);err=abs(hit-z);dist=distance(sc,X)
    Pr,Fr=integrate('UNIT_MM_CONTROL',['G01_004_ref08'],unit_mm=True,export=False)
    ab=cKDTree(Pr).query(P)[0];ba=cKDTree(P).query(Pr)[0];unitmax=float(max(ab.max(),ba.max()))
    fids,Xr=face_samples(s);dr=distance(sc,Xr)
    # Empty real-image mask: no fabricated geometry/depth, official integrator must stay empty.
    empty=HEROToTSDFAdapter(s['depth'],a.rgb,np.zeros_like(a.valid,np.uint8),s['Kn'],s['T'],c['depth_trunc_mm']);ev=volume();ev.integrate(empty.rgbd(),empty.intrinsic,empty.w2c_m);empty_ok=len(ev.extract_triangle_mesh().triangles)==0
    b=P.min(0),P.max(0);rawbounds=[s['P'].min(0),s['P'].max(0)]
    g=c['engineering_gate'];checks=dict(raw_XYZ_roundtrip=s['XYZ_roundtrip_mm']<=g['raw_XYZ_mm'],native_resize=s['ancestry_mm']<=g['native_resize_mm'],pixel_roundtrip=float(np.max(abs(rt-uv)))<=g['roundtrip_pixel'],unit_equivalence=unitmax<=g['metric_scale_mesh_Hausdorff_mm'],unknown_zero=bool(np.all(a.depth_m[~a.valid]==0)),empty_mask_empty_mesh=empty_ok,native_first_hit=float(np.isfinite(hit).mean())>=g['single_native_hit_fraction_min'],native_depth_error=float(np.quantile(err,.95))<=g['single_native_depth_p95_mm_max'],point_retention=float((dist<=.2).mean())>=g['point_retention_at_0p2_mm_min'])
    out=dict(checks=checks,engineering_pass=all(checks.values()),native_valid_depth_N=len(X),native_hit_N=int(np.isfinite(hit).sum()),native_hit_fraction=float(np.isfinite(hit).mean()),native_depth_abs_error_mm=stats(err),native_distance_mm=stats(dist),native_retention_at_0p2_mm=float((dist<=.2).mean()),original_face_sample_retention_at_0p2_mm=float((dr<=.2).mean()),raw_face_sample_distance_mm=stats(dr),unit_mm_vs_m_max_bidirectional_vertex_distance_mm=unitmax,pixel_roundtrip_max=float(np.max(abs(rt-uv))),depth_roundtrip_max_mm=float(np.max(abs(zrt-z))),bounds_mm=b,raw_bounds_mm=rawbounds,bounds_center_shift_mm=float(np.linalg.norm((b[0]+b[1]-rawbounds[0]-rawbounds[1])/2)),Ring_bounds_mm=ringmesh().bounds,Ring_unchanged_SHA256=sha(CAD),boundary_and_anatomical_quality='reported separately; no GT')
    save('config/SINGLE_SOURCE_VALIDATION.json',out)
    print('SINGLE_SOURCE_VALIDATION',json.dumps(clean(out)),flush=True)
    # Predeclared extra resolution control only; primary parameters unchanged.
    trigger=out['native_hit_fraction']<.90 or (out['native_depth_abs_error_mm']['p95']or np.inf)>.2
    if trigger and all(checks[k]for k in ['raw_XYZ_roundtrip','native_resize','pixel_roundtrip','unit_equivalence','unknown_zero','empty_mask_empty_mesh']):
        integrate('SINGLE_RESOLUTION_CONTROL',['G01_004_ref08'],voxel_override=.05)
        save('config/RESOLUTION_CONTROL.json',dict(run=True,trigger='predeclared single-source native hit/depth threshold',main_parameters_changed=False))
    else:save('config/RESOLUTION_CONTROL.json',dict(run=False,reason='predeclared discretization trigger absent'))
    assert out['engineering_pass'],'SINGLE_SOURCE_ENGINEERING_FAILED_STOP_BEFORE_MULTI'
    save('config/ADAPTER_INTERFACE_FREEZE.json',dict(status='ENGINEERING_INTERFACE_VERIFIED',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),adapter=asset(R/'code/hero_tsdf_adapter.py'),common=asset(R/'code/common.py'),validation=asset(R/'config/SINGLE_SOURCE_VALIDATION.json'),scientific_parameters_accepted=False,anatomical_quality_accepted=False))

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['single','multi']);args=p.parse_args()
    frozen=load(R/'config/BEFORE_ANY_INTEGRATION.json')
    assert sha(R/'TSDF_CONFIG.json')==frozen['config']['sha256']and sha(R/'VIEW_COVERAGE_SELECTION.csv')==frozen['selection']['sha256']
    if args.stage=='single':
        assert not(R/'local_results/SINGLE/mesh_mm.ply').exists(),'DO_NOT_OVERWRITE_EXISTING_EXPERIMENT'
        P,F=integrate('SINGLE',cfg()['Single']);single_checks(P,F)
    else:
        f=load(R/'config/ADAPTER_INTERFACE_FREEZE.json');assert sha(R/'code/hero_tsdf_adapter.py')==f['adapter']['sha256']and sha(R/'code/common.py')==f['common']['sha256']
        for name in ['G0','G1']:
            assert not(R/'local_results'/name/'mesh_mm.ply').exists(),'DO_NOT_OVERWRITE_EXISTING_EXPERIMENT'
            integrate(name,cfg()[name])
        snapshot('AFTER_OFFICIAL_INTEGRATION')
if __name__=='__main__':main()
