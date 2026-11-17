"""Independent, fixed-scale GT fits and fixed INITIAL→GT diagnostic copies."""
import csv
from pathlib import Path
import numpy as np
from io_utils import TD,OLD,load_inputs,source_folder,read,body,dump,sha
from ring_first_3d.synthetic.io import fetch,outputs
from ring_first_3d.multisurface.geometry import scene,sample_mesh,closest
from ring_first_3d.multisurface.evaluate import fixed_stats
from ring_first_3d.inita.evaluate import legacy_namespace
from ring_first_3d.synthetic.raster import ray_map
from projection_gate import stats
from scipy.ndimage import binary_dilation

def write_csv(path,rows):
    path.parent.mkdir(exist_ok=True,parents=True);keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='')as f:
        w=csv.DictWriter(f,keys,lineterminator='\n');w.writeheader();w.writerows(rows)
def shape(pred,gt):
    P,_,_=sample_mesh(pred['V'],pred['F'],12000,20261117);G,_,_=sample_mesh(gt['V'],gt['F'],12000,20261118)
    Q,_,_=closest(scene(gt['V'],gt['F']),P);d=np.linalg.norm(P-Q,axis=1)
    Q,_,_=closest(scene(pred['V'],pred['F']),G);e=np.linalg.norm(G-Q,axis=1)
    st=fixed_stats(np.r_[d,e]);pr=float((d<=.5).mean());re=float((e<=.5).mean())
    return dict(Chamfer_MAE_mm=st['MAE'],Chamfer_median_mm=st['median'],Chamfer_P95_mm=st['p95'],Chamfer_max_mm=st['maximum'],Fscore_at0p5mm=2*pr*re/max(1e-12,pr+re),GT_coverage_at0p5mm=re,N_per_direction=12000)

def evaluate(t,attempt):
    root=attempt.parents[1];freezes={c:fetch(root,'G1_'+c,'PREDICTIONS_FROZEN.json')for c in ['G01','G03']}
    records={c:read(f)['records'][0]for c,f in freezes.items()}
    # All predictor outputs are hash-checked before any GT shape read.
    for c,r in records.items():
        if 'mesh_relative'in r:assert sha(fetch(root,'G1_'+c,r['mesh_relative']))==r['mesh_sha256']
    dump(attempt/'GT_FIRST_ACCESS.json',dict(all_prediction_freezes={c:dict(path=str(p),sha256=sha(p))for c,p in freezes.items()},GT_selection=False,scale_fixed=1))
    ns=legacy_namespace(dict(task_id='TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001'));rows=[];views_all=[];detail=[];failures=[];ringrows=[];lengthrows=[]
    for case in ['G01','G03']:
        initial,views,ring,base,chart,source=load_inputs(case);gt=body(source['GT']['path']);folder=attempt/case;folder.mkdir();np.savez_compressed(folder/'GT.npz',**gt)
        old=source_folder(case);r=records[case];models={'INITIAL':initial,'ITERATION_024':body(old/'STEP_024/BODY.npz'),'OLD_REJECTED':body(old/'GROWTH_PROPOSAL_024/BODY.npz')}
        if 'mesh_relative'in r:models['RECOVERY'if r['status']=='NUMERIC'else'FAILED_ATTEMPT_DIAGNOSTIC']=body(fetch(root,'G1_'+case,r['mesh_relative']))
        previous_T=body(OLD/'review_assets'/case/'INITIAL_GT_ALIGNED.npz')['T']
        rz={v['id']:ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape)['z']for v in views}
        for arm,b in models.items():
            metrics=[]
            for v in views:
                rr=ray_map(b['V'],b['F'],v['K'],v['C'],v['labels'].shape);pred=rr['valid']&(rr['z']>0)&(rr['z']<rz[v['id']]-.05);known=~binary_dilation(v['labels']==2,iterations=3)
                mm=dict(case=case,arm=arm,id=v['id'],video=v['video'],role=v['role'],**stats(pred,v['labels']==1,known));views_all.append(mm);metrics.append(mm)
            T,trials=ns['align'](b['V'],b['F'],gt['V'],gt['F'],10. if source['ring']=='R10'else 5.)
            aligned=dict(b,V=ns['apply'](b['V'],T));common=dict(b,V=ns['apply'](b['V'],previous_T))
            np.savez_compressed(folder/(arm+'_GT_ALIGNED.npz'),**aligned,T=T);np.savez_compressed(folder/(arm+'_INITIAL_GT_FRAME.npz'),**common,T=previous_T)
            dump(folder/(arm+'_RIGID_TRIALS.json'),trials);main=shape(aligned,gt);diagnostic=shape(common,gt)
            row=dict(case=case,arm=arm,status='ACCEPTED_GROWTH'if arm=='RECOVERY'else'DIAGNOSTIC_INVALID'if arm in ['OLD_REJECTED','FAILED_ATTEMPT_DIAGNOSTIC']else'FROZEN_REFERENCE',**main,
                FIT_IoU=float(np.mean([v['IoU']for v in metrics if v['role']=='FIT'])),HOLDOUT_IoU=float(np.mean([v['IoU']for v in metrics if v['role']=='HOLDOUT'])),
                FIT_Boundary_MAE_px=float(np.mean([v['Boundary_MAE_px']for v in metrics if v['role']=='FIT'])),HOLDOUT_Boundary_MAE_px=float(np.mean([v['Boundary_MAE_px']for v in metrics if v['role']=='HOLDOUT'])),
                fixed_INITIAL_GT_Chamfer_MAE_mm=diagnostic['Chamfer_MAE_mm'],fixed_INITIAL_GT_Chamfer_P95_mm=diagnostic['Chamfer_P95_mm'])
            rows.append(row);detail.append(dict(case=case,arm=arm,main=main,fixed_initial_frame=diagnostic,T=T,initial_T=previous_T,projection=metrics))
        pred_folder=fetch(root,'G1_'+case,'PREDICTIONS_FROZEN.json').parent/case/'DEFORM_SWEEP_RECOVERY'
        if (pred_folder/'UPDATES.json').exists():
            u=read(pred_folder/'UPDATES.json');chosen=u['chosen'];lengthrows.append(dict(case=case,status=r['status'],reported_stalk_length_mm=chosen['length']['exposed_stalk_length_mm']if r['status']=='NUMERIC'and chosen.get('length')else'NaN',**(chosen.get('length')or{}),**chosen['geometry']))
            for scope in ['before','after','delta']:ringrows.append(dict(case=case,scope=scope,**chosen['ring'][scope]))
        if r['status']!='NUMERIC':
            failures.append(dict(id='GR001-'+case,case=case,type='SCIENTIFIC_NEGATIVE'if(pred_folder/'UPDATES.json').exists()else'ENGINEERING_FAILURE',symptom='NO_ACCEPTED_GROWTH',
                confirmed_cause=r.get('failure_reasons',[]),evidence=str(pred_folder/'UPDATES.json'),repair='Retain actual attempts; do not relax frozen gates or use GT.',regression='recovery_regression',permanent_rule=False,review=dict(status='unreviewed'),rule_status='candidate'))
            rows.append(dict(case=case,arm='RECOVERY',status='FAILED_NAN',Chamfer_MAE_mm='NaN',Chamfer_P95_mm='NaN',FIT_IoU='NaN',HOLDOUT_IoU='NaN'))
        if 'mesh_relative'in r:assert sha(fetch(root,'G1_'+case,r['mesh_relative']))==r['mesh_sha256']
    for name,data in [('BODY_METRICS',rows),('PER_VIEW_METRICS',views_all),('GROWTH_METRICS',lengthrows),('RING_COLLISION_METRICS',ringrows)]:write_csv(attempt/'metrics'/(name+'.csv'),data)
    dump(attempt/'EVALUATION.json',dict(summary=rows,detail=detail,predictions=records,target_groups=2,GT_after_all_predictions=True,GT_selects_algorithm=False))
    dump(attempt/'FAILURE_REGISTRY.json',dict(records=failures,permanent_promotion_reviewed=False))
    return outputs(attempt,dict(status='PASS',scientific_failures=failures,accepted_growth=sum(r['status']=='NUMERIC'for r in records.values()),target_groups=2,GT_evaluation_only=True))
