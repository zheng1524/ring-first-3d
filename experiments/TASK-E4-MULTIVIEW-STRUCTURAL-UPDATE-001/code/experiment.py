"""Registered handlers. Engineering execution and C0 scientific validity are distinct."""
from pathlib import Path
import io,json,sys,unittest,shutil
import numpy as np
import open3d as o3d
from ring_first_3d.policy.contracts import ROOT,require
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.synthetic.io import fetch,save_json,outputs
from ring_first_3d.multisurface.geometry import scene,sample_mesh,closest
from ring_first_3d.multisurface.evaluate import fixed_stats
from body_update import update,projection_metrics,ring_maps,legacy_geometry,growth_quality
from data_adapter import simulation_data,real_data,audit,sources


def train_one(task,attempt,case,simulation=False):
    initial,views,ring,base,chart=simulation_data(task,'FIT') if simulation else real_data(task,case,'FIT')
    out=attempt/case;out.mkdir();np.savez_compressed(out/'INITIAL.npz',**initial);records=[]
    geometry_source=task['structural']['assets']['legacy_geometry']['path']
    for arm in task['structural']['Body_arms']:
        body=update(initial,views,ring,base,chart,task['structural']['update'],out/arm,geometry_source,arm=='DEFORM_GROW')
        records.append(dict(case=case,arm=arm,status='NUMERIC',mesh_relative=case+'/'+arm+'/FINAL.npz',
                            mesh_sha256=sha256(out/arm/'FINAL.npz'),update_record_relative=case+'/'+arm+'/UPDATES.json',
                            GT_read=False,HERO_read=False,cameras_optimized=False))
    save_json(out/'PREDICTIONS_FROZEN.json',dict(records=records,FIT_ids=[v['id'] for v in views],GT_read=False,checkpoint='FINAL_FIXED_BUDGET_NO_GT_SELECTION'))
    return records


def c0_train(task,attempt):
    rows=train_one(task,attempt,'C0',True);save_json(attempt/'BODY_PREDICTIONS_FROZEN.json',dict(records=rows,GT_read=False))
    return outputs(attempt,dict(status='PASS',condition='C0',body_arms=len(rows),GT_read_by_predictor=False))


def shape_metrics(body,gt,seed=20261117,N=12000):
    P,_,_=sample_mesh(body['V'],body['F'],N,seed);G,_,_=sample_mesh(gt['V'],gt['F'],N,seed+1)
    Q,_,_=closest(scene(gt['V'],gt['F']),P);d=np.linalg.norm(P-Q,axis=1)
    Q,_,_=closest(scene(body['V'],body['F']),G);e=np.linalg.norm(G-Q,axis=1)
    return dict(Chamfer_mm=fixed_stats(np.r_[d,e]),pred_to_GT_mm=fixed_stats(d),GT_to_pred_mm=fixed_stats(e),
                Fscore_0p5mm=float(2*(d<=.5).mean()*(e<=.5).mean()/max(1e-12,(d<=.5).mean()+(e<=.5).mean())),
                GT_coverage_0p5mm=float((e<=.5).mean()),fixed_samples_per_direction=N)


def c0_evaluate(task,attempt):
    root=attempt.parents[1];freeze=fetch(root,'G1_C0_update','BODY_PREDICTIONS_FROZEN.json')
    save_json(attempt/'GT_FIRST_ACCESS.json',dict(predictions_frozen_sha256=sha256(freeze),stage='G2_C0_evaluate',prediction_changes_after_GT=False))
    initial,views,ring,base,chart=simulation_data(task);rz=ring_maps(views,ring)
    gt=dict(np.load(task['structural']['assets']['virtual_gt']['path']));ns=legacy_geometry(task['structural']['assets']['legacy_geometry']['path'])
    np.savez_compressed(attempt/'GT.npz',V=gt['V'],F=gt['F']);rows=[]
    for arm in ['INITIAL']+task['structural']['Body_arms']:
        p=fetch(root,'G1_C0_update','C0/INITIAL.npz' if arm=='INITIAL' else 'C0/'+arm+'/FINAL.npz');m=dict(np.load(p));digest=sha256(p)
        projection=projection_metrics(m,views,rz);why,geo=growth_quality(m,initial,ring,ns,base,chart)
        item=dict(arm=arm,**shape_metrics(m,gt),projection=projection,geometry=geo,geometry_violations=why,
                  prediction_sha256=digest,GT_alignment='NONE; physical canonical Ring frame retained')
        item['split_means']={role:{key:float(np.mean([r[key] for r in projection if r['role']==role])) for key in ('IoU','Boundary_Fscore_at2px')} for role in ('FIT','HOLDOUT')}
        if arm!='INITIAL':item['updates']=json.loads(fetch(root,'G1_C0_update','C0/'+arm+'/UPDATES.json').read_text())
        require(sha256(p)==digest,'BODY_IMMUTABLE','Evaluator cannot alter predictions');rows.append(item)
    b={r['arm']:r for r in rows};a=b['DEFORM_GROW'];old=b['INITIAL'];deform=b['DEFORM_ONLY'];checks=dict(
        GT_Chamfer_improvement=a['Chamfer_mm']['MAE']<old['Chamfer_mm']['MAE'],
        HOLDOUT_IoU_nonworsening=a['split_means']['HOLDOUT']['IoU']>=old['split_means']['HOLDOUT']['IoU'],
        accepted_growth=a['updates']['accepted_growth']>0,
        growth_over_deform_GT_gain=a['Chamfer_mm']['MAE']<deform['Chamfer_mm']['MAE'],
        no_geometry_worsening=not a['geometry_violations'])
    result=dict(rows=rows,condition='C0',scientific_checks=checks,scientific_pass=all(checks.values()),
                GT_read_only_after_predictions_frozen=True,hyperparameters_selected_with_GT=False,
                seed=20261117,real_cases_permitted=all(checks.values()))
    save_json(attempt/'C0_METRICS.json',result);return outputs(attempt,dict(status='PASS',scientific_pass=result['scientific_pass'],checks=checks,GT_read_by_evaluator=True))


def c0_gate(task,attempt):
    result=json.loads(fetch(attempt.parents[1],'G2_C0_evaluate','C0_METRICS.json').read_text())
    save_json(attempt/'SCIENTIFIC_GATE.json',dict(scientific_pass=result['scientific_pass'],checks=result['scientific_checks'],
                decision='PROCEED_REAL' if result['scientific_pass'] else 'STOP_CORE_VALIDATION_FAILED',
                no_parameter_retuning_after_GT=True,negative_result_is_not_code_error=True))
    return outputs(attempt,dict(status='PASS' if result['scientific_pass'] else 'SCIENTIFIC_NEGATIVE_STOP',
                               checks=result['scientific_checks'],real_executed=False))


def require_c0(root):
    rec=json.loads(fetch(root,'G4_C0_gate','SCIENTIFIC_GATE.json').read_text())
    require(rec['scientific_pass'],'C0_SCIENTIFIC_GATE','Real experiments not authorized until C0 validates shared structural updates')


def real_train(task,attempt):
    require_c0(attempt.parents[1]);rows=[]
    for case in task['structural']['real_cases']:
        try:rows.extend(train_one(task,attempt,case))
        except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:
            from ring_first_3d.policy.contracts import PolicyError
            if isinstance(e,PolicyError):raise
            rows.append(dict(case=case,status='FAILED_NAN',reason=str(e)))
    save_json(attempt/'BODY_PREDICTIONS_FROZEN.json',dict(records=rows,GT_read=False));return outputs(attempt,dict(status='PASS',records=rows))


def hero_predict(task,attempt):
    from hero_relocation import relocate
    from ring_first_3d.stress.real import load_view,validate_view
    root=attempt.parents[1];require_c0(root);pred=json.loads(fetch(root,'G5_real_update','BODY_PREDICTIONS_FROZEN.json').read_text());by={(r['case'],r.get('arm')):r for r in pred['records']};groups=[]
    for case in task['structural']['real_cases']:
        src=next(g for g in sources(task)['real_groups'] if g['group']==case);fit=[v for v in src['views'] if v['role']=='FIT'];out=attempt/case;out.mkdir();record=dict(case=case,methods=[],absolute_GT='NOT_EVALUABLE_NO_INDEPENDENT_GT')
        if len(fit)<2 or by.get((case,'DEFORM_GROW'),{}).get('status')!='NUMERIC':
            record.update(status='NOT_EVALUABLE',reason='No source-bound multi-Mesh or final Body');groups.append(record);continue
        for v in fit:validate_view(v)
        data=[load_view(v,[.3,.1]) for v in fit];initial,_,ring,_,_=real_data(task,case,'FIT');bp=fetch(root,'G5_real_update',by[case,'DEFORM_GROW']['mesh_relative']);digest=sha256(bp);final=dict(np.load(bp))
        for method,body in [('M0',initial),('RAY_INITIAL',initial),('RAY_UPDATED',final)]:
            mo=out/method;mo.mkdir()
            if method=='M0':meshes=[dict(V=d['V'],F=d['F'],uv=d['uv']) for d in data];maps=[];details=dict(original=True)
            else:meshes,maps,details=relocate(data,body,ring,task['structural']['hero'])
            for d,m in zip(data,meshes):np.savez_compressed(mo/(d['id']+'.npz'),**m)
            for d,p in zip(data,maps):np.savez_compressed(mo/(d['id']+'_CORRESPONDENCES.npz'),**p)
            record['methods'].append(dict(method=method,details=details,status='NUMERIC'))
        require(sha256(bp)==digest,'BODY_IMMUTABLE','HERO never updates Body');record.update(status='NUMERIC',Body_sha256=digest,camera_optimized=False);groups.append(record)
    save_json(attempt/'HERO_PREDICTIONS_FROZEN.json',dict(groups=groups,GT_read=False,no_fusion=True));return outputs(attempt,dict(status='PASS',groups=len(groups)))


def real_evaluate(task,attempt):
    from ring_first_3d.inita.evaluate import legacy_namespace
    from ring_first_3d.stress.real import load_view,overlap_targets,holdout_metrics
    root=attempt.parents[1];require_c0(root);pred=json.loads(fetch(root,'G5_real_update','BODY_PREDICTIONS_FROZEN.json').read_text());rows=[]
    ns=legacy_namespace(dict(task,task_id='TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001'))
    for case in task['structural']['real_cases']:
        initial,views,ring,base,chart=real_data(task,case);rz=ring_maps(views,ring);source=next(r for r in sources(task)['cases'] if r['case']==case);gt=dict(np.load(source['GT']['path']));out=attempt/case;out.mkdir()
        for arm in ['INITIAL']+task['structural']['Body_arms']:
            if arm=='INITIAL':m=initial
            else:
                r=next((r for r in pred['records'] if r['case']==case and r.get('arm')==arm),{})
                if r.get('status')!='NUMERIC':rows.append(dict(case=case,arm=arm,status='FAILED_NAN'));continue
                m=dict(np.load(fetch(root,'G5_real_update',r['mesh_relative'])))
            T,trials=ns['align'](m['V'],m['F'],gt['V'],gt['F'],10. if source['ring']=='R10' else 5.)
            aligned=dict(m,V=ns['apply'](m['V'],T));np.savez_compressed(out/(arm+'_GT_ALIGNED.npz'),**aligned,T=T)
            save_json(out/(arm+'_RIGID_TRIALS.json'),trials)
            rows.append(dict(case=case,arm=arm,status='NUMERIC',**shape_metrics(aligned,gt),projection=projection_metrics(m,views,rz),alignment=T,GT_alignment_scope='EVALUATION_COPY_ONLY_SCALE1'))
    save_json(attempt/'REAL_BODY_METRICS.json',dict(rows=rows,target_cases=3))
    hero=json.loads(fetch(root,'G6_hero_relocate','HERO_PREDICTIONS_FROZEN.json').read_text());heroes=[]
    for group in hero['groups']:
        case=group['case'];source=next(g for g in sources(task)['real_groups'] if g['group']==case)
        if group['status']!='NUMERIC':heroes.append(group);continue
        data=[load_view(v,[.3,.1]) for v in source['views'] if v['role']=='FIT'];fixed=overlap_targets(data);save_json(attempt/(case+'_FIXED_OVERLAPS.json'),fixed);ring=dict(np.load(source['assets']['ring']['path']));rs=scene(ring['V'],ring['F'])
        for method in group['methods']:
            meshes=[dict(np.load(fetch(root,'G6_hero_relocate',case+'/'+method['method']+'/'+d['id']+'.npz'))) for d in data];scenes=[scene(m['V'],m['F']) for m in meshes];family={'within_video':[],'cross_video':[]}
            for p in fixed:
                P=meshes[p['first']]['V'][p['source_vertex']];Q,_,_=closest(scenes[p['second']],P) if len(P) else (np.empty((0,3)),None,None);family[p['family']].extend(np.linalg.norm(P-Q,axis=1))
            V=np.concatenate([m['V'] for m in meshes]);offset=0;faces=[]
            for m in meshes:faces.append(m['F']+offset);offset+=len(m['V'])
            full=dict(V=V,F=np.concatenate(faces));hold=[holdout_metrics(full,v,rs) for v in source['views'] if v['role']=='HOLDOUT']
            heroes.append(dict(case=case,method=method['method'],status='NUMERIC',**{k:fixed_stats(x) for k,x in family.items()},HOLDOUT=hold,details=method['details'],absolute_accuracy='NOT_EVALUABLE_NO_INDEPENDENT_GT',GT_alignment=False))
    save_json(attempt/'REAL_HERO_METRICS.json',dict(rows=heroes,target_cases=3,all_raw_vertices_preserved=True));return outputs(attempt,dict(status='PASS',body_rows=len(rows),HERO_rows=len(heroes)))


def regression(attempt):
    loader=unittest.defaultTestLoader;patterns=['test_harness_contracts.py','test_policy_bootstrap.py','test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py','test_stress.py','test_inita.py','test_contour_guided.py','test_structural_update.py'];suites=[loader.discover(str(ROOT/'tests'),pattern=p) for p in patterns];base=sum(s.countTestCases() for s in suites[:2]);stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(suites));(attempt/'regression_log.txt').write_text(stream.getvalue());return outputs(attempt,dict(status='PASS' if r.wasSuccessful() and base==35 else 'FAIL',baseline_tests=base,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors)))


def dispatch(stage,task,attempt):
    if stage=='structural_regression':return regression(attempt)
    if stage=='G0_initialization':return outputs(attempt,audit(task,attempt))
    if stage=='G1_C0_update':return c0_train(task,attempt)
    if stage=='G2_C0_evaluate':return c0_evaluate(task,attempt)
    if stage in {'G3_C0_visualize','G4_visualize'}:
        from figures import visualize
        return visualize(task,attempt,stage=='G4_visualize')
    if stage=='G4_C0_gate':return c0_gate(task,attempt)
    if stage=='G5_real_update':return real_train(task,attempt)
    if stage=='G6_hero_relocate':return hero_predict(task,attempt)
    if stage=='G7_real_evaluate':return real_evaluate(task,attempt)
    raise ValueError(stage)
