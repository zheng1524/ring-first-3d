"""Preserve initial failure; locate representation loss before any multi fusion.
Correction of validation implementation: mesh Hausdorff uses surface distance,
not nearest vertex distance. Frozen numerical thresholds remain unchanged.
"""
from run_tsdf import *
def main():
    first=load(R/'config/SINGLE_SOURCE_VALIDATION.json');save('config/SINGLE_FIRST_ATTEMPT_FAILURE.json',first)
    s=source('G01_004_ref08');c=cfg();a=HEROToTSDFAdapter.from_source(s,c['depth_trunc_mm']);primary=output_mesh('SINGLE');sc=mesh_scene(primary.vertices,primary.faces)
    Pr,Fr=integrate('UNIT_MM_CONTROL_SURFACE',['G01_004_ref08'],unit_mm=True,export=False);sr=mesh_scene(Pr,Fr)
    ab=distance(sr,primary.vertices);ba=distance(sc,Pr);unitmax=float(max(ab.max(),ba.max()))
    # Mandatory single allowed predeclared resolution contrast, primary output kept.
    Pc,Fc=integrate('SINGLE_RESOLUTION_CONTROL',['G01_004_ref08'],voxel_override=.05);control=mesh_scene(Pc,Fc)
    v,u=np.nonzero(a.valid);uv=np.c_[u,v];z=s['depth'][v,u];X=unproject(z,s['T'],uv,s['Kn']);labels=cv2.resize(s['labels'],(640,352),interpolation=cv2.INTER_NEAREST)
    edge=cv2.distanceTransform((labels==1).astype(np.uint8),cv2.DIST_L2,5)[v,u]
    result={};rows=[]
    for name,scene in [('SINGLE',sc),('SINGLE_RESOLUTION_CONTROL',control)]:
        h,_=cast(scene,uv,s['Kn'],s['T']);hit=np.isfinite(h);err=abs(h-z);d=distance(scene,X)
        # Censored metric: missed rays remain infinity; separately report finite-hit residual.
        kth=int(np.ceil(.95*len(err)))-1;fullp95=float(np.sort(err)[kth])
        checks=dict(unit_equivalence_surface=unitmax<=c['engineering_gate']['metric_scale_mesh_Hausdorff_mm'],native_first_hit=hit.mean()>=.90,native_depth_error_full_denominator=fullp95<=.2,point_retention=(d<=.2).mean()>=.90)
        result[name]=dict(checks=checks,pass_=all(checks.values()),native_valid_N=len(h),hit_N=int(hit.sum()),hit_fraction=float(hit.mean()),miss_N=int((~hit).sum()),finite_hit_depth_error_mm=stats(err),full_denominator_depth_p95_mm=fullp95,full_denominator_p95_is_infinite=not np.isfinite(fullp95),retention_at_0p2_mm=float((d<=.2).mean()),near_mask_boundary_miss_N=int(((~hit)&(edge<=2)).sum()),interior_miss_N=int(((~hit)&(edge>2)).sum()),miss_xyz=stats(d[~hit]))
        for label,vv in [('within2_native_pixels_boundary',edge<=2),('interior',edge>2)]:rows.append(dict(mesh=name,stratum=label,input_N=int(vv.sum()),hit_N=int((hit&vv).sum()),miss_N=int((~hit&vv).sum()),retained_at_0p2_mm_N=int(((d<=.2)&vv).sum())))
    save('config/SINGLE_DIAGNOSIS.json',dict(unit_surface_distance_mm=stats(np.r_[ab,ba]),unit_surface_max_mm=unitmax,original_vertex_only_control_was_not_mesh_Hausdorff=True,thresholds_changed=False,results=result))
    table('SINGLE_BOUNDARY_DIAGNOSIS.csv',rows)
    save('config/RESOLUTION_CONTROL.json',dict(run=True,trigger='primary native first hit <0.90 as predeclared',voxel_mm=.05,sdf_trunc_mm=.4,main_parameters_changed=False))
    print(json.dumps(clean(result)),flush=True)
    # Algebra and surface fidelity qualify the adapter, not ray coverage of TSDF at open edges.
    # Never relabel failed primary/contrast acceptance. Decision deferred to evidence report.
if __name__=='__main__':main()
