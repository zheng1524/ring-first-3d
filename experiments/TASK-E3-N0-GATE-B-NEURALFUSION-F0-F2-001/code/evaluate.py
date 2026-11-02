"""Original identity denominators, actual first hits and all original Raw faces."""
from common import *
def evaluate(method,v,stage):
    m=output_mesh(method,v,stage);P=np.asarray(m.vertices);F=np.asarray(m.faces);scene=mesh_scene(P,F)
    rayrows=[];rawrows=[];allarrays={};finite_geometry=bool(len(F)>0 and np.isfinite(P).all())
    for cid in CORE:
        n=native(cid,'V2');current=native(cid,v);ids=n['ids'];uv=n['uv'];z=n['depth'].flat[ids].astype(float)
        hit=cast(scene,uv,n['K'],n['T']);cad=cast(ringscene(),uv,n['K'],n['T'])
        blocked=np.isfinite(cad)&(z>cad+cfg()['evaluation']['CAD_tolerance_mm'])
        available=current['valid'].flat[ids];visible=~blocked
        error=hit-z;finite=np.isfinite(hit)
        d=scene.compute_distance(o3d.core.Tensor(n['X'].astype(np.float32))).numpy()if len(F)else np.full(len(ids),np.inf)
        cat=np.full(len(ids),'MISS',dtype='<U20');cat[blocked]='CAD_OCCLUDED'
        cat[visible&finite&(abs(error)<=.25)]='AGREE';cat[visible&finite&(error<-.25)]='NEAR';cat[visible&finite&(error>.25)]='FAR'
        fused=cid in cfg()['sequences'][stage]
        row=dict(method=method,version=v,stage=stage,source=cid,source_in_fusion=fused,
            role='IN_SAMPLE'if fused else'HELD_OUT_SHARED_HERO_UPSTREAM',fixed_V2_observation_N=len(ids),
            version_available_N=int(available.sum()),version_unavailable_N=int((~available).sum()),CAD_occluded_N=int(blocked.sum()),
            CAD_visible_N=int(visible.sum()),hit_N=int((visible&finite).sum()),miss_N=int((visible&~finite).sum()),
            hit_fraction=float((visible&finite).sum()/max(1,visible.sum())),
            agree_N=int((cat=='AGREE').sum()),near_N=int((cat=='NEAR').sum()),far_N=int((cat=='FAR').sum()),
            agree_fraction_fixed_visible=float((cat=='AGREE').sum()/max(1,visible.sum())),
            depth_error_hit_only_mm=metric(error[visible&finite]),
            point_retention_at_0p25mm=float((d[visible]<=.25).mean())if visible.any()else None,
            native_point_distance_mm=metric(d[visible]))
        rayrows.append(row)
        allarrays[cid+'_native_id']=ids;allarrays[cid+'_hit_mm']=hit;allarrays[cid+'_depth_mm']=z
        allarrays[cid+'_CAD_mm']=cad;allarrays[cid+'_category']=cat;allarrays[cid+'_version_available']=available
        # All Raw faces, their source IDs and original areas; no mesh input substitution.
        raw=original(cid);centers=raw['P'][raw['F']].mean(1)
        dr=scene.compute_distance(o3d.core.Tensor(centers.astype(np.float32))).numpy()if len(F)else np.full(len(centers),np.inf)
        area=raw['area'];near=dr<=.25
        rawrows.append(dict(method=method,version=v,stage=stage,source=cid,original_face_N=len(centers),
            original_area_mm2=float(area.sum()),retained_face_N=int(near.sum()),
            area_retention_at_0p25mm=float(area[near].sum()/area.sum()),face_retention_at_0p25mm=float(near.mean()),distance_mm=metric(dr)))
        allarrays[cid+'_original_face_id']=np.arange(len(centers));allarrays[cid+'_face_distance_mm']=dr
    topology=dict(vertices_N=len(P),faces_N=len(F),area_mm2=float(m.area),is_watertight=bool(m.is_watertight),
        boundary_edge_N=int(np.sum(np.bincount(m.edges_unique_inverse)==1)),
        nonmanifold_edge_N=int(np.sum(np.bincount(m.edges_unique_inverse)>2)),bounds_mm=m.bounds.tolist())
    # Original connectivity and component areas; do not remove any fragment.
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    edges=m.edges_unique
    graph=coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(P),len(P)))
    nc,labels=connected_components(graph,directed=False)
    facecomp=labels[F[:,0]];areas=np.bincount(facecomp,weights=np.asarray(m.area_faces),minlength=nc)
    topology.update(components_N=int(nc),largest_component_area_fraction=float(areas.max()/areas.sum()))
    np.savez_compressed(R/'local_results'/f'{method}_{v}_{stage}_evaluation.npz',**allarrays)
    table(f'{method}_{v}_{stage}_RAYS.csv',rayrows);table(f'{method}_{v}_{stage}_RAW_FACES.csv',rawrows)
    # F0 checks use actual current-input observations, with misses preserved as +inf.
    n=native(CORE[0],v);hit=cast(scene,n['uv'],n['K'],n['T']);cad=cast(ringscene(),n['uv'],n['K'],n['T']);z=n['depth'].flat[n['ids']].astype(float)
    visible=~(np.isfinite(cad)&(z>cad+.002));dist=scene.compute_distance(o3d.core.Tensor(n['X'].astype(np.float32))).numpy()
    errors=np.abs(hit[visible]-z[visible])
    # NumPy linear quantiles can compute inf-inf=NaN across missing rays.
    # Preserve the original denominator and define that quantile as +inf.
    ordered=np.sort(errors);upper=int(np.ceil((len(ordered)-1)*.95))
    p95=float(np.inf if not np.isfinite(ordered[upper]) else np.quantile(errors,.95))
    values=dict(native_CAD_visible_N=int(visible.sum()),native_hit_fraction=float(np.isfinite(hit[visible]).mean()),
        native_depth_error_p95_including_misses_mm=p95,
        native_depth_error_p95_status='FINITE'if np.isfinite(p95)else'INFINITE_DUE_TO_MISSED_RAYS',
        native_point_retention_0p25mm=float((dist[visible]<=.25).mean()))
    g=cfg()['F0_gate'];checks=dict(nonempty_finite_geometry=finite_geometry,
        native_hit=values['native_hit_fraction']>=g['native_CAD_visible_V6_hit_fraction_min'],
        depth_error=p95<=g['native_CAD_visible_depth_error_p95_mm_max'],
        point_retention=values['native_point_retention_0p25mm']>=g['native_CAD_visible_point_retention_at_0p25mm_min'])
    result=dict(method=method,version=v,stage=stage,topology=topology,rays=rayrows,Raw_faces=rawrows,
        ref08_current_input_checks=checks,ref08_current_input_values=values,
        F0_pass=all(checks.values())if stage=='F0'else None,physical_accuracy='NOT_CERTIFIED',
        GT_read=False,mesh_geometry_postprocessed=False)
    save(f'{method}_{v}_{stage}_METRICS.json',result)
    if stage=='F0':result['progression_ok']=bool(result['F0_pass'])
    else:
        prev='F'+str(int(stage[1:])-1);prior=load(R/f'{method}_{v}_{prev}_METRICS.json')
        current_by={r['source']:r for r in rayrows}
        loss=[r['agree_fraction_fixed_visible']-current_by[r['source']]['agree_fraction_fixed_visible']for r in prior['rays']if r['source_in_fusion']]
        new=next(r for r in rayrows if r['source']==cfg()['sequences'][stage][-1])
        p=new['depth_error_hit_only_mm']['p95']
        result['progression_ok']=bool(finite_geometry and max(loss,default=0)<=.10 and p is not None and p<=1.)
        result['previous_view_max_agreement_drop']=max(loss,default=0)
    save(f'{method}_{v}_{stage}_METRICS.json',result)
    print('GEOMETRY_GATE',method,v,stage,clean(dict(checks=checks,values=values,progression_ok=result['progression_ok'])),flush=True)
    return result
