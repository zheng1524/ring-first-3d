"""Post-freeze native 3D audit. Does not optimize or load a nonexistent q_GT."""
from continuous import *
from physics import *
import subprocess,datetime
def samples(V,F,N=6000):
    rng=np.random.default_rng(20261105);areas=trimesh.triangles.area(V[F]);idx=rng.choice(len(F),N,p=areas/areas.sum());uv=rng.random((N,2));a=np.sqrt(uv[:,0]);w=np.c_[1-a,a*(1-uv[:,1]),a*uv[:,1]]
    return (V[F[idx]]*w[:,:,None]).sum(1)
def dimensions(V,F):
    m=trimesh.Trimesh(V,F,process=False);X=V-V.mean(0);vals,vec=np.linalg.eigh(X.T@X/len(X));vec=vec[:,::-1]
    return dict(center_of_mass_mm=m.center_mass,world_extent_mm=np.ptp(V,axis=0),PCA_extent_mm=np.ptp(X@vec,axis=0),PCA_axes=vec,volume_mm3=float(m.volume),area_mm2=float(m.area))
def main():
    assert not (R/'metrics/NATIVE_POSTERIOR.json').exists()
    arms=['ORIGINAL']+(['SUBPIXEL_TARGET']if load(R/'metrics/SYNTHETIC_OBJECTIVE_AUDIT.json')['trigger_single_target_boundary_correction']else[])
    for arm in arms:assert load(R/'metrics'/f'{arm}_FINISHED.json')['finished']
    frozen=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()]
    save('metrics/ALL_PREDICTIONS_FREEZE.json',dict(timestamp=datetime.datetime.now().isoformat(),files=frozen,all_predictions_frozen_before_this_first_native_GT_evaluation=True,GT_selected=False))
    gt=dict(np.load(R/'audit_only/NATIVE_CAD_GT.npz'));VG,FG=gt['V'],gt['F'];GT=scene(VG,FG);body=Body();renderer=Renderer();base=dict(np.load(R/'inputs/BASE_SOURCE_MESH.npz'));V0,F0=base['V'],base['F'];P0=scene(V0,F0);fixed=body.P
    phiGT=signed(GT,fixed);phi0=signed(P0,fixed);oGT=phiGT<0;o0=phi0<0;GTadded=oGT&~o0;GTremoved=o0&~oGT;voxel=float(body.a['h'])**3
    XG=samples(VG,FG);GTdim=dimensions(VG,FG);ref0=signed(P0,V0);dGT=-signed(GT,V0)+ref0
    def gt_visible(X):
        supported=np.zeros(len(X),bool)
        for cid in protocol()['fit_views']:
            d=renderer.data[cid];uv,z=vis.project_camera(X,d['K'],d['T']);inside=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);tz,_=cast(GT,uv,d['K'],d['T']);cz,_=cast(renderer.cad,uv,d['K'],d['T'])
            supported|=inside&d['target'][px[:,1],px[:,0]]&d['known'][px[:,1],px[:,0]]&(abs(z-tz)<.02)&(z<cz)
        return supported
    visibleG=gt_visible(XG);rows=[];perviews=[];traces=[]
    for arm in arms:
        history=load(R/'metrics'/f'{arm}_HISTORY.json')
        for stage in history:
            a=dict(np.load(R/'local_results'/arm/stage['stage']/'MODEL.npz'));V,F=a['V'],a['F'];rt=scene(V,F);X=samples(V,F);distP=abs(signed(GT,X));distG=abs(signed(rt,XG));closest=GT.compute_closest_points(o3d.core.Tensor(X.astype(np.float32)))['points'].numpy();visibleP=gt_visible(closest)
            dm=dimensions(V,F);phi=signed(rt,fixed);occ=phi<0;added=occ&~o0;removed=o0&~occ;errVol=float((occ!=oGT).sum()*voxel)
            dp=-signed(rt,V0)+ref0
            volume=dict(fixed_N=len(fixed),cell_volume_mm3=voxel,method='fixed independent P0 grid occupancy from exact signed distance to actual closed meshes; rectangular quadrature proxy',GT_added_mm3=float(GTadded.sum()*voxel),GT_removed_mm3=float(GTremoved.sum()*voxel),pred_added_mm3=float(added.sum()*voxel),pred_removed_mm3=float(removed.sum()*voxel),added_recovered_mm3=float((added&GTadded).sum()*voxel),removed_recovered_mm3=float((removed&GTremoved).sum()*voxel),wrong_added_mm3=float((added&~GTadded).sum()*voxel),wrong_removed_mm3=float((removed&~GTremoved).sum()*voxel),missed_added_mm3=float((GTadded&~added).sum()*voxel),missed_removed_mm3=float((GTremoved&~removed).sum()*voxel),symmetric_difference_mm3=errVol)
            volume['added_recovery_ratio']=volume['added_recovered_mm3']/volume['GT_added_mm3']if volume['GT_added_mm3']else None;volume['removed_recovery_ratio']=volume['removed_recovered_mm3']/volume['GT_removed_mm3']if volume['GT_removed_mm3']else None
            visdist=np.r_[distG[visibleG],distP[visibleP]];unkdist=np.r_[distG[~visibleG],distP[~visibleP]]
            row=dict(arm=arm,stage=stage['stage'],q=a['q'],dimensions=dm,center_error_mm=float(np.linalg.norm(dm['center_of_mass_mm']-GTdim['center_of_mass_mm'])),relative_volume_error=float((dm['volume_mm3']-GTdim['volume_mm3'])/GTdim['volume_mm3']),relative_area_error=float((dm['area_mm2']-GTdim['area_mm2'])/GTdim['area_mm2']),Chamfer_mm=stats(np.r_[distG,distP]),GT_to_prediction_mm=stats(distG),prediction_to_GT_mm=stats(distP),visible_region_Chamfer_mm=stats(visdist),unknown_region_Chamfer_mm=stats(unkdist),visible_GT_sample_N=int(visibleG.sum()),unknown_GT_sample_N=int((~visibleG).sum()),visible_pred_sample_N=int(visibleP.sum()),unknown_pred_sample_N=int((~visibleP).sum()),fixed_P0_Eulerian_error_mm=stats(dp-dGT),actual_Eulerian_motion_mm=stats(dp),volume=volume,physical=stage['physical'],fit_IoU=float(np.mean([v['full_IoU']for v in stage['per_view']if v['role']=='FIT'])),holdout_IoU=float(np.mean([v['full_IoU']for v in stage['per_view']if v['role']!='FIT'])))
            rows.append(row);perviews.extend(dict(arm=arm,stage=stage['stage'],**v)for v in stage['per_view'])
            np.savez_compressed(R/'audit_only'/f'{arm}_{stage["stage"]}_ERRORS.npz',X_gt=XG,GT_visible=visibleG,GT_distance=distG,X_pred=X,pred_visible=visibleP,pred_distance=distP,V0=V0,F0=F0,GT_Eulerian=dGT,pred_Eulerian=dp)
        records=load(R/'metrics'/f'{arm}_TRACE.json');best=float('inf')
        for t in records:
            improved=t['loss']<best;reason='objective improvement; no physical constraint enforcement'if improved else'line-search candidate not a new best';best=min(best,t['loss']);traces.append(dict(arm=arm,evaluation=t['evaluation'],q=t['q'],loss=t['loss'],new_best=improved,Ring_collision=t['physical']['collision'],reason=reason))
    representation=dict(family='one nonnegative Wendland basis times a single signed amplitude; frozen P0',GT_requires_added_mm3=float(GTadded.sum()*voxel),GT_requires_removed_mm3=float(GTremoved.sum()*voxel),GT_requires_both_signs=bool(GTadded.any()and GTremoved.any()),unavoidable_symmetric_difference_lower_bound_mm3=float(min(GTadded.sum(),GTremoved.sum())*voxel),proof='a<0 can only add occupancy relative to P0; a>0 can only remove. A single signed nonnegative kernel cannot simultaneously correct both native CAD differences. Grid volumes are proxies; sign restriction is analytic.',GT_q='DOES_NOT_EXIST',GT_vertices_outside_independent_domain=int(np.any((VG<fixed.min(0))|(VG>fixed.max(0)),axis=1).sum()))
    # Consistent normal-ray audit; any miss remains NaN rather than filled by GT.
    n=trimesh.Trimesh(V0,F0,process=False).vertex_normals;origins=V0+.8*n;rays=o3d.core.Tensor(np.c_[origins,-n].astype(np.float32))
    z0=P0.cast_rays(rays)['t_hit'].numpy();zg=GT.cast_rays(rays)['t_hit'].numpy();normal=[]
    for arm in arms:
        a=np.load(R/'local_results'/arm/'FINAL/MODEL.npz');rt=scene(a['V'],a['F']);zp=rt.cast_rays(rays)['t_hit'].numpy();valid=np.isfinite(z0)&np.isfinite(zg)&np.isfinite(zp)&(z0<=1.6)&(zg<=1.6)&(zp<=1.6)&(signed(P0,origins)>0)&(signed(GT,origins)>0)&(signed(rt,origins)>0);err=np.full(len(z0),np.nan);np.subtract(zg,zp,out=err,where=valid);normal.append(dict(arm=arm,fixed_N=len(z0),valid_N=int(valid.sum()),missing_N=int((~valid).sum()),error_mm=stats(err)))
        np.savez_compressed(R/'audit_only'/(arm+'_NORMAL_RAYS.npz'),valid=valid,error=err)
    checks=[]
    endpoints=[('P0',base),('GT_native',gt)]+[(arm,dict(np.load(R/'local_results'/arm/'FINAL/MODEL.npz')))for arm in arms]
    cad=dict(np.load(R/'inputs/RING_CAD.npz'))
    for name,a in endpoints:
        inp=R/'audit_only'/(name+'_BLENDER_INPUT.npz');out=R/'metrics'/(name+'_BLENDER_PHYSICAL.json');np.savez_compressed(inp,V=a['V'],F=a['F'],CAD_V=cad['V'],CAD_F=cad['F'])
        p=subprocess.run([BLENDER,'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(PREV/'code/blender_check.py'),'--',str(inp),str(out)],capture_output=True,text=True,timeout=120);(R/'runtime'/(name+'_BLENDER_CHECK.log')).write_text(p.stdout+p.stderr);assert p.returncode==0;checks.append(dict(state=name,**load(out)))
    save('metrics/NATIVE_POSTERIOR.json',dict(GT_identity='unmodified native Blender CAD; not same-kernel control',GT_dimensions=GTdim,stages=rows,representation=representation,normal_rays=normal,Blender_checks=checks,GT_never_used_for_selection=True,visible_definition='GT first-visible surface under the three fit cameras/target Masks/Ring; prediction samples split by nearest GT surface visibility, never by small error',all_surface_denominator_per_direction=6000,all_predictions_frozen=True))
    table('metrics/NATIVE_STAGE_METRICS.csv',rows);table('metrics/NATIVE_PER_VIEW.csv',perviews);table('metrics/CANDIDATE_DECISIONS.csv',traces)
    np.savez_compressed(R/'audit_only/FIXED_OCCUPANCY_AUDIT.npz',P=fixed,GT=oGT,P0=o0)
    print('NATIVE_POSTERIOR_DONE',[(x['arm'],x['stage'],x['fit_IoU'],x['holdout_IoU'],x['Chamfer_mm']['MAE'],x['volume']['symmetric_difference_mm3'])for x in rows if x['stage']in ['P0','FINAL']],representation,flush=True)
if __name__=='__main__':main()
