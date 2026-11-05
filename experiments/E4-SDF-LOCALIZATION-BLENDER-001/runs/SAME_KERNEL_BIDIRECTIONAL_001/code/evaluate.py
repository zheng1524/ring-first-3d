"""Post-prediction geometry audit, same operator for GT and prediction."""
from model import *
from renderer import Renderer
from original_objective import bind_objective
import datetime,subprocess
sys.path.insert(0,'/home/liu/ring_first_3d_e4_pmgr_r1/experiments/TASK-E4-PMGR-R1/runtime/packages')
import fcl
def vertex_area(V,F):
    out=np.zeros(len(V));a=trimesh.triangles.area(V[F])/3
    for j in range(3):np.add.at(out,F[:,j],a)
    return out
def fcl_object(V,F):
    m=fcl.BVHModel();m.beginModel(len(V),len(F));m.addSubModel(np.asarray(V,float),np.asarray(F,np.int32));m.endModel();return fcl.CollisionObject(m)
def physical(V,F,cad,cad_obj):
    o=fcl_object(V,F);n=fcl.collide(o,cad_obj,fcl.CollisionRequest(),fcl.CollisionResult());gap=fcl.distance(o,cad_obj,fcl.DistanceRequest(),fcl.DistanceResult())if not n else-1.;m=trimesh.Trimesh(V,F,process=False)
    return dict(triangle_collision=bool(n),full_triangle_gap_mm=float(gap),closed=m.is_watertight,winding=m.is_winding_consistent,components=len(m.split(only_watertight=False)),Euler_number=int(m.euler_number),volume_mm3=float(m.volume))
def volume_quadrature(body,qgt,qpred):
    """Same conforming tets and float32 nodal fields as actual DMTet extraction."""
    T=body.tets.numpy();P=body.V.numpy().astype(float);xyz=P[T];tetvol=abs(np.einsum('ij,ij->i',xyz[:,1]-xyz[:,0],np.cross(xyz[:,2]-xyz[:,0],xyz[:,3]-xyz[:,0])))/6
    aa=.5854101966249685;bb=.1381966011250105;B=np.full((4,4),bb);np.fill_diagonal(B,aa)
    def occupied(q):
        v=body.values(q).astype(np.float32).astype(float);return (v[T]@B.T)<0
    zero=np.r_[np.zeros(3),0.];occ0=occupied(zero);occgt=occupied(qgt);occp=occupied(qpred)
    def vol(mask):return float(np.sum(tetvol[:,None]*mask)/4)
    changedgt=occgt!=occ0;changedp=occp!=occ0;correct=(occgt==occp)&changedgt&changedp
    return dict(method='fixed 4-point symmetric quadrature of occupancy indicators; approximation, not exact intersection volume',tets_N=len(T),fixed_quadrature_points_N=4*len(T),GT_added_mm3=vol(occgt&~occ0),GT_removed_mm3=vol(occ0&~occgt),pred_added_mm3=vol(occp&~occ0),pred_removed_mm3=vol(occ0&~occp),changed_volume_IoU=vol(changedgt&changedp)/max(vol(changedgt|changedp),1e-15),correct_direction_volume_IoU=vol(correct)/max(vol(changedgt|changedp),1e-15),off_target_changed_volume_mm3=vol(changedp&~changedgt),missed_target_changed_volume_mm3=vol(changedgt&~changedp))
def main():
    assert load(R/'metrics/FIT_FINISHED.json')['finished']
    prediction=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()]
    freeze=R/'metrics/PREDICTION_FREEZE.json'
    if freeze.exists():assert all(sha(x['path'])==x['sha256']for x in load(freeze)['files'])
    else:save('metrics/PREDICTION_FREEZE.json',dict(files=prediction,before_this_first_GT_read=True,timestamp=datetime.datetime.now().isoformat(),GT_selection=False))
    gt=dict(np.load(R/'audit_only/TARGET_GT.npz'));qgt=gt['q'];body=Body();renderer=Renderer();history=load(R/'metrics/FIT_HISTORY.json');initial=dict(np.load(R/'local_results/INITIAL/MODEL.npz'));V=initial['V'];F=initial['F'];weights=vertex_area(V,F);rt0=scene(V,F);s0=signed(rt0,V);rtgt=scene(gt['V'],gt['F']);dgt=-signed(rtgt,V)+s0;changed=abs(dgt)>.01;sign=1. if qgt[3]<0 else-1.;support=np.linalg.norm(V-qgt[:3],axis=1)<=body.radius
    gtcenter=np.average(V,axis=0,weights=weights*abs(dgt));cad=dict(np.load(R/'inputs/RING_CAD.npz'));cad_obj=fcl_object(cad['V'],cad['F']);rows=[];perview=[]
    normals=trimesh.Trimesh(V,F,process=False).vertex_normals;origin=V+.8*normals;rays=o3d.core.Tensor(np.c_[origin,-normals].astype(np.float32))
    def normal_hits(rt):
        z=rt.cast_rays(rays)['t_hit'].numpy().astype(float);valid=np.isfinite(z)&(z<=1.6)&(signed(rt,origin)>0);return z,valid
    z0,v0=normal_hits(rt0);zg,vg=normal_hits(rtgt);dg_ray=np.full(len(V),np.nan);np.subtract(z0,zg,out=dg_ray,where=v0&vg);normalrows=[]
    for h in history:
        cp=dict(np.load(R/'local_results'/h['stage']/'MODEL.npz'));rt=scene(cp['V'],cp['F']);dp=-signed(rt,V)+s0;active=abs(dp)>.01;cent=np.average(V,axis=0,weights=weights*abs(dp))if np.sum(weights*abs(dp))>1e-10 else None;inter=np.sum(weights[changed&active]);union=np.sum(weights[changed|active]);quality=normals_quality(cp['V'],cp['F']);ph=physical(cp['V'],cp['F'],cad,cad_obj);z,v=normal_hits(rt);valid=v0&vg&v;dr=np.full(len(V),np.nan);np.subtract(z0,z,out=dr,where=valid)
        normalrows.append(dict(stage=h['stage'],fixed_N=len(V),valid_N=int(valid.sum()),miss_N=int((~valid).sum()),GT_region_fixed_N=int(changed.sum()),GT_region_valid_N=int((changed&valid).sum()),GT_directional_peak_mm=float(np.nanmax(sign*dg_ray[valid])),pred_directional_peak_mm=float(np.nanmax(sign*dr[valid])),error_mm=stats((dr-dg_ray)[valid]),GT_region_error_mm=stats((dr-dg_ray)[valid&changed])))
        q=np.asarray(h['q']);center_err=q[:3]-qgt[:3];err=dp-dgt
        row=dict(stage=h['stage'],iteration=h['iteration'],q=q,parameter_center_error_mm=float(np.linalg.norm(center_err))if abs(q[3])>1e-10 else None,center_X_error_mm=float(center_err[0])if abs(q[3])>1e-10 else None,center_Y_error_mm=float(center_err[1])if abs(q[3])>1e-10 else None,center_Z_error_mm=float(center_err[2])if abs(q[3])>1e-10 else None,GT_center_mm=qgt[:3],GT_sdf_amplitude_mm=float(qgt[3]),pred_sdf_amplitude_mm=float(q[3]),actual_update_centroid_mm=cent,GT_update_centroid_mm=gtcenter,update_centroid_error_mm=float(np.linalg.norm(cent-gtcenter))if cent is not None else None,GT_region_N=int(changed.sum()),fixed_surface_N=len(V),GT_region_area_mm2=float(weights[changed].sum()),pred_region_area_mm2=float(weights[active].sum()),region_IoU=float(inter/max(union,1e-15)),direction_agreement=float(np.sum(weights[changed]*(dp[changed]*dgt[changed]>0))/max(np.sum(weights[changed]),1e-15)),GT_directional_peak_mm=float(np.max(sign*dgt)),pred_directional_peak_mm=float(np.max(sign*dp)),wrong_direction_peak_mm=float(np.max(-sign*dp)),GT_region_error_mm=stats(err[changed]),all_error_mm=stats(err),non_target_motion_mm=stats(dp[~changed]),non_target_changed_area_mm2=float(weights[~changed&active].sum()),outside_kernel_motion_mm=stats(dp[~support]),quality=quality,Ring=ph,fit_IoU=float(np.mean([x['full_IoU']for x in h['per_view']if x['role']=='FIT'])),holdout_IoU=float(np.mean([x['full_IoU']for x in h['per_view']if x['role']!='FIT'])),objective=h['objective'])
        row['relative_physical_peak_error']=abs(row['pred_directional_peak_mm']-row['GT_directional_peak_mm'])/max(row['GT_directional_peak_mm'],1e-15);rows.append(row);perview.extend(dict(stage=h['stage'],**x)for x in h['per_view'])
        np.savez_compressed(R/'audit_only'/(h['stage']+'_SURFACE.npz'),V=V,F=F,GT=dgt,pred=dp,error=err,GT_changed=changed,pred_changed=active,weights=weights)
        np.savez_compressed(R/'audit_only'/(h['stage']+'_NORMAL_RAYS.npz'),valid=valid,GT=dg_ray,pred=dr)
        if h['stage']in ['INITIAL','FINAL']:
            for c in renderer.views:
                pred,z,face=renderer.project(rt,c['id']);np.savez_compressed(R/'audit_only'/(h['stage']+'__'+c['id']+'_PROJECTION.npz'),pred=pred,depth_mm=z,target=renderer.data[c['id']]['target'],known=renderer.data[c['id']]['known'])
    final=rows[-1];qfinal=np.asarray(final['q']);zero=np.r_[np.zeros(3),0.];phi0=body.values(zero).astype(np.float32);phifinal=body.values(qfinal).astype(np.float32);phigt=body.values(qgt).astype(np.float32)
    quad=volume_quadrature(body,qgt,qfinal);Vinit=rows[0]['quality']['volume_mm3'];Vgt=float(trimesh.Trimesh(gt['V'],gt['F'],process=False).volume);Vfinal=final['quality']['volume_mm3']
    volume=dict(initial_mesh_mm3=Vinit,GT_mesh_mm3=Vgt,final_mesh_mm3=Vfinal,GT_signed_volume_change_mm3=Vgt-Vinit,pred_signed_volume_change_mm3=Vfinal-Vinit,GT_node_delta_min=float((phigt-phi0).min()),GT_node_delta_max=float((phigt-phi0).max()),pred_node_delta_min=float((phifinal-phi0).min()),pred_node_delta_max=float((phifinal-phi0).max()),prediction_occupancy_subset_of_initial=bool(np.all(phifinal>=phi0)),prediction_occupancy_superset_of_initial=bool(np.all(phifinal<=phi0)),quadrature=quad)
    volume['genuine_volume_deletion']=bool(np.all(phifinal>=phi0)and Vfinal<Vinit-1e-6 and quad['pred_removed_mm3']>1e-6)
    # User-requested single GT objective substitution, after the prediction freeze.
    objective,objective_source=bind_objective(body,renderer);Lgt,parts_gt,_=objective(qgt);Lf,parts_final,_=objective(qfinal);seed=np.asarray(load(R/'metrics/MASK_ONLY_INITIALIZATION.json')['q']);Ls,parts_seed,_=objective(seed)
    assert abs(Lf-load(R/'metrics/FIT_FINISHED.json')['loss'])<1e-12
    gt_metrics=[renderer.metrics(rtgt,c['id'])[0]for c in renderer.views];threshold=max(.002,.1*abs(Lgt));trace=load(R/'metrics/OBJECTIVE_TRACE.json');dist=np.array([np.linalg.norm(np.asarray(t['q'])[:3]-qgt[:3])for t in trace]);GT_better=Lf-Lgt>threshold
    diag=dict(GT_loss=float(Lgt),final_loss=float(Lf),start_loss=float(Ls),final_minus_GT=float(Lf-Lgt),clearly_better_threshold=threshold,GT_clearly_better=bool(GT_better),GT_loss_parts=parts_gt,final_loss_parts=parts_final,start_loss_parts=parts_seed,GT_forward_metrics=gt_metrics,objective_source=objective_source,prediction_frozen_before_GT_substitution=True,no_new_optimizer_or_parameter_search=True,trace_evaluations=len(trace),closest_visited_center_error_mm=float(dist.min()),visited_centers_within_0p1mm_N=int((dist<.1).sum()),visited_centers_within_0p5mm_N=int((dist<.5).sum()),initial_center_error_mm=float(np.linalg.norm(seed[:3]-qgt[:3])),initial_Z_error_mm=float(seed[2]-qgt[2]))
    if GT_better:diag['interpretation']='GT is clearly superior under the unchanged objective; inspect initialization, explored parameter region and local/numerical search. This alone does not prove a unique cause.'
    else:diag['interpretation']='GT is not clearly superior under this sampled contour objective despite the forward projection gate. Inspect contour sampling, pixel convention/loss bias and discretization; do not change the loss in this run.'
    p=protocol()['evaluation_thresholds'];gates=dict(fit_Mask_improved=final['fit_IoU']>rows[0]['fit_IoU'],center_error=final['parameter_center_error_mm'] is not None and final['parameter_center_error_mm']<=p['center_error_mm'],centroid_error=final['update_centroid_error_mm'] is not None and final['update_centroid_error_mm']<=p['centroid_error_max_mm'],direction=final['direction_agreement']>=.95,physical_peak=final['relative_physical_peak_error']<=p['relative_peak_error_max'],non_target=final['non_target_motion_mm']['p95']<=p['wrong_region_displacement_p95_mm'],roughness=final['quality']['normal_angle_deg']['p95']<=rows[0]['quality']['normal_angle_deg']['p95']+p['normal_angle_p95_growth_limit_deg'],closed_connected=all(x['quality']['closed']and x['quality']['components']==1 for x in rows),Ring_no_collision=all(not x['Ring']['triangle_collision']for x in rows))
    if R.name=='B_contraction':gates['genuine_volume_deletion']=volume['genuine_volume_deletion']
    save('metrics/GEOMETRY_EVALUATION.json',dict(case=R.name,definition='same signed nearest-surface-distance change on the common initial DMTet mesh; positive outward, negative inward',stages=rows,per_view=perview,gates=gates,all_numeric_gates_pass=all(gates.values()),GT_audit_only_after_prediction_freeze=True))
    save('metrics/VOLUME_VALIDATION.json',volume);save('metrics/GT_OBJECTIVE_DIAGNOSTIC.json',diag);save('metrics/NORMAL_RAY_VALIDATION.json',dict(fixed_N=len(V),rows=normalrows,operator='same initial vertex normals, origins X+0.8n, directions -n; missing values NaN without fallback'))
    table('metrics/ROUND_GEOMETRY.csv',rows);table('metrics/PER_VIEW_METRICS.csv',perview)
    # Independent Blender EXACT checks at initial, GT and final endpoints.
    bchecks=[]
    for name,data in [('INITIAL',initial),('TARGET',gt),('FINAL',dict(np.load(R/'local_results/FINAL/MODEL.npz')))]:
        inp=R/'audit_only'/(name+'_BLENDER_INPUT.npz');out=R/'metrics'/(name+'_BLENDER.json');np.savez_compressed(inp,V=data['V'],F=data['F'],CAD_V=cad['V'],CAD_F=cad['F']);proc=subprocess.run([BLENDER,'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(PREV/'code/blender_check.py'),'--',str(inp),str(out)],capture_output=True,text=True,timeout=120);(R/'runtime'/(name+'_BLENDER.log')).write_text(proc.stdout+proc.stderr);assert proc.returncode==0;bchecks.append(dict(stage=name,**load(out)))
    save('metrics/BLENDER_PHYSICAL_AUDIT.json',dict(passed=all(x['EXACT_intersection_volume_mm3']<=1e-8 for x in bchecks),checks=bchecks))
    imm=[dict(path=x['path'],unchanged=sha(x['path'])==x['sha256'])for x in load(R/'metrics/IMPLEMENTATION_FREEZE.json')['files']];assert all(x['unchanged']for x in imm);save('metrics/IMMUTABILITY.json',dict(passed=True,checks=imm))
    print('CASE_AUDITED',R.name,gates,'GTloss',Lgt,'final',Lf,'center',final['parameter_center_error_mm'],'volume',Vfinal-Vinit,flush=True)
if __name__=='__main__':main()
