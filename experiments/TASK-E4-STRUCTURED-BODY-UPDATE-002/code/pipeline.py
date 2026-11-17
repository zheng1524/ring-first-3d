"""Policy-only handlers: fixed real pilot, all prediction freezes precede GT."""
from pathlib import Path
import csv,io,json,unittest,sys
import numpy as np
from common import load_case,legacy,dump,geometry,OLD
from optimizer import train
from projection_gate import ProjectionGate,stats
from ring_collision_gate import RingCollisionGate
from ring_first_3d.synthetic.io import fetch,outputs
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.policy.contracts import ROOT,require,PolicyError
from ring_first_3d.multisurface.geometry import scene,sample_mesh,closest
from ring_first_3d.multisurface.evaluate import fixed_stats
TD=ROOT/'experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002'
PREVIOUS=OLD/'runs/STRUCTURAL_004/attempts/0009-G5_real_update-842b9067'

def read(p):return json.loads(Path(p).read_text())
def regression(attempt):
    patterns=['test_harness_contracts.py','test_policy_bootstrap.py','test_synthetic_correspondence.py','test_dualvideo_gate.py','test_sim_rev1.py','test_multisurface.py','test_stress.py','test_inita.py','test_contour_guided.py','test_structural_update.py']
    loader=unittest.defaultTestLoader;suites=[loader.discover(str(ROOT/'tests'),pattern=p)for p in patterns];base=sum(s.countTestCases()for s in suites[:2]);suites.append(loader.discover(str(TD/'tests')))
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(suites));(attempt/'regression_log.txt').write_text(stream.getvalue())
    return outputs(attempt,dict(status='PASS'if r.wasSuccessful()and base==35 else'FAIL',baseline_tests=base,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors)))

def audit(task,attempt):
    import torch
    from ring_first_3d.synthetic.raster import ray_map
    items=[]
    for case in task['structured']['cases']:
        initial,views,ring,base,chart,row=load_case(case,'FIT');weights=legacy.balanced_weights(views);projection=[]
        for v in views:
            rr=ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape);p=rr['valid'];t=v['labels']==2
            projection.append(dict(id=v['id'],video=v['video'],**stats(p,t,np.ones_like(t,bool)),weight=weights[v['id']],camera_sha256=sha256(next(x['cache']['path']for x in row['FIT']if x['meta']['id']==v['id']))))
        items.append(dict(case=case,initial_path=row['resolved013_initial']['path'],initial_sha256=sha256(row['resolved013_initial']['path']),vertices=len(initial['V']),faces=len(initial['F_solid']),FIT=[v['id']for v in views],HOLDOUT=[v['meta']['id']for v in row['HOLDOUT']],weights=weights,ring_projection=projection,GT_read=False,HERO_read=False))
    dump(attempt/'INITIALIZATION_AUDIT.json',dict(cases=items,initializer=str(legacy.__file__),initializer_sha256=sha256(legacy.__file__),same_initializer_function=True,E1_E2_used=False,coordinates='opencv_c2w_mm',environment=dict(python=sys.executable,torch=torch.__version__,cuda=torch.cuda.is_available(),GPU=torch.cuda.get_device_name(0))))
    return outputs(attempt,dict(status='PASS',cases=3,GT_read=False,HERO_read=False))

def predict(task,attempt,case):
    initial,views,ring,base,chart,row=load_case(case,'FIT');records=[]
    for arm in task['structured']['arms']:
        try:
            target=attempt/case/arm;train(initial,views,ring,base,chart,task['structured']['update'],target,arm)
            records.append(dict(case=case,arm=arm,status='NUMERIC',mesh_relative=f'{case}/{arm}/FINAL.npz',mesh_sha256=sha256(target/'FINAL.npz')))
        except (ValueError,RuntimeError,np.linalg.LinAlgError)as e:
            if isinstance(e,PolicyError):raise
            records.append(dict(case=case,arm=arm,status='FAILED_NAN',reason=str(e)))
    dump(attempt/'BODY_PREDICTIONS_FROZEN.json',dict(records=records,GT_read=False,HERO_read=False,camera_optimized=False,checkpoint='FINAL_FIXED36_NO_GT_SELECTION'))
    return outputs(attempt,dict(status='PASS',records=records,GT_read=False))

def shape_metrics(body,gt,N=12000):
    P,_,_=sample_mesh(body['V'],body['F'],N,20261117);G,_,_=sample_mesh(gt['V'],gt['F'],N,20261118)
    Q,_,_=closest(scene(gt['V'],gt['F']),P);d=np.linalg.norm(P-Q,axis=1);Q,_,_=closest(scene(body['V'],body['F']),G);e=np.linalg.norm(G-Q,axis=1)
    return dict(Chamfer_mm=fixed_stats(np.r_[d,e]),pred_to_GT_mm=fixed_stats(d),GT_to_pred_mm=fixed_stats(e),Fscore_0p5mm=float(2*(d<=.5).mean()*(e<=.5).mean()/max(1e-12,(d<=.5).mean()+(e<=.5).mean())),GT_coverage_0p5mm=float((e<=.5).mean()),fixed_samples_per_direction=N)

def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r));path.parent.mkdir(exist_ok=True,parents=True)
    with path.open('w')as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)

def evaluate(task,attempt):
    from ring_first_3d.inita.evaluate import legacy_namespace
    from ring_first_3d.synthetic.raster import ray_map
    root=attempt.parents[1];freezes={case:fetch(root,'G1_'+case,'BODY_PREDICTIONS_FROZEN.json')for case in task['structured']['cases']}
    dump(attempt/'GT_FIRST_ACCESS.json',dict(stage='G2_evaluate',all_prediction_freezes={c:dict(path=str(p),sha256=sha256(p))for c,p in freezes.items()},GT_tunes_algorithm=False,prediction_mutations_allowed=False))
    ns=legacy_namespace(dict(task,task_id='TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001'));gns=legacy.legacy_geometry('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/legacy015/safe_geometry.py')
    rows=[];bv=[];pv=[];gv=[];rv=[];failures=[]
    for case in task['structured']['cases']:
        initial,views,ring,base,chart,source=load_case(case);gt=dict(np.load(source['GT']['path']));folder=attempt/case;folder.mkdir();np.savez_compressed(folder/'GT.npz',**gt)
        records=read(freezes[case])['records'];rz={v['id']:ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape)['z']for v in views};rg=RingCollisionGate(initial,ring)
        paths={'INITIAL':None,'PREVIOUS_DEFORM_GROW':PREVIOUS/case/'DEFORM_GROW/FINAL.npz'}
        for r in records:
            if r['status']=='NUMERIC':paths[r['arm']]=fetch(root,'G1_'+case,r['mesh_relative'])
            else:
                failures.append(dict(type='CODE_OR_NUMERICAL_FAILURE',case=case,arm=r['arm'],symptom=r['reason'],confirmed_cause='See saved worker evidence; no fallback',permanent_rule=False));bv.append(dict(case=case,arm=r['arm'],status='FAILED_NAN',GT_MAE_mm='NaN'))
        initial_ge=None
        for arm,path in paths.items():
            body=initial if path is None else dict(np.load(path));digest=None if path is None else sha256(path)
            projection=[]
            for v in views:
                ra=ray_map(body['V'],body['F'],v['K'],v['C'],v['labels'].shape);pred=ra['valid']&(ra['z']<rz[v['id']]-.05)
                from scipy.ndimage import binary_dilation
                known=~binary_dilation(v['labels']==2,iterations=3);s=stats(pred,v['labels']==1,known);s.update(case=case,arm=arm,id=v['id'],video=v['video'],role=v['role'],raw_Mask_IoU=stats(pred,v['labels']==1,np.ones_like(known))['IoU']);projection.append(s);pv.append(s)
            # Original frozen metric-scale coordinates retained; GT rigid fit only copies.
            T,trials=ns['align'](body['V'],body['F'],gt['V'],gt['F'],10. if source['ring']=='R10'else 5.)
            aligned=dict(body,V=ns['apply'](body['V'],T));np.savez_compressed(folder/(arm+'_GT_ALIGNED.npz'),**aligned,T=T);dump(folder/(arm+'_RIGID_TRIALS.json'),trials)
            shape=shape_metrics(aligned,gt);unaligned=shape_metrics(body,gt);why,geo=geometry(body,initial,initial,base,chart,gns);collision=rg.measure(body)
            ringrow=dict(case=case,arm=arm,epsilon_mm=rg.epsilon,**{k:v for k,v in collision.items()if not isinstance(v,np.ndarray)});rv.append(ringrow);gv.append(dict(case=case,arm=arm,violations=';'.join(why),**geo))
            item=dict(case=case,arm=arm,status='NUMERIC',prediction_path=None if path is None else str(path),prediction_sha256=digest,GT_alignment_scope='EVALUATION_COPY_ONLY_SCALE1',alignment=T,projection=projection,geometry=geo,geometry_violations=why,ring=ringrow,**shape,unaligned_world_shape=unaligned)
            item['split_means']={role:{key:float(np.mean([r[key]for r in projection if r['role']==role]))for key in ['IoU','Boundary_Fscore_at2px','Boundary_MAE_px']}for role in ['FIT','HOLDOUT']}
            summary=dict(case=case,arm=arm,status='NUMERIC',GT_MAE_mm=shape['Chamfer_mm']['MAE'],GT_median_mm=shape['Chamfer_mm']['median'],GT_p95_mm=shape['Chamfer_mm']['p95'],GT_max_mm=shape['Chamfer_mm']['maximum'],GT_coverage_0p5mm=shape['GT_coverage_0p5mm'],Fscore_0p5mm=shape['Fscore_0p5mm'],FIT_IoU=item['split_means']['FIT']['IoU'],HOLDOUT_IoU=item['split_means']['HOLDOUT']['IoU'],FIT_Boundary_Fscore=item['split_means']['FIT']['Boundary_Fscore_at2px'],HOLDOUT_Boundary_Fscore=item['split_means']['HOLDOUT']['Boundary_Fscore_at2px'],growth_length_mm=0.,growth_volume_mm3=0.,growth_status='NOT_APPLICABLE')
            if arm in task['structured']['arms']:
                updates=read(path.parent/'UPDATES.json');item['updates']=updates;summary['accepted_updates']=sum(r['accepted']for r in updates['iterations']);summary['growth_status']='ACCEPTED'if any(r['status']=='ACCEPTED_SWEEP'for r in updates['growth'])else'NOT_ACCEPTED'
                final_sweep=path.parent/'STEP_035/SWEEP.npz'
                if final_sweep.exists():
                    sw=np.load(final_sweep);summary['growth_length_mm']=float(np.linalg.norm(np.diff(sw['centerline'],axis=0),axis=1).sum());summary['growth_volume_mm3']=float(geo['volume_mm3']-geometry(initial,initial,initial,base,chart,gns)[1]['volume_mm3']);summary['cross_section_min_mm']=float(2*sw['axes'].min());summary['cross_section_max_mm']=float(2*sw['axes'].max())
                for entry in updates['growth']:
                    if entry['status']!='ACCEPTED_SWEEP':failures.append(dict(type='SCIENTIFIC_NEGATIVE',case=case,arm=arm,symptom=entry['status'],confirmed_cause='Persisted multiview support / candidate gates',evidence=str(path.parent/'UPDATES.json'),permanent_rule=False))
                if not summary['accepted_updates']:failures.append(dict(type='SCIENTIFIC_NEGATIVE',case=case,arm=arm,symptom='NO_ACCEPTED_UPDATE',confirmed_cause='All candidate gates rejected; initial prediction retained within this route',evidence=str(path.parent/'UPDATES.json'),permanent_rule=False))
            rows.append(item);bv.append(summary)
            if path is not None:require(sha256(path)==digest,'BODY_IMMUTABLE','Evaluation copies only')
    for c in task['structured']['cases']:
        for arm in task['structured']['arms']:
            b=next((r for r in bv if r['case']==c and r['arm']=='INITIAL'),None);a=next((r for r in bv if r['case']==c and r['arm']==arm and r['status']=='NUMERIC'),None)
            if a and a['GT_MAE_mm']>=b['GT_MAE_mm']:failures.append(dict(type='SCIENTIFIC_NEGATIVE',case=c,arm=arm,symptom='NO_GT_SURFACE_GAIN',confirmed_cause='Frozen prediction independently evaluated; failure is not automatically a permanent rule',evidence=f'{c}/{arm}_GT_ALIGNED.npz',permanent_rule=False))
    for name,data in [('BODY_METRICS',bv),('PER_VIEW_METRICS',pv),('GEOMETRY_METRICS',gv),('RING_COLLISION_METRICS',rv)]:write_csv(attempt/'metrics'/(name+'.csv'),data)
    for i,f in enumerate(failures):f.update(id=f'SB002-{i+1:03d}',cause_status='confirmed'if f['type']=='SCIENTIFIC_NEGATIVE'else'observed_only',repair='Retain frozen negative prediction; no GT-based retuning',regression=['structured_regression'],rule_status='candidate',review=dict(status='unreviewed'))
    dump(attempt/'EVALUATION.json',dict(rows=rows,summary=bv,target_cases=3,arms=4,GT_read_only_after_all_predictions_frozen=True,GT_parameter_selection=False));dump(attempt/'FAILURE_REGISTRY.json',dict(records=failures,reviewed_for_permanent_promotion=False))
    return outputs(attempt,dict(status='PASS',body_rows=len(rows),scientific_failures=failures,GT_read_by_evaluator=True))

def dispatch(stage,task,attempt):
    if stage=='structured_regression':return regression(attempt)
    if stage=='G0_source_audit':return audit(task,attempt)
    if stage.startswith('G1_'):return predict(task,attempt,stage[3:])
    if stage=='G2_evaluate':return evaluate(task,attempt)
    if stage=='G4_visualize':
        from figures import visualize
        return visualize(task,attempt)
    raise ValueError(stage)
