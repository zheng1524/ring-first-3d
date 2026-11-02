"""Bounded F0 failure diagnosis only; no inference, mesh edits or new views."""
from common import *
def main():
    assert not load(R/'NN_V6_F0_METRICS.json')['F0_pass']
    save('STAGE_STATUS.json',dict(F0='COMPLETED_GEOMETRY_FAIL',F1='NOT_RUN_F0_STOP',F2='NOT_RUN_F0_STOP',F3_F5='NOT_AUTHORIZED',reverse='NOT_AUTHORIZED',training='NOT_PERFORMED',optimizer_steps=0,GPU_pipeline_forwards=2,reason='V6 F0 current-input p95=0.935719mm > preregistered0.20mm; V2 F0 is bounded control, not a bypass'))
    summary=[];cases=[]
    for method in ['NN','O3D']:
        for v in ['V6','V2']:
            m=output_mesh(method,v,'F0');scene=mesh_scene(m.vertices,m.faces)
            evals=np.load(R/'local_results'/f'{method}_{v}_F0_evaluation.npz')
            flags=None
            if method=='NN':
                rr=list(csv.DictReader((R/f'NN_{v}_F0_FACE_VALIDITY.csv').open()))
                flags=np.array([a['unknown_boundary_proxy']=='True'for a in rr])
            for cid in CORE:
                n=native(cid,'V2');ids=n['ids'];hit=evals[cid+'_hit_mm'];z=evals[cid+'_depth_mm'];cat=evals[cid+'_category'];available=evals[cid+'_version_available'];eligible=cat!='CAD_OCCLUDED';finite=np.isfinite(hit)
                rays=vis.camera_rays(n['uv'],n['K'],n['T']).astype(np.float32)
                casted=scene.cast_rays(o3d.core.Tensor(rays));faceid=casted['primitive_ids'].numpy().astype(np.int64)
                first_boundary=np.zeros(len(ids),bool)
                if flags is not None:first_boundary[finite]=flags[faceid[finite]]
                error=hit-z;bad=eligible&finite&(abs(error)>.25)
                errors=abs(error[eligible]);ordered=np.sort(errors);upper=int(np.ceil((len(ordered)-1)*.95));q95=float(np.inf if not np.isfinite(ordered[upper])else np.quantile(errors,.95))
                row=dict(method=method,version=v,source=cid,fixed_V2_visible_N=int(eligible.sum()),
                    hit_N=int((eligible&finite).sum()),miss_N=int((eligible&~finite).sum()),
                    depth_error_p95_fixed_with_misses_mm=q95,
                    p95_status='FINITE'if np.isfinite(q95)else'INFINITE_DUE_TO_MISSES',
                    near_first_layer_N=int((eligible&finite&(error<-.25)).sum()),far_first_layer_N=int((eligible&finite&(error>.25)).sum()),
                    bad_first_layer_N=int(bad.sum()),
                    unknown_boundary_first_hit_N=int((eligible&finite&first_boundary).sum())if flags is not None else None,
                    bad_first_layer_on_unknown_boundary_N=int((bad&first_boundary).sum())if flags is not None else None,
                    unknown_boundary_face_N=int(flags.sum())if flags is not None else None,
                    all_output_faces_N=len(m.faces),all_output_faces_preserved=True)
                summary.append(row)
                # Save exact first-hit faces for replay, without changing geometry.
                np.savez_compressed(R/'local_results'/f'{method}_{v}_{cid}_first_faces.npz',native_id=ids,face_id=faceid,first_unknown_boundary=first_boundary)
                if method=='NN'and v=='V6':
                    legal=np.flatnonzero(eligible&finite&available)
                    worst=int(legal[np.argmax(abs(error[legal]))])
                    # One explicit worst-current-input ray per reference; auxiliary only.
                    result=scene.list_intersections(o3d.core.Tensor(rays[worst:worst+1]))
                    layers=np.sort(result['t_hit'].numpy());layers=np.unique(np.round(layers,6))
                    cases.append(dict(source=cid,native_id=int(ids[worst]),native_u=int(n['uv'][worst,0]),native_v=int(n['uv'][worst,1]),
                        source_HERO_depth_mm=float(z[worst]),output_first_hit_mm=float(hit[worst]),error_mm=float(error[worst]),
                        intersection_depths_mm=layers.tolist(),first_face_unknown_boundary=bool(first_boundary[worst]),
                        selection='max absolute finite first-hit error among current V6 available non-CAD observations; no output changes'))
    table('F0_FAILURE_DIAGNOSIS.csv',summary);save('F0_WORST_REAL_RAYS.json',cases)
    # Correct SI-unit GLB exports from unchanged millimetre PLY; no mesh cleanup.
    glbs=[]
    for method in ['NN','O3D']:
        for v in ['V6','V2']:
            m=output_mesh(method,v,'F0');m.vertices=np.asarray(m.vertices)*.001
            p=R/'meshes'/f'{method}_{v}_F0_m.glb';m.export(p);glbs.append(asset(p))
    save('provenance/GLB_UNITS.json',dict(delivered_GLBs='metres as glTF specifies; PLYs are millimetres; vertex/face IDs unchanged',files=glbs,initial_infer_mm_glb='local diagnostic only; not delivered or used for any evaluation'))
    print('F0_BOUNDED_DIAGNOSIS',clean(summary),flush=True)
if __name__=='__main__':main()
