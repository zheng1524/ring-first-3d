"""Independent post-freeze evaluation; never supplies values back to predictors."""
import json
import numpy as np
from scipy.spatial.transform import Rotation
from ..synthetic.io import fetch,save_json,outputs
from ..policy.contracts import require
from ..contracts.identities import sha256
from ..contracts.coordinates import unproject,project
from .geometry import scene,closest,transform,summary,boundary_error,contour,cast,pose_error,choose
from .legacy import namespace


def gt_scene(root):
    a=dict(np.load(fetch(root,'G0_simulate','private/virtual_GT.npz')));return a,scene(a['V'],a['F'])


def body(task,attempt):
    root=attempt.parents[1];ns=namespace(task);gt,gs=gt_scene(root);freeze=json.loads(fetch(root,'G1_initialize','BODY_FREEZE.json').read_text())
    frames=json.loads(fetch(root,'G0_simulate','public/frame_index.json').read_text());ring=np.load(fetch(root,'G0_simulate','public/canonical_ring.npz'));rs=scene(ring['V'],ring['F'])
    rows=[];arms=[]
    for arm,selection in freeze['selections'].items():
        if not selection['available']:arms.append(dict(arm=arm,status=selection['status'],GT_surface_error_mm=None));continue
        b=dict(np.load(fetch(root,'G1_initialize',arm+'_body.npz')));bs=scene(b['V'],b['F'])
        p,_,_=closest(gs,b['V']);q,_,_=closest(bs,gt['V']);errors=np.r_[np.linalg.norm(p-b['V'],axis=1),np.linalg.norm(q-gt['V'],axis=1)]
        c,Q,a=ns['decode'](b['p'],b['R0']);rho=np.linalg.norm((ring['V']-c)@Q/a,axis=1)
        arms.append(dict(arm=arm,status=selection['status'],symmetric_GT_surface_mm=summary(errors),GT_surface_error_mm=summary(errors),
            Ring_vertices_inside_body=int((rho<1).sum()),Ring_penetration_fraction=float((rho<1).mean()),Ring_penetration_proxy_max_mm=float(np.maximum(0,1-rho).max()*min(a)),
            independent_numeric_N=len(errors),GT_selected_body=False))
        for row in frames:
            obs=np.load(fetch(root,'G0_simulate','public/initialization/'+row['id']+'.npz'));K,C=obs['K'],obs['C']
            y,x=np.mgrid[:360,:640];uv=np.c_[x.ravel(),y.ravel()];z=ns['first_depth'](b['p'],b['R0'],ns['vis'].camera_rays(uv,K,C));rz=cast(rs,uv,K,C)[0]
            pred=(np.isfinite(z)&(z<rz)).reshape(360,640);labels=obs['labels'];known=labels!=2;mask=labels==1;knownpred=pred&known
            error=boundary_error(contour(mask),contour(knownpred));inter=(mask&knownpred).sum();union=(mask|knownpred).sum()
            rows.append(dict(arm=arm,id=row['id'],video=row['video'],role=row['role'],used_for_body_fit=row['id']in freeze['fit_ids'],IoU=float(inter/max(1,union)),boundary_px=error,
                observed_pixels=int(mask.sum()),missed_pixels=int((mask&~pred).sum()),Ring_unknown_prediction_pixels=int((pred&~known).sum())))
    save_json(attempt/'G1_METRICS.json',dict(arms=arms,frames=rows,selected_arm=freeze['selected_arm'],multi_start_stability=freeze['multi_start_stability'],GT_selected_body=False,Body_sha256=freeze['body_sha256']))
    return outputs(attempt,dict(status='PASS',role='evaluator',arms=arms,frame_rows=rows,GT_read_by_evaluator=True))


def mapping(task,attempt):
    root=attempt.parents[1];freeze=json.loads(fetch(root,'G2_mapping','MAPPING_FROZEN.json').read_text());body=np.load(fetch(root,'G1_initialize','FROZEN_BODY.npz'));rows=[];paired=[];errors={}
    for row in freeze['rows']:
        m=np.load(fetch(root,'G2_mapping','maps/'+row['key']+'.npz'));truth=np.load(fetch(root,'G0_simulate','private/'+row['id']+'.npz'))
        uv=m['original_uv'].astype(int);truevisible=truth['true_visible'][uv[:,1],uv[:,0]];gt=truth['points'][uv[:,1],uv[:,0]]
        numeric=m['valid'];valid=numeric&truevisible&~m['contact_unknown'];err=np.linalg.norm(m['points']-gt,axis=1)
        if numeric.any():require(np.max(np.linalg.norm(np.einsum('ni,nij->nj',m['bary'][numeric],body['V'][body['F'][m['face'][numeric]]])-m['points'][numeric],axis=1))<1e-8,'BARYCENTRIC_CONTRACT',row['key'])
        result=dict(**row,target_N=len(valid),numeric_N=int(numeric.sum()),independently_evaluable_N=int(valid.sum()),not_evaluable_N=int((~valid).sum()),coverage=float(valid.mean()),
            GT_point_error_mm=summary(err[valid]),GT_reference='Synthetic original-pixel visible surface; real_source is G01-like virtual-ray diagnostic only',
            true_source_to_virtual_unmatched=int((~truevisible).sum()))
        rows.append(result);errors[row['key']]=(err,valid)
    for row in freeze['rows']:
        if row['method']!='MEDIATED':continue
        key=row['key'];other=key.replace('__MEDIATED','__DIRECT_PIXEL');e,v=errors[key];d,w=errors[other];common=v&w
        paired.append(dict(id=row['id'],domain=row['domain'],role=row['role'],common_N=int(common.sum()),target_N=len(v),mediated_MAE_mm=float(e[common].mean())if common.any()else None,direct_MAE_mm=float(d[common].mean())if common.any()else None))
    save_json(attempt/'G2_METRICS.json',dict(rows=rows,paired_common_success=paired,mapping_is_pose_correction=False,GT_used_after_prediction_freeze=True))
    return outputs(attempt,dict(status='PASS',role='evaluator',rows=rows,GT_read_by_evaluator=True))


def registration(task,attempt,smoke=False):
    root=attempt.parents[1];stage='G3_smoke_predict'if smoke else'G3_matrix_predict';freeze=json.loads(fetch(root,stage,'PREDICTIONS_FROZEN.json').read_text())
    injections=json.loads(fetch(root,'G0_simulate','private/INJECTIONS.json').read_text());gt,gs=gt_scene(root)
    index=json.loads(fetch(root,'G0_simulate','public/frame_index.json').read_text());source=json.loads(__import__('pathlib').Path(task['sim']['assets']['source_manifest']['path']).read_text());native={r['view_id']:np.asarray(r['Camera_to_Ring'])for r in source['rows']}
    truth={v:dict(np.load(fetch(root,'G0_simulate','private/'+v+'_clean.npz')))for v in ['004','005']};rows=[];injection_checks=[]
    for cond in sorted({r['condition']for r in freeze['rows']}):
        cameras=json.loads(fetch(root,'G0_simulate','public/conditions/'+cond+'/cameras.json').read_text())
        for v in ['004','005']:
            D=np.asarray(injections[cond][v]);angle,tr=task['sim']['error_transforms'][task['sim']['conditions'][cond][v]]
            # Independent scipy Euler construction, not generator adapter reuse.
            R=Rotation.from_euler('y',angle,degrees=True).as_matrix();independent=np.eye(4);independent[:3,:3]=R;independent[0,3]=tr
            require(np.allclose(D,independent,atol=1e-12),'INJECTION_PROTOCOL',cond+v)
            obs=np.load(fetch(root,'G0_simulate','public/conditions/'+cond+'/'+v+'_mesh.npz'))
            err=float(np.linalg.norm(obs['V']-transform(truth[v]['V'],independent),axis=1).max());require(err<1e-10 and np.array_equal(obs['F'],truth[v]['F']),'MESH_RIGIDITY','Injected full original topology')
            cs=[c for c in cameras if c['video']==v]
            for c in cs:
                require(np.allclose(c['T_estimated'],independent@native[c['id']],atol=1e-10),'CAMERA_BINDING',c['id'])
                if cond!='L1':require(np.allclose(np.linalg.inv(D)@np.asarray(c['T_estimated']),native[c['id']],atol=1e-10),'INJECTION_PROTOCOL','Camera-to-Ring invariant')
            for a,b in zip(cs,cs[1:]):require(np.allclose(np.linalg.inv(a['T_estimated'])@np.asarray(b['T_estimated']),np.linalg.inv(native[a['id']])@native[b['id']],atol=1e-10),'INJECTION_PROTOCOL','Within-video camera geometry')
            injection_checks.append(dict(condition=cond,video=v,actual_rotation_deg=pose_error(D)['rotation_deg'],actual_translation_mm=pose_error(D)['translation_mm'],mesh_injection_max_error_mm=err,actual_mesh_motion_max_mm=float(np.linalg.norm(obs['V']-truth[v]['V'],axis=1).max()),camera_to_Ring_invariant=cond!='L1',within_video_relative_poses_preserved=True))
    # Evaluation uses independent re-rendering of every registered full mesh for
    # HOLDOUT: mesh + estimated camera share a correction, while Body is fixed.
    ns=namespace(task);body=np.load(fetch(root,'G1_initialize','FROZEN_BODY.npz'));canon_ring=np.load(fetch(root,'G0_simulate','public/canonical_ring.npz'));rs=scene(canon_ring['V'],canon_ring['F'])
    for pred in freeze['rows']:
        cond,method=pred['condition'],pred['method'];D={v:np.asarray(injections[cond][v])for v in ['004','005']};input_relative=np.linalg.inv(D['004'])@D['005']
        if pred['status']!='NUMERIC':rows.append(dict(condition=cond,family=pred['family'],method=method,status='FAILED_NAN',relative_before=pose_error(input_relative),relative_after=None,GT_surface_mm=None,coverage=0.,reason=pred['reason']));continue
        X={v:np.asarray(pred['corrections'][v])for v in D};E={v:X[v]@D[v]for v in D};relative=np.linalg.inv(E['004'])@E['005'];pervideo=[];holdout=[];meshes={};all_surface_errors=[]
        for v in D:
            mesh=dict(np.load(fetch(root,stage,cond+'/'+method+'/'+v+'_registered.npz')));meshes[v]=mesh
            observed=np.load(fetch(root,'G0_simulate','public/conditions/'+cond+'/'+v+'_mesh.npz'))
            require(np.array_equal(mesh['F'],observed['F'])and np.allclose(mesh['V'],transform(observed['V'],X[v]),atol=1e-10),'MESH_RIGIDITY','Actual complete mesh output must equal estimated rigid correction')
            near,_,_=closest(gs,mesh['V']);raw=np.linalg.norm(mesh['V']-near,axis=1)
            gauged=transform(mesh['V'],np.linalg.inv(E['004']));gnear,_,_=closest(gs,gauged);gauge=np.linalg.norm(gauged-gnear,axis=1)
            all_surface_errors.append(gauge)
            point_error=np.linalg.norm(gauged-truth[v]['V'],axis=1)
            pervideo.append(dict(video=v,vertices=len(mesh['V']),faces=len(mesh['F']),absolute_GT_surface_mm=summary(raw),gauge_fixed_GT_surface_mm=summary(gauge),gauge_fixed_material_point_mm=summary(point_error),coverage_surface_within0p1mm=float((gauge<=.1).mean()),numeric_coverage=1.,true_relative_pose_error=pose_error(relative)))
        # Common visible material vertices are an evaluation-only diagnostic,
        # never used as known correspondence by ICP or the Body optimizer.
        common,ix,iy=np.intersect1d(truth['004']['original_vertex_ids'],truth['005']['original_vertex_ids'],return_indices=True)
        agreement=np.linalg.norm(meshes['004']['V'][ix]-meshes['005']['V'][iy],axis=1)
        camera_rows=json.loads(fetch(root,'G0_simulate','public/conditions/'+cond+'/cameras.json').read_text())
        for c in camera_rows:
            if c['role']!='HOLDOUT':continue
            v=c['video'];C=X[v]@np.asarray(c['T_estimated']);K=np.asarray(c['K']);obs=np.load(fetch(root,'G0_simulate','public/observations/'+c['id']+'.npz'))
            center,M,axes,curve=ns['ellipse_projection'](body['p'],body['R0'],K,C);boundary=contour(obs['labels']==1)
            holdout.append(dict(id=c['id'],video=v,body_contour_px=summary(ns['signed_distance'](boundary,center,M,axes)),GT_used_to_select=False))
        rows.append(dict(condition=cond,family=pred['family'],method=method,status='NUMERIC',relative_before=pose_error(input_relative),relative_after=pose_error(relative),
          per_video=pervideo,GT_surface_mm=summary(np.concatenate(all_surface_errors)),
          common_visible_material_N=len(common),common_visible_consistency_mm=summary(agreement),HOLDOUT=holdout,
          relative_pose_pass=pose_error(relative)['rotation_deg']<=task['sim']['relative_success_rotation_deg']and pose_error(relative)['translation_mm']<=task['sim']['relative_success_translation_mm'],
          optimizer_success=pred['details'].get('optimizer_success',True),corrections=pred['corrections'],Body_frozen=True,GT_read_by_predictor=False))
    if smoke:
        check=next(r for r in injection_checks if r['condition']=='S1'and r['video']=='005');require(check['actual_mesh_motion_max_mm']>.1,'SMOKE_INJECTION','A must actually displace full Mesh')
        moved=[p for p in freeze['rows']if p['condition']=='S1'and p['method']in {'M1','M2'}and p['status']=='NUMERIC'and p['full_mesh_max_displacement_mm']['005']>.01]
        require(moved,'SMOKE_OPTIMIZATION','At least one real legal optimizer must move the actual mesh')
    save_json(attempt/'REGISTRATION_METRICS.json',dict(rows=rows,injection_checks=injection_checks,smoke=smoke,GT_used_after_prediction_freeze=True,GT_selects_predictor=False,
        gauge='Relative E004^-1 E005; absolute surface and 004-gauge-fixed surface reported separately. S4 has shared world gauge.'))
    return outputs(attempt,dict(status='PASS',role='evaluator',rows=rows,injection_checks=injection_checks,GT_read_by_evaluator=True,smoke=smoke))
