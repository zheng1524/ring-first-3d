"""Freeze ALL optimizer outputs before any native GT read; no fitting here."""
from model import *
from continuous import *
from physics import physical
from audit_helpers import samples,dimensions,gradient_norm
import subprocess,datetime
def main():
    assert not (R/'metrics/POSTERIOR.json').exists();assert load(R/'metrics/S1_FINISHED.json')['finished'];stages=['S1']
    eligible=load(R/'metrics/KERNEL_SELECTION.json')['eligible']
    if eligible:
        assert load(R/'metrics/S2_FINISHED.json')['finished'];stages+=['S2']
        if load(R/'metrics/CENTER_RELEASE_GATE.json')['released']:
            assert load(R/'metrics/S3_FINISHED.json')['finished'];stages+=['S3']
    b=Body()
    if not(R/'local_results/P0').exists():b.save('P0',np.zeros(6))
    files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()];configs=[asset(p)for p in sorted((R/'config').glob('*.json'))]
    freeze=R/'metrics/ALL_OPTIMIZED_PREDICTIONS_FREEZE.json'
    if freeze.exists():
        for x in load(freeze)['files']+load(freeze)['configs']:assert sha(x['path'])==x['sha256']
    else:save('metrics/ALL_OPTIMIZED_PREDICTIONS_FREEZE.json',dict(files=files,configs=configs,timestamp=datetime.datetime.now().isoformat(),before_first_native_GT_read=True,GT_selection=False,stages=stages))
    # Native asset is reused byte-for-byte; no Blender re-export or target rendering.
    gtpath=REPO/'experiments/TASK-E4-2D3D-OBSERVABILITY-001/audit_only/NATIVE_CAD_GT.npz';gt=dict(np.load(gtpath));VG,FG=gt['V'],gt['F'];GT=scene(VG,FG);GTdim=dimensions(VG,FG)
    base=dict(np.load(R/'inputs/BASE_SOURCE_MESH.npz'));V0,F0=base['V'],base['F'];P0=scene(V0,F0);ref0=signed(P0,V0);dGT=-signed(GT,V0)+ref0;XG=samples(VG,FG);renderer=Renderer();points=np.load(R/'inputs/EVAL_POINTS.npz');P=points['P'];w=float(points['weight']);GTocc=signed(GT,P)<0;P0occ=signed(P0,P)<0;addedGT=GTocc&~P0occ;removedGT=P0occ&~GTocc
    def vol(mask):return float(mask.sum()*w)
    def visible(X):
        valid=np.zeros(len(X),bool)
        for cid in protocol()['fit_views']:
            d=renderer.data[cid];uv,z=vis.project_camera(X,d['K'],d['T']);inside=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);tz,_=cast(GT,uv,d['K'],d['T']);cz,_=cast(renderer.cad,uv,d['K'],d['T']);valid|=inside&d['known'][px[:,1],px[:,0]]&d['target'][px[:,1],px[:,0]]&(abs(tz-z)<.02)&(z<cz)
        return valid
    visGT=visible(XG);rows=[];perview=[];endpoints=[];previous_stage_occ=P0occ;cache={}
    def metric(name,V,F,q,reference_occ):
        rt=scene(V,F);m=trimesh.Trimesh(V,F,process=False);valid=m.is_watertight and m.is_winding_consistent and len(m.split(only_watertight=False))==1;XP=samples(V,F);dp=GT.compute_distance(o3d.core.Tensor(XP.astype(np.float32))).numpy();dg=rt.compute_distance(o3d.core.Tensor(XG.astype(np.float32))).numpy();near=GT.compute_closest_points(o3d.core.Tensor(XP.astype(np.float32)))['points'].numpy();visP=visible(near);dim=dimensions(V,F)
        if valid:
            occ=signed(rt,P)<0;motion=-signed(rt,V0)+ref0;volume=dict(occupancy_mm3=vol(occ),symmetric_difference_mm3=vol(occ!=GTocc),added_from_P0_mm3=vol(occ&~P0occ),removed_from_P0_mm3=vol(P0occ&~occ),added_from_previous_stage_mm3=vol(occ&~reference_occ),removed_from_previous_stage_mm3=vol(reference_occ&~occ),GT_added_recovered_mm3=vol(occ&~P0occ&addedGT),GT_removed_recovered_mm3=vol(P0occ&~occ&removedGT),GT_added_recovery=vol(occ&~P0occ&addedGT)/max(vol(addedGT),1e-15),GT_removed_recovery=vol(P0occ&~occ&removedGT)/max(vol(removedGT),1e-15))
        else:occ=None;motion=np.full(len(V0),np.nan);volume=dict(symmetric_difference_mm3=None,reason='open/nonmanifold/multicomponent; signed occupancy NOT_EVALUABLE')
        view=[subpixel_metrics(renderer,V,F,c['id'])for c in renderer.views];localcenters=b.kernel_centers(q)if len(q)>6 else None;row=dict(name=name,q=q,center_parameters_mm=b.c0+q[:3],semiaxes_mm=b.a0*np.exp(q[3:6]),local_amplitudes_mm=q[6:8]if len(q)>6 else[],local_centers_mm=localcenters,Mesh_dimensions=dim,center_of_mass_error_mm=float(np.linalg.norm(dim['center_of_mass_mm']-GTdim['center_of_mass_mm'])),Chamfer_mm=stats(np.r_[dp,dg]),GT_to_prediction_mm=stats(dg),prediction_to_GT_mm=stats(dp),visible_Chamfer_mm=stats(np.r_[dg[visGT],dp[visP]]),unknown_Chamfer_mm=stats(np.r_[dg[~visGT],dp[~visP]]),GT_visible_N=int(visGT.sum()),GT_unknown_N=int((~visGT).sum()),actual_Eulerian_motion_mm=stats(motion),fixed_P0_Eulerian_error_mm=stats(motion-dGT),volume=volume,physical=physical(V,F),field_gradient=gradient_norm(b,q),fit_IoU=float(np.mean([x['full_IoU']for x in view if x['role']=='FIT'])),holdout_IoU=float(np.mean([x['full_IoU']for x in view if x['role']!='FIT'])))
        np.savez_compressed(R/'audit_only'/(name.replace('/','__')+'_ERRORS.npz'),V0=V0,F0=F0,GT_motion=dGT,pred_motion=motion,GT_samples=XG,GT_distance=dg,pred_samples=XP,pred_distance=dp,GT_visible=visGT,pred_visible=visP)
        perview.extend(dict(name=name,**x)for x in view);return row,occ
    p0row,p0oc=metric('P0',V0,F0,np.zeros(6),P0occ);rows.append(p0row);endpoints.append(p0row)
    for stage in stages:
        history=load(R/'metrics'/(stage+'_HISTORY.json'));last_occ=None
        for rec in history:
            a=dict(np.load(R/'local_results'/stage/rec['checkpoint']/'MODEL.npz'));name=stage+'/'+rec['checkpoint'];row,occ=metric(name,a['V'],a['F'],a['q'],previous_stage_occ);rows.append(row)
            if rec['checkpoint']=='FINAL':endpoints.append(row);last_occ=occ
        if last_occ is not None:previous_stage_occ=last_occ
        print('EVALUATED',stage,endpoints[-1]['fit_IoU'],endpoints[-1]['Chamfer_mm']['MAE'],endpoints[-1]['volume'],flush=True)
    # Algebraic fixed-parameter components, NOT new optimized experiment arms.
    components=[]
    for stage in stages[1:]:
        q=np.array(load(R/'metrics'/(stage+'_FINISHED.json'))['q']);items=[('GLOBAL_ONLY',q[:6]),('EXPANSION_ONLY',q.copy()),('SHRINK_ONLY',q.copy())];items[1][1][7]=0.;items[2][1][6]=0.
        globalocc=None
        for tag,qq in items:
            V,F=b.mesh(qq);row,occ=metric('COMPONENT_'+stage+'_'+tag,V,F,qq,P0occ);L,parts=objective(b,renderer,qq,False);row.update(actual_fit_objective=L,loss_parts=parts,diagnostic_only_no_optimization=True)
            if tag=='GLOBAL_ONLY':globalocc=occ
            if occ is not None and globalocc is not None:row['local_add_vs_same_global_mm3']=vol(occ&~globalocc);row['local_remove_vs_same_global_mm3']=vol(globalocc&~occ)
            components.append(row);np.savez_compressed(R/'audit_only'/('COMPONENT_'+stage+'_'+tag+'.npz'),q=qq,V=V,F=F)
        full=next(x for x in endpoints if x['name']==stage+'/FINAL');a=np.load(R/'local_results'/stage/'FINAL/MODEL.npz');fullocc=signed(scene(a['V'],a['F']),P)<0;full['local_add_vs_same_global_mm3']=vol(fullocc&~globalocc);full['local_remove_vs_same_global_mm3']=vol(globalocc&~fullocc)
    # Independent endpoint Ring and nonadjacent self-intersection checks.
    cad=dict(np.load(R/'inputs/RING_CAD.npz'));checks=[]
    sources=[('NATIVE_GT',gt),('P0',base)]+[(s,dict(np.load(R/'local_results'/s/'FINAL/MODEL.npz')))for s in stages]
    for label,a in sources:
        inp=R/'audit_only'/(label+'_BLENDER_INPUT.npz');np.savez_compressed(inp,V=a['V'],F=a['F'],CAD_V=cad['V'],CAD_F=cad['F']);out=R/'metrics'/(label+'_BLENDER_RING.json');so=R/'metrics'/(label+'_BLENDER_SELF.json')
        for script,target in [(PREV/'code/blender_check.py',out),(R/'code/blender_self_check.py',so)]:
            proc=subprocess.run([BLENDER,'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(script),'--',str(inp),str(target)],capture_output=True,text=True,timeout=180);(R/'runtime'/(label+'_'+target.stem+'.log')).write_text(proc.stdout+proc.stderr);assert proc.returncode==0
        checks.append(dict(label=label,Ring=load(out),self=load(so)))
    save('metrics/POSTERIOR.json',dict(stages=stages,GT_source=asset(gtpath),GT_mesh_dimensions=GTdim,GT_vertices_outside_fixed_metric_domain=int(np.any((VG<points['lo'])|(VG>points['hi']),axis=1).sum()),fixed_space_N=len(P),fixed_space_weight_mm3=w,GT_added_vs_P0_mm3=vol(addedGT),GT_removed_vs_P0_mm3=vol(removedGT),GT_occupancy_volume_mm3=vol(GTocc),fixed_surface_samples_per_direction=6000,all_checkpoints=rows,endpoints=endpoints,components=components,Blender_checks=checks,all_predictions_frozen_before_GT=True,no_component_reoptimization=True,Gate_B_C_D_not_run=True))
    table('metrics/ENDPOINT_METRICS.csv',endpoints);table('metrics/ROUND_METRICS.csv',rows);table('metrics/PER_VIEW_METRICS.csv',perview);table('metrics/COMPONENT_METRICS.csv',components)
    print('POSTERIOR_COMPLETE',[(x['name'],x['fit_IoU'],x['holdout_IoU'],x['Chamfer_mm']['MAE'],x['volume']['symmetric_difference_mm3'])for x in endpoints],flush=True)
if __name__=='__main__':main()
