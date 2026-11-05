"""Read-only fixed-denominator comparisons and physical/evidence audit."""
from run import *
from mesh_checks import self_intersections
from copanalysis import inspect_coplanar
import subprocess,datetime
def absolute(x):
    z=stats(x);z['median_absolute']=float(np.median(abs(x)))if len(x)else None;return z
def main():
    assert load(R/'metrics/RUN_FINISHED.json')['finished'];data=Data();hist=load(R/'metrics/EVOLUTION_HISTORY.json');stages=[x['stage']for x in hist];stages+=['FINAL'];rows=[];comparison=[];joint=[];checks=[]
    a=np.load(R/'local_results/INITIAL/FIELD.npz');g=Field(a['origin'],a['shape'],float(a['h']));phi0=a['phi'];e=Evolution(g,phi0,data);col=Collision('G01_004')
    for stage in stages:
        q=np.load(R/'local_results'/stage/'FIELD.npz');V=q['V'];F=q['F'];phi=q['phi'];m=trimesh.Trimesh(V,F,process=False);rt=mesh_scene(V,F);z=load(R/'metrics'/(stage+'.json'))
        for x in z['per_source']:
            o=obs(x['source']);ar=np.load(R/'local_results'/stage/(x['source']+'_EVAL.npz'));h=ar['hit'];ph=ar['pair_hit'];pair=o['pairs'][ph];r=dict(stage=stage,**x);r['first_depth_mm']=absolute(ar['z'][h]-o['z'][h]);r['relative_depth_mm']=absolute(ar['z'][pair[:,0]]-ar['z'][pair[:,1]]-o['delta'][ph]);r['HERO_distance_mm']=absolute(ar['distance']);rows.append(r)
        vv=signed(rt,a['V']);exp=int((vv<-.005).sum());shrink=int((vv>.005).sum());ang=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',m.face_normals[m.face_adjacency[:,0]],m.face_normals[m.face_adjacency[:,1]]),-1,1)))
        comparison.append(dict(stage=stage,volume_mm3=m.volume,area_mm2=m.area,V=len(V),F=len(F),closed=m.is_watertight,consistent=m.is_winding_consistent,components=len(m.split(only_watertight=False)),symmetric_P0_drift_mm=z['initial_surface_drift_mm'],initial_surface_expanded_N=exp,initial_surface_contracted_N=shrink,initial_surface_test_N=len(vv),normal_angle_deg=absolute(ang),Ring_gap_mm=z['Ring']['distance_mm'],objective=z['objective'],protected_HERO=z['protected_HERO_mm'],geometry=z['geometry']))
    for cid in data.ids:
        o=obs(cid);arrays={st:dict(np.load(R/'local_results'/st/(cid+'_EVAL.npz')))for st in stages};common=np.logical_and.reduce([x['pair_hit']for x in arrays.values()]);pairs=o['pairs'][common]
        for st,x in arrays.items():
            ee=x['z'][pairs[:,0]]-x['z'][pairs[:,1]]-o['delta'][common];joint.append(dict(source=cid,role='FIT'if cid in data.fit else'UPDATE_HOLDOUT',stage=st,fixed_pairs_N=256,all_stages_common_N=int(common.sum()),**absolute(ee)))
    # Evidence classification is evaluation only, does not create or trim the final mesh.
    q=np.load(R/'local_results/FINAL/FIELD.npz');V=q['V'];F=q['F'];rt=mesh_scene(V,F);support=[];blocks=[]
    for cid in data.ids:
        s=source(cid);uv,z=vis.project_camera(V,s['K'],s['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);hit,_=cast(rt,uv,s['K'],s['T']);cad,_=cast(ringscene('G01_004'),uv,s['K'],s['T']);dist=cKDTree(obs(cid)['X']).query(V)[0];good=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)&(s['labels'][px[:,1],px[:,0]]==1)&(abs(z-hit)<.1)&(z<=cad)&(dist<=.75);support.append(good);blocks.append(GATE[cid]['block'])
    support=np.asarray(support);parts=sum(np.any(support[np.array(blocks)==b],axis=0)for b in set(blocks));obsface=np.any(support,axis=0)[F].sum(1)>=2;multiface=(parts[F]>=2).sum(1)>=2;area=trimesh.Trimesh(V,F,process=False).area_faces;np.savez_compressed(R/'local_results/FINAL/OBSERVATION_EVIDENCE.npz',vertex_support=support,partition_count=parts,observed_face=obsface,multiview_face=multiface,inferred_face=~obsface)
    evidence=dict(total_area_mm2=float(area.sum()),observed_proxy_area_mm2=float(area[obsface].sum()),multiview_proxy_area_mm2=float(area[multiface].sum()),inferred_or_insufficient_area_mm2=float(area[~obsface].sum()),definition='2/3 face vertices pass original Polyp label, actual first visibility/CAD, <=.75mm same-source fixed HERO proximity; uncalibrated proxy; not physical truth',fit_only_sources=data.fit,validation_sources_used_for_posthoc_classification_only=data.validation)
    for name in ['INITIAL',load(R/'metrics/MIDDLE.json')['stage']if (R/'metrics/MIDDLE.json').exists()else'INITIAL','FINAL']:
        ar=np.load(R/'local_results'/name/'FIELD.npz');si=self_intersections(ar['V'],ar['F']);mes=trimesh.Trimesh(ar['V'],ar['F'],process=False);narrow=inspect_coplanar(ar['V'],ar['F'])if si['coplanar_candidates']else[];checks.append(dict(stage=name,closed=mes.is_watertight,outward_positive_volume=mes.volume>0,signs=signed(mesh_scene(ar['V'],ar['F']),np.array([mes.center_mass,mes.center_mass+[100,0,0]])),Ring=col.check(ar['V'],ar['F']),coplanar_narrow_phase=narrow,coplanar_unresolved_N=sum(x['resolution']=='UNRESOLVED_POSITIVE_AREA'for x in narrow),**si))
    frozen=load(R/'assets_index/FROZEN_INPUTS.json')['files'];checksums=[dict(path=x['path'],unchanged=sha(x['path'])==x['sha256'])for x in frozen];assert all(x['unchanged']for x in checksums)
    source_checks=[]
    for x in load(R/'metrics/IMPLEMENTATION_FREEZE.json')['files']:source_checks.append(dict(path=x['path'],unchanged=sha(x['path'])==x['sha256']))
    assert all(x['unchanged']for x in source_checks)
    first=hist[0];last=load(R/'metrics/FINAL.json');fs=[x for x in first['per_source']if x['source']in data.validation];ls=[x for x in last['per_source']if x['source']in data.validation];maskratio=np.mean([x['fixed_Mask_loss']for x in ls])/np.mean([x['fixed_Mask_loss']for x in fs]);hitratio=sum(x['hit_N']for x in ls)/sum(x['hit_N']for x in fs);log=load(R/'metrics/UPDATE_LOG.json');validH=all(x['geometry']['protected_HERO_abs_mm']['maximum']<=max(e.protect_tol)+1e-6 for x in log if x['accepted']);accepted=sum(x['accepted']for x in log)
    physical=all(not c['Ring']['collision']and c['intersections']==0 and c['coplanar_unresolved_N']==0 and c['closed']for c in checks)and last['Blender']['EXACT_intersection_volume_mm3']<=1e-8
    gates=dict(actual_expansion_and_contraction=comparison[-1]['initial_surface_expanded_N']>0 and comparison[-1]['initial_surface_contracted_N']>0,at_least_3_accepted=accepted>=3,training_objective_improved=last['objective']['total']<first['objective']['total'],protected_HERO_contract=validH,physical_mesh_checks=physical,update_holdout_Mask_ratio_le_1p05=maskratio<=1.05,update_holdout_coverage_ratio_ge_0p98=hitratio>=.98)
    save('metrics/FINAL_AUDIT.json',dict(gates=gates,all_numeric_gates_pass=all(gates.values()),validation_Mask_ratio=maskratio,validation_native_hit_ratio=hitratio,asset_checks=checksums,implementation_checks=source_checks,physical_checks=checks,full_triangle_continuous_path_certified=False,accepted_endpoints_checked=True,no_GT=True,historical_measurement_fallback=0,target_cases=1,numerical_output_cases=1,scientific_accuracy='NOT_EVALUABLE',unknown_shape_truth='NOT_EVALUABLE',no_ablation_no_FFD_no_GPU=True,scope_stopped=True))
    table('metrics/PER_SOURCE_METRICS.csv',rows);table('metrics/STAGE_COMPARISON.csv',comparison);table('metrics/COMMON_PAIR_COMPARISON.csv',joint);save('metrics/EVALUATION.json',dict(stages=comparison,per_source=rows,common_pairs=joint,evidence=evidence));save('metrics/FINAL_EVIDENCE.json',evidence)
    fullrows=[];u,v=np.meshgrid(np.arange(640),np.arange(360));uv=np.c_[u.ravel(),v.ravel()]
    display_stages=['INITIAL',load(R/'metrics/MIDDLE.json')['stage'],'FINAL']
    for stage in display_stages:
        q=np.load(R/'local_results'/stage/'FIELD.npz');rt=mesh_scene(q['V'],q['F'])
        for cid in data.ids:
            s=source(cid);d=data.views[cid];z,_=cast(rt,uv,s['K'],s['T']);cz,_=cast(ringscene('G01_004'),uv,s['K'],s['T']);pred=(np.isfinite(z)&(z>0)&(z<=cz)).reshape(360,640);target=s['labels']==1;known=~np.repeat(np.repeat(d['unknown'],2,axis=0),2,axis=1)
            pp=contour(pred);tt=contour(target);pp=pp[known[pp[:,1].astype(int),pp[:,0].astype(int)]];tt=tt[known[tt[:,1].astype(int),tt[:,0].astype(int)]];dd=np.r_[cKDTree(pp).query(tt)[0],cKDTree(tt).query(pp)[0]]
            fullrows.append(dict(stage=stage,source=cid,role='FIT'if cid in data.fit else'UPDATE_HOLDOUT',full_original_Mask_N=int(target.sum()),full_original_hit_N=int((pred&target).sum()),full_original_miss_N=int((~pred&target).sum()),full_original_IoU=float((pred&target).sum()/max(1,(pred|target).sum())),symmetric_known_IoU=float((pred&target&known).sum()/max(1,((pred|target)&known).sum())),known_N=int(known.sum()),known_contour_original_px=absolute(dd)))
            np.savez_compressed(R/'local_results'/stage/(cid+'_FULL_PROJECTION.npz'),depth_mm=z.reshape(360,640),cad_depth_mm=cz.reshape(360,640),pred=pred,target=target,known=known)
    table('metrics/FULL_ORIGINAL_MASK_METRICS.csv',fullrows);save('metrics/FULL_ORIGINAL_MASK_METRICS.json',fullrows)
    # Reconstruct the failed proposal only for diagnosis. It never replaces the safe output.
    rejected=[x for x in log if not x['accepted']]
    diag=[]
    if rejected:
        it=max(x['iteration']for x in rejected);bi=max([x['iteration']for x in log if x['accepted']and x['iteration']<it],default=0);base='ACCEPTED_%02d'%bi if bi else'INITIAL';delta=np.load(R/'local_results'/('iter_%02d_PROPOSAL.npz'%it))['delta'];q=np.load(R/'local_results'/base/'FIELD.npz');oldrt=mesh_scene(q['V'],q['F'])
        for alpha in protocol()['line_search']:
            vv,ff=g.mesh(q['phi']+alpha*delta);m=trimesh.Trimesh(vv,ff,process=False);dist=oldrt.compute_distance(o3d.core.Tensor(vv.astype(np.float32))).numpy();worst=np.argsort(dist)[-8:];components=m.split(only_watertight=False);path=R/'local_results'/('REJECTED_iter%02d_alpha%s_mm.ply'%(it,str(alpha)));m.export(path)
            diag.append(dict(iteration=it,alpha=alpha,base_stage=base,reason=next((x['reasons']for x in rejected if x['iteration']==it and x['alpha']==alpha),['SCALE_NOT_TRIED_DIAGNOSTIC_ONLY']),candidate_only_not_final=True,components=[dict(V=len(c.vertices),F=len(c.faces),volume_mm3=c.volume,bounds_mm=c.bounds)for c in components],largest_new_vertex_distance_mm=float(dist.max()),worst_points_mm=vv[worst],phi_at_worst_old=g.value(q['phi'],vv[worst]),field_change_at_worst=g.value(alpha*delta,vv[worst]),mesh=asset(path)))
    save('metrics/REJECTED_CANDIDATE_DIAGNOSTIC.json',diag)
    files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()];save('assets_index/LOCAL_RESULTS.json',dict(root=str(R),units='mm except *_m.glb in meters',files=files,uploaded_large_data=False))
    print('ANALYZED',gates,'holdout',maskratio,hitratio,flush=True)
if __name__=='__main__':main()
