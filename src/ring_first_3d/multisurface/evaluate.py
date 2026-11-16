"""Frozen-denominator independent material, overlap, model and section evaluation."""
import json
import numpy as np
from scipy.spatial.transform import Rotation
from ..synthetic.io import fetch,save_json,outputs
from ..policy.contracts import require
from .geometry import transform,scene,closest,summary,sample_mesh,mesh_sections,plane_coordinates,point_segment_distance,vertex_normals
from .fusion import body_chart


def fixed_stats(values):
    a=np.asarray(values);ok=np.isfinite(a);return dict(target_N=int(len(a)),numeric_N=int(ok.sum()),failed_N=int((~ok).sum()),**summary(a))


def curve_samples(segments,n=400):
    if not len(segments):return np.full((n,segments.shape[-1]if segments.ndim==3 else 2),np.nan)
    length=np.linalg.norm(segments[:,1]-segments[:,0],axis=1);total=length.sum()
    if total<=0:return np.full((n,segments.shape[-1]),np.nan)
    q=(np.arange(n)+.5)/n*total;cs=np.cumsum(length);ids=np.searchsorted(cs,q);start=np.r_[0.,cs[:-1]][ids];u=(q-start)/np.maximum(length[ids],1e-15)
    return segments[ids,0]+u[:,None]*(segments[ids,1]-segments[ids,0])


def section_metrics(V,F,reference,cfg):
    rows=[]
    for spec in cfg['sections']:
        axis,off=spec['axis'],spec['offset_mm'];GT=reference[(axis,off)];pred=plane_coordinates(mesh_sections(V,F,axis,off),axis)
        targets=curve_samples(GT);sources=curve_samples(pred);a=point_segment_distance(targets,pred);b=point_segment_distance(sources,GT)
        rows.append(dict(axis=axis,offset_mm=off,GT_segments=len(GT),model_segments=len(pred),GT_to_model_mm=fixed_stats(a),model_to_GT_mm=fixed_stats(b),GT_coverage_within0p2mm=float((a<=cfg['coverage_threshold_mm']).mean()),
            status='GT_PATCH_NOT_CUT_BY_PLANE'if not len(GT)else'UNMATCHED_MODEL_SECTION'if not len(pred)else'EVALUABLE',
            intersection='All actual triangle/plane intersection segments; arclength samples are evaluation quadrature only, never display replacement'))
    return rows


def model_metrics(V,F,gt,gt_scene,targets,observed,body_arm,cfg,seed,ownership=None):
    near,_,face=closest(scene(V,F),targets);GTerr=np.linalg.norm(targets-near,axis=1)
    points,ids,bary=sample_mesh(V,F,cfg['evaluation_model_samples'],seed);Q,norm,idx=closest(gt_scene,points);err=np.linalg.norm(points-Q,axis=1)
    tri=V[F[ids]];ownnorm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);ownnorm/=np.maximum(np.linalg.norm(ownnorm,axis=1)[:,None],1e-12)
    angles=np.rad2deg(np.arccos(np.clip(abs((ownnorm*norm).sum(1)),0,1)))
    result=dict(arm=body_arm,GT_to_model_mm=fixed_stats(GTerr),model_to_GT_mm=fixed_stats(err),bidirectional_mm=fixed_stats(np.r_[GTerr,err]),
        GT_observed_region=dict(error_mm=fixed_stats(GTerr[observed]),coverage=float((GTerr[observed]<=cfg['coverage_threshold_mm']).mean())),
        GT_unobserved_region=dict(error_mm=fixed_stats(GTerr[~observed]),coverage=float((GTerr[~observed]<=cfg['coverage_threshold_mm']).mean())),
        GT_unique_coverage=float((GTerr<=cfg['coverage_threshold_mm']).mean()),GT_unique_covered_N=int((GTerr<=cfg['coverage_threshold_mm']).sum()),fixed_GT_target_N=len(targets),
        local_unoriented_normal_error_deg=fixed_stats(angles),no_GT_rigid_alignment=True,vertices=len(V),faces=len(F))
    if ownership is not None:
        for tag,flag in [('observed_faces',ownership['face_observed'][ids]),('completion_faces',ownership['face_completion'][ids]),('transition_faces',~(ownership['face_observed'][ids]|ownership['face_completion'][ids]))]:
            result[tag]=dict(sampled_area_fraction=float(flag.mean()),model_to_GT_mm=fixed_stats(err[flag]))
        predicted_observed=ownership['face_observed'][face]
        result['ownership_GT_visibility_confusion']=dict(true_observed_pred_observed=int((observed&predicted_observed).sum()),true_observed_pred_completion=int((observed&~predicted_observed).sum()),true_unobserved_pred_observed=int((~observed&predicted_observed).sum()),true_unobserved_pred_completion=int((~observed&~predicted_observed).sum()))
    return result


def check_injection(task,root,conditions):
    truth=json.loads(fetch(root,'G0_views_noise','private/INJECTION_TRUTH.json').read_text());rows=[]
    for cond in conditions:
        poses={r['id']:r for r in json.loads(fetch(root,'G0_views_noise','public/conditions/'+cond+'/ESTIMATED_POSES.json').read_text())}
        for video,info in truth[cond].items():
            bias_name=task['fusion']['conditions'][cond]['bias'][video];angle,tr=task['fusion']['bias_parameters'][bias_name];D=np.eye(4);D[:3,:3]=Rotation.from_euler('y',angle,degrees=True).as_matrix();D[0,3]=tr
            vectors=[]
            for f in info['frames']:
                q=np.array(f['noise_vector_deg_mm']);N=np.eye(4);N[:3,:3]=Rotation.from_rotvec(np.deg2rad(q[:3])).as_matrix();N[:3,3]=q[3:];C=np.asarray(f['TruePose']);estimated=D@C@N
                require(np.allclose(estimated,poses[f['id']]['estimated_C'],atol=1e-10),'INJECTION_PROTOCOL','Independent EstimatedPose=Bias@True@Noise')
                camera_mesh=np.load(fetch(root,'G0_views_noise','public/camera_meshes/'+f['id']+'.npz'));actual=np.load(fetch(root,'G0_views_noise','public/conditions/'+cond+'/'+f['id']+'.npz'))
                require(np.allclose(actual['V'],transform(camera_mesh['V'],estimated),atol=1e-10)and np.array_equal(actual['F'],camera_mesh['F']),'MESH_SOURCE','Independent depth-grid backprojection with estimated camera')
                vectors.append(q)
            q=np.array(vectors);require(np.max(abs(q.mean(0)))<1e-12,'NOISE_MEAN','Centered zero-mean draw')
            require(np.allclose(np.cov(q,rowvar=False),info['empirical_covariance_ddof1'],atol=1e-12),'NOISE_COVARIANCE','Actual empirical covariance')
            rows.append(dict(condition=cond,video=video,mean_deg_mm=q.mean(0).tolist(),std_deg_mm=q.std(0,ddof=1).tolist(),covariance=np.cov(q,rowvar=False).tolist(),actual_frame_count=len(q)))
    return rows,truth


def registration_metrics(task,root,stage):
    cfg=task['fusion'];pred=json.loads(fetch(root,stage,'PREDICTIONS_FROZEN.json').read_text());index=[r for r in json.loads(fetch(root,'G0_views_noise','public/FRAME_INDEX.json').read_text())if r['role']=='FIT'];overlaps=json.loads(fetch(root,'G0_views_noise','private/OVERLAP_TARGETS.json').read_text());rows=[]
    local_references={}
    for d in index:
        gtlocal=np.load(fetch(root,'G0_views_noise','private/'+d['id']+'_truth.npz'));cammesh=np.load(fetch(root,'G0_views_noise','public/camera_meshes/'+d['id']+'.npz'));references={}
        for spec in cfg['sections']:references[spec['axis'],spec['offset_mm']]=plane_coordinates(mesh_sections(gtlocal['Ptrue'],cammesh['F'],spec['axis'],spec['offset_mm']),spec['axis'])
        local_references[d['id']]=references
    for r in pred['rows']:
        key=r['key'];conditions=r['condition'];out=dict(key=key,condition=conditions,arm=r['arm'],method=r['method'],kind=r['kind'],tolerance_mm=r['tolerance_mm'],status=r['status']);frames=[];corrected={};camera={a['id']:a for a in json.loads(fetch(root,'G0_views_noise','public/conditions/'+conditions+'/ESTIMATED_POSES.json').read_text())}
        for d in index:
            truth=np.load(fetch(root,'G0_views_noise','private/'+d['id']+'_truth.npz'));Ptrue=truth['Ptrue'];den=len(Ptrue)
            if r['status']=='NUMERIC':
                actual=np.load(fetch(root,stage,key+'/'+d['id']+'.npz'));P=actual['V'];base=np.load(fetch(root,'G0_views_noise','public/conditions/'+conditions+'/'+d['id']+'.npz'));X=np.asarray(r['surface_corrections'][d['id']]);require(np.allclose(P,transform(base['V'],X),atol=1e-10)and np.array_equal(actual['F'],base['F']),'MESH_RIGIDITY','Output all vertices must be actual rigid source Mesh')
                corrected[d['id']]=P;error=np.linalg.norm(P-Ptrue,axis=1)
                e=actual['F'][:,[0,1]];edge=np.linalg.norm(P[e[:,0]]-P[e[:,1]],axis=1)-np.linalg.norm(base['V'][e[:,0]]-base['V'][e[:,1]],axis=1);intrinsic=float(abs(edge).max())
            else:error=np.full(den,np.nan);intrinsic=None
            axial=((Ptrue-truth['true_C'][:3,3])@truth['true_C'][:3,:3])[:,2]
            cuts=[]
            if r['status']=='NUMERIC':
                cuts=section_metrics(P,actual['F'],local_references[d['id']],cfg)
            frames.append(dict(id=d['id'],video=d['video'],material_error_mm=fixed_stats(error),material_coverage_within0p2mm=float((error<=cfg['material_success_threshold_mm']).mean()),median_absolute_relative_error_to_true_axial_depth=float(np.nanmedian(error/axial))if np.isfinite(error).any()else None,intrinsic_edge_length_change_max_mm=intrinsic,local_material_patch_sections=cuts))
        pairrows=[]
        for p in overlaps:
            target=np.load(fetch(root,'G0_views_noise','private/overlaps/'+p['key']+'.npz'));n=len(target['source_vertex'])
            if r['status']=='NUMERIC'and n:
                first=corrected[p['first']][target['source_vertex']];C=np.asarray(camera[p['second']]['estimated_C']);X=np.asarray(r['surface_corrections'][p['second']]);second=transform(target['target_camera_points'],X@C);error=np.linalg.norm(first-second,axis=1)
            else:error=np.full(n,np.nan)
            pairrows.append(dict(first=p['first'],second=p['second'],family=p['family'],fixed_target_N=n,error_mm=fixed_stats(error),reference='Fixed GT-visible material-overlap target; no method-dependent distance rejection'))
        out.update(frames=frames,overlap_pairs=pairrows,mean_frame_material_MAE_mm=float(np.mean([f['material_error_mm']['MAE']for f in frames]))if r['status']=='NUMERIC'else None,optimizer_success=r.get('details',{}).get('optimizer_success',False),no_GT_alignment=True)
        rows.append(out)
    return rows,pred


def smoke(task,attempt):
    root=attempt.parents[1];checks,truth=check_injection(task,root,['C0','C1']);rows,pred=registration_metrics(task,root,'G3_smoke_predict')
    inputs=truth['C1']['005']['frames'];require(max(r['actual_vertex_displacement_max_mm']for r in inputs)>.1,'SMOKE_INJECTION','Actual independent Mesh layers must move')
    require(all(r['actual_vertex_displacement_max_mm']==0 for v in truth['C0'].values()for r in v['frames']),'C0_GATE','No C0 injected motion')
    moved=[r for r in pred['rows']if r['condition']=='C1'and r['method']in ['ICP','BODY_VIDEO','BODY_HIER']and r['status']=='NUMERIC'and max(r['maximum_surface_motion_mm'].values())>.01]
    require(moved,'SMOKE_OPTIMIZATION','Real independent surface optimization must change the full Mesh')
    save_json(attempt/'SMOKE_METRICS.json',dict(rows=rows,injection_checks=checks,scientific_accuracy_is_not_assumed=True,actual_full_mesh_motion_verified=True))
    return outputs(attempt,dict(status='PASS',role='evaluator',conditions=['C0','C1'],actual_full_mesh_motion_verified=True,GT_read_by_evaluator=True))


def run(task,attempt):
    root=attempt.parents[1];cfg=task['fusion'];checks,truth=check_injection(task,root,cfg['condition_order']);reg,pred=registration_metrics(task,root,'G3_all_predict');regby={r['key']:r for r in reg}
    fusion=json.loads(fetch(root,'G4_fusion_predict','FUSION_FROZEN.json').read_text());gt=dict(np.load(fetch(root,'G0_views_noise','private/GT_SCENE.npz')));gs=scene(gt['V'],gt['F']);targets=np.load(fetch(root,'G0_views_noise','private/FIXED_GT_TARGETS.npz'));Pgt=targets['points'];observed=targets['observed'];reference={}
    for s in cfg['sections']:reference[s['axis'],s['offset_mm']]=plane_coordinates(mesh_sections(gt['V'],gt['F'],s['axis'],s['offset_mm']),s['axis'])
    baselines=[]
    for arm in cfg['body_arms']:
        b=np.load(fetch(root,'G1_body',arm+'_BODY.npz'))
        for model,(V,F)in [('BODY_ONLY_FROZEN_MESH',(b['V'],b['F'])),('BODY_ONLY_MATCHED_CHART',body_chart(b))]:
            m=model_metrics(V,F,gt,gs,Pgt,observed,arm,cfg,cfg['seed']+99);m['sections']=section_metrics(V,F,reference,cfg);m['model']=model;baselines.append(m)
    models=[];failures=[]
    for f in fusion['rows']:
        r=regby[f['key']]
        if f['status']!='NUMERIC':models.append(dict(key=f['key'],status='FAILED_NAN',fixed_GT_target_N=len(Pgt),GT_unique_coverage=0.,reason=f.get('reason')));failures.append(dict(key=f['key'],category='method_failure',reason=f.get('reason')));continue
        mesh=np.load(fetch(root,'G4_fusion_predict',f['key']+'/FUSED_MODEL.npz'));ownership=np.load(fetch(root,'G4_fusion_predict',f['key']+'/SURFACE_OWNERSHIP.npz'))
        require(len(np.unique(ownership['base_face_ids']))==len(mesh['F']),'DUPLICATE_COVERAGE','Unique actual fused triangles')
        m=model_metrics(mesh['V'],mesh['F'],gt,gs,Pgt,observed,r['arm'],cfg,cfg['seed']+99,ownership);m.update({k:r[k]for k in ['key','condition','arm','method','kind','tolerance_mm']});m['status']='NUMERIC';m['ownership_summary']=f;m['sections']=section_metrics(mesh['V'],mesh['F'],reference,cfg);models.append(m)
        baseline=next(b for b in baselines if b['arm']==r['arm']and b['model']=='BODY_ONLY_MATCHED_CHART');improvement=m['bidirectional_mm']['MAE']<baseline['bidirectional_mm']['MAE'];m['improves_Body_bidirectional_MAE']=bool(improvement);m['comparison_baseline']='BODY_ONLY_MATCHED_CHART'
        if not improvement or not r['optimizer_success']or r['mean_frame_material_MAE_mm']>cfg['material_success_threshold_mm']:
            failures.append(dict(key=r['key'],category='scientific_negative',reason='Body fusion did not improve and/or material-location or optimizer criterion not met; preserve all curves',material_MAE_mm=r['mean_frame_material_MAE_mm'],Body_bidirectional_MAE_mm=baseline['bidirectional_mm']['MAE'],fusion_bidirectional_MAE_mm=m['bidirectional_mm']['MAE'],optimizer_success=r['optimizer_success']))
    save_json(attempt/'REGISTRATION_METRICS.json',dict(rows=reg,denominators='All per-view material vertices; fixed overlap material targets. Failed targets kept, no GT optimal rigid alignment'))
    save_json(attempt/'MODEL_METRICS.json',dict(body_only=baselines,models=models,GT_fixed_target_N=len(Pgt),GT_observed_target_N=int(observed.sum()),GT_unobserved_target_N=int((~observed).sum()),GT_alignment=False))
    save_json(attempt/'NOISE_AUDIT.json',dict(empirical_checks=checks,actual_injections=truth,estimated_pose_model=cfg['pose_model'],actual_inverse_not_available_to_predictor=True))
    save_json(attempt/'FAILURE_LEDGER.json',dict(failures=failures,new_permanent_rules=False,no_scientific_failure_hidden=True))
    return outputs(attempt,dict(status='PASS',role='evaluator',models=len(models),scientific_failures=len(failures),GT_read_by_evaluator=True,GT_alignment=False))
