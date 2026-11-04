"""Read-only geometry evaluation after GLOBAL_STOP; never calls an optimizer."""
from run import Model,Observations,Collision,P0Constraints,evaluate,volume,shape_quality
from inputs import *
from scipy.spatial import cKDTree

def restore(scene):
    h=dict(np.load(R/'local_results'/(scene+'_HISTORICAL_P0.npz')));c=dict(np.load(R/'local_results'/(scene+'_P0_CANDIDATE.npz')))
    m=Model(p0(scene,protocol()['scenes'][scene]['initial']));b=dict(np.load(R/'inputs'/(scene+'_CONSERVATIVE_BASIS.npz')))
    m.set_reference(c['q'],b['phi']);m.frequency=b['frequency'];return h,c,m

def raster_distance(scene,V,F,cid):
    met,ar=evaluate(scene,V,F,cid);s=source(cid);band=cv2.dilate((s['labels']==2).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    a=contour(ar['pred']);b=contour(s['labels']==1)
    a=a[~band[a[:,1].astype(int),a[:,0].astype(int)]];b=b[~band[b[:,1].astype(int),b[:,0].astype(int)]]
    d=np.r_[cKDTree(b).query(a)[0],cKDTree(a).query(b)[0]]if len(a)and len(b)else np.array([])
    return met,stats(d)

def fixed_feature_distance(mapping,V,cid,target):
    e=mapping['edges'];t=mapping['fraction'];P=V[e[:,0]]*(1-t[:,None])+V[e[:,1]]*t[:,None];s=source(cid);uv=vis.project_camera(P,s['K'],s['T'])[0]
    return float(np.r_[cKDTree(target).query(uv)[0],cKDTree(uv).query(target)[0]].mean())

def main():
    scene='G01_004';h,c,m=restore(scene);co=Collision(scene);ob=Observations(scene,m)
    # Reconstruct final P0 checks, NOT optimizer trace, from preserved arrays.
    cm=Model(p0(scene,protocol()['scenes'][scene]['initial']));cert=P0Constraints(cm,co);g=cert.both(c['q'])[0]
    oldev=[evaluate(scene,h['V'],h['F'],cid)[0]for cid in ob.ids];newev=[evaluate(scene,c['V'],c['F'],cid)[0]for cid in ob.ids]
    dr=np.array([b['IoU']-a['IoU']for a,b in zip(oldev,newev)])
    save('metrics/'+scene+'_P0_FEASIBILITY_RECONSTRUCTED.json',dict(status='P0_FEASIBLE',status_evidence='formal run passed gate and entered P1; all final checks recomputed here',scope='final endpoint reconstruction only; no repeated solve',trace=None,optimizer_iterations=None,optimizer_success=None,audit_failure='Original feasibility JSON overwritten by P0 stage filename collision. Intermediate feasibility trace not recoverable; no rerun performed.',old_p=h['q'],new_p=c['q'],old_evaluations=oldev,new_evaluations=newev,old_collision=co.check(h['V'],h['F'],True),new_collision=co.check(c['V'],c['F'],True),old_Blender=load(R/'metrics'/(scene+'_HISTORICAL_P0_BLENDER.json')),new_Blender=load(R/'metrics'/(scene+'_CONSERVATIVE_P0_BLENDER.json')),analytic_clearance_lower_bound_mm=float(g[:-1].min()+cert.target-cert.cover),CAD_cover_radius_mm=cert.cover,CAD_certificate_sample_N=len(cert.points),mean_IoU_change=float(dr.mean()),worst_IoU_change=float(dr.min()),volume_ratio=volume(c['V'],c['F'])/volume(h['V'],h['F']),axis_ratios=np.exp(c['q'][6:9]-h['q'][6:9]),center_shift_mm=float(np.linalg.norm(c['q'][:3]-h['q'][:3])),reasons=[]))
    updates=load(R/'metrics/ALL_UPDATE_PROPOSALS.json');rows=[];summary=[];totals=[]
    for i,u in enumerate(updates):
        cp=dict(np.load(u['snapshot']));q=cp['q_before'];qp=cp['q_proposed'];before=ob.linearize(q,None,True);after=ob.linearize(qp,None,True)
        assert abs(before['E']-ob.linearize(q,None)['E'])<1e-10
        assert np.max(abs(m.vertices(q)-cp['before_V']))<1e-10
        q9=q.copy();q9[:9]=qp[:9];qn=q.copy();qn[9:]=qp[9:]
        summary.append(dict(proposal=i+1,case=scene,stage=u['stage'],iteration=u['iteration'],trial=u['trial'],accepted=u['accepted'],reasons=u['reasons'],before_CORE_objective=u['before_objective'],proposed_CORE_objective=u['candidate_objective'],all_source_before_objective=before['E'],all_source_proposed_objective=after['E'],max_actual_move_mm=u['candidate_max_vertex_move_mm'],live9_only_max_move_mm=float(np.linalg.norm(m.vertices(q9)-cp['before_V'],axis=1).max()),spectral_only_max_move_mm=float(np.linalg.norm(m.vertices(qn)-cp['before_V'],axis=1).max()),Ring_gap_mm=u['collision']['distance_mm'],QP_failed='FEASIBLE_DIRECTION_QP_FAILED'in u['reasons']))
        for a,b in zip(before['per_view'],after['per_view']):
            cid=a['source'];met0,rd0=raster_distance(scene,cp['before_V'],cp['F'],cid);met1,rd1=raster_distance(scene,cp['proposed_V'],cp['F'],cid)
            mp=before['mapping'][cid];target=ob.targets[cid]['boundary'];fixed0=fixed_feature_distance(mp,cp['before_V'],cid,target);fixed1=fixed_feature_distance(mp,cp['proposed_V'],cid,target)
            rows.append(dict(proposal=i+1,source=cid,accepted=u['accepted'],dynamic_contour_before_px=a['contour_mean_px'],dynamic_contour_after_px=b['contour_mean_px'],dynamic_delta_px=b['contour_mean_px']-a['contour_mean_px'],before_edge_sample_N=a['predicted_boundary_N'],after_edge_sample_N=b['predicted_boundary_N'],fixed_feature_before_px=fixed0,fixed_feature_after_px=fixed1,fixed_feature_delta_px=fixed1-fixed0,raster_contour_before_px=rd0['MAE'],raster_contour_after_px=rd1['MAE'],raster_contour_delta_px=rd1['MAE']-rd0['MAE'],IoU_before=met0['IoU'],IoU_after=met1['IoU'],native_fixed_N=512,native_hit_before=met0['native_hit_N'],native_hit_after=met1['native_hit_N'],relative_depth_MAE_before=met0['relative_depth_mm']['MAE'],relative_depth_MAE_after=met1['relative_depth_mm']['MAE'],role='POSTHOC_TRAINING_DIAGNOSTIC_NOT_GATE_REPLACEMENT'))
        print('DIAGNOSTIC',i+1,flush=True)
    table('metrics/UPDATE_SUMMARY.csv',summary);table('metrics/PER_VIEW_REJECTION_ANALYSIS.csv',rows);save('metrics/POSTHOC_DIAGNOSTICS.json',dict(updates=summary,per_view=rows,formal_gate_unchanged=True,no_new_optimization=True,qualification_not_changed=True))
    stages=[('HISTORICAL',h),('P0',c),('LAST_SAFE',dict(np.load(R/'local_results'/scene/'LAST_SAFE.npz')))];evrows=[]
    for name,cp in stages:
        for cid in ob.ids:
            met,r=raster_distance(scene,cp['V'],cp['F'],cid);evrows.append(dict(case=scene,stage=name,**met,raster_contour_px=r))
    table('metrics/STAGE_SOURCE_METRICS.csv',evrows)
    save('metrics/POST_STOP_OUTPUT_FIX.json',dict(problem='conservative_p0 and save_stage(P0) used same metrics filename',impact='single-solve intermediate trace lost; historical and accepted endpoint arrays, all update candidates and full acceptance logs preserved',remedy='run.py output-only path changed to _P0_FEASIBILITY.json for reproduction; final feasibility metrics recomputed without optimization into separate RECONSTRUCTED file',frozen_executed_commit='eea53d7',formal_optimization_repeated=False,thresholds_changed=False))

if __name__=='__main__':main()
