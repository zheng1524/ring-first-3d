"""Frozen predictions only: fixed-camera projections and independent rigid GT copies."""
from pathlib import Path
import argparse,ast,itertools,json
import numpy as np
import torch
import open3d as o3d
import trimesh
from scipy.spatial.transform import Rotation
from scipy.stats import qmc
from scipy.ndimage import binary_dilation
import pipeline as p
from ring_first_3d.mainline.paths import LINEAGE,activate
from ring_first_3d.mainline.native.io import sha256,save_json
from ring_first_3d.synthetic.raster import ray_map
from ring_first_3d.multisurface.geometry import scene
from ring_first_3d.multisurface.evaluate import fixed_stats
T=p.TASK;OUT=T/'runs/RF_ONLY_V1';SD=activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
from projection_gate import stats
from body_hooks import RingGateAdapter,historical_depth,mesh

def namespaces():
    folder=LINEAGE/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/legacy015'
    ns=dict(np=np,o3d=o3d,trimesh=trimesh,itertools=itertools,Rotation=Rotation,qmc=qmc,scene=scene)
    for file,names in [('evaluate.py',['area_samples','distance','occupied']),('best_rigid015.py',['frames','pca','apply','rigid','interpolate','align']),('safe_geometry.py',['self_intersections'])]:
        tree=ast.parse((folder/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==len(names)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(folder/file),'exec'),ns)
    return ns

def freeze():
    records=[]
    for c in p.cases():
        for arm in ['B0','B1','B2']:
            path=Path(c['initial']['path']) if arm=='B0' else OUT/c['case']/'004/body'/arm/'FINAL.npz'
            valid=path.exists();records.append(dict(group=c['case'],video='004',arm=arm,status='PASS' if valid else 'NOT_RUN',path=str(path) if valid else None,sha256=sha256(path) if valid else None))
    for g in ['G01','G03','G05','G06']:
        for arm in ['B1','B2']:
            path=OUT/g/'004/body'/arm
            assert (path/'TASK_PREDICTION_FROZEN.json').exists() or (path/'FAILURE.json').exists(),str(path)
    save_json(OUT/'PREDICTIONS_FROZEN_BEFORE_GT.json',dict(records=records,GT_read=False,checkpoint_selection='FINAL_FIXED_36; no GT/HOLDOUT selection',all_training_complete=True))

def evaluate():
    freeze_path=OUT/'PREDICTIONS_FROZEN_BEFORE_GT.json';f=p.read(freeze_path);assert f['all_training_complete']
    for rec in f['records']:
        if rec['path']:assert sha256(rec['path'])==rec['sha256']
    # This file is written immediately before first GT content access.
    save_json(OUT/'GT_FIRST_ACCESS.json',dict(freeze=str(freeze_path),sha256=sha256(freeze_path),training_mutation_allowed=False,GT_used_for_hyperparameters=False,alignment='015 symmetric 96-start scale-fixed SE3; evaluation copies only'))
    ns=namespaces();metadata=LINEAGE/'experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/TASK.yaml'
    import yaml
    metapath=yaml.safe_load(metadata.read_text())['inita']['assets']['GT_metadata']['path'];gtmeta={r['case']:r for r in p.read(metapath)}
    shape=[];projections=[];depthrows=[];geometry=[]
    selected=p.read(T/'audit/SELECTED_VIEWS.json')
    for c in p.cases():
        group=c['case'];folder=OUT/group/'004/evaluation';folder.mkdir(parents=True,exist_ok=True)
        records=[r for r in f['records'] if r['group']==group];initial=dict(np.load(c['initial']['path']));ring=dict(np.load(c['static']['RING.npz']['path']));rg=RingGateAdapter(initial,ring)
        gt=dict(np.load(c['GT']['path']));assert sha256(c['GT']['path'])==c['GT']['sha256'];GV,GF=gt['V'],gt['F'];gr=scene(GV,GF);gm=trimesh.Trimesh(GV,GF,process=False);gsi=ns['self_intersections'](GV,GF)['intersections'];G=ns['area_samples'](GV,GF,8192);aligned={};local=[]
        for rec in records:
            arm=rec['arm'];item=dict(group=group,video='004',arm=arm,status=rec['status'],strict_3D_IoU=None,conditional_occupancy_IoU=None,GT_MAE_mm=None,GT_P95_mm=None,Fscore_0_5mm=None,GT_coverage_0_5mm=None,strict_IoU_validity='NOT_EVALUABLE_NO_PREDICTION')
            if not rec['path']:shape.append(item);continue
            body=dict(np.load(rec['path']));V=body['V'];F=body['F'];Fs=body['F_solid'];pm=trimesh.Trimesh(V,Fs,process=False)
            trans,trials=ns['align'](V,F,GV,GF,10.);AV=ns['apply'](V,trans);assert np.isclose(np.linalg.det(trans[:3,:3]),1,atol=1e-6)
            np.savez_compressed(folder/(arm+'_GT_ALIGNED.npz'),**dict(body,V=AV,T=trans));trimesh.Trimesh(AV,Fs,process=False).export(folder/(arm+'_GT_ALIGNED.ply'));save_json(folder/(arm+'_ALIGNMENT.json'),dict(T=trans,scale=1,world_prediction=rec,only_evaluation_copy_changed=True,trials=trials))
            P=ns['area_samples'](AV,F,8192);dp=ns['distance'](gr,P);dg=ns['distance'](scene(AV,F),G);distance=fixed_stats(np.r_[dp,dg]);precision=float((dp<=.5).mean());recall=float((dg<=.5).mean())
            si=ns['self_intersections'](V,Fs)['intersections'];valid=bool(pm.is_volume and gm.is_volume and si==0 and gsi==0)
            strict=valid and not bool(body['inferred_base_faces'].any()) and gtmeta.get(group,{}).get('GT_geometry_complete',False)
            penetration=rg.measure(body);initial_penetration=rg.measure(initial);displacement=np.linalg.norm(V[:len(initial['V'])]-initial['V'],axis=1)
            item.update(GT_MAE_mm=distance['MAE'],GT_P95_mm=distance['p95'],GT_median_mm=distance['median'],GT_max_mm=distance['maximum'],GT_median_relative_to_diagonal=distance['median']/np.linalg.norm(np.ptp(GV,axis=0)),Fscore_0_5mm=2*precision*recall/max(precision+recall,1e-12),GT_coverage_0_5mm=recall,strict_IoU_validity='VALID_SOLID_SOBOL_ESTIMATE' if strict else 'NOT_EVALUABLE_ENTITY_OR_BASE_VALIDITY',GT_pose_is_independent_shape_alignment=True,world_accuracy_claim=False,vertex_displacement_MAE_mm=float(displacement.mean()),vertex_displacement_p95_mm=float(np.percentile(displacement,95)),GT_volume_error_mm3=float(abs(pm.volume-gm.volume)) if valid else None,GT_volume_relative_error=float(abs(pm.volume-gm.volume)/abs(gm.volume)) if valid else None)
            aligned[arm]=(AV,Fs,strict);local.append(item)
            geometry.append(dict(group=group,video='004',arm=arm,watertight=bool(pm.is_watertight),winding_consistent=bool(pm.is_winding_consistent),self_intersections=si,GT_self_intersections=gsi,volume_entity_valid=valid,inferred_base=bool(body['inferred_base_faces'].any()),faces=len(Fs),vertices=len(V),body_ring_penetration_max_mm=penetration['body_max_mm'],initial_body_ring_penetration_max_mm=initial_penetration['body_max_mm'],Ring_to_Body_penetration_max_mm=penetration['ring_max_mm'],initial_Ring_to_Body_penetration_max_mm=initial_penetration['ring_max_mm'],body_penetration_area_mm2=penetration['body_area_mm2'],body_penetration_energy_mm4=penetration['body_energy_mm4'],new_structure_length_mm=0,new_structure_volume_mm3=0,unchanged_growth_rejection='Single-video fitting cannot meet frozen >=2-video growth evidence'))
            for v in selected:
                m=v['meta']
                if m['case']!=group or m['video']!='004':continue
                cam=OUT/group/'004/camera'/m['id']/'ADMISSION.json';status='PASS' if cam.exists() and p.read(cam)['status']=='PASS' else 'FAIL';row=dict(group=group,video='004',arm=arm,id=m['id'],role='FIT' if m['role']=='FIT' else 'HOLDOUT',camera_status=status,IoU=None,Boundary_MAE_px=None,Boundary_Fscore_at2px=None)
                if status=='PASS':
                    a=p.check_input(v);C=np.array(p.read(cam.parent/'CAMERA_RESULT.json')['c2w_mm']);r=ray_map(V,F,a['K'],C,a['labels'].shape);rz=ray_map(ring['V'],ring['F'],a['K'],C,a['labels'].shape)['z'];pred=r['valid']&(r['z']>0)&(r['z']<rz-.05);known=~binary_dilation(a['labels']==2,iterations=3);row.update(stats(pred,a['labels']==1,known))
                    pd=folder/'projections'/arm;pd.mkdir(parents=True,exist_ok=True);np.savez_compressed(pd/(m['id']+'.npz'),predicted=pred,target=a['labels']==1,unknown=~known)
                projections.append(row)
            assert sha256(rec['path'])==rec['sha256'],'World prediction changed by evaluator'
        bounds=np.concatenate([GV]+[a[0] for a in aligned.values()]);lo=bounds.min(0)-.5;hi=bounds.max(0)+.5;Q=lo+(hi-lo)*qmc.Sobol(3,scramble=True,seed=20261108).random_base2(17);og=ns['occupied'](gr,Q)
        save_json(folder/'COMMON_OCCUPANCY_DOMAIN.json',dict(lo=lo,hi=hi,N=len(Q),seed=20261108,all_frozen_arms_share_domain=True))
        for item in local:
            AV,Fs,strict=aligned[item['arm']];op=ns['occupied'](scene(AV,Fs),Q);inter=int((op&og).sum());union=int((op|og).sum());val=inter/max(1,union);item.update(conditional_occupancy_IoU=val,strict_3D_IoU=val if strict else None,occupancy_intersection_N=inter,occupancy_union_N=union,occupancy_N=len(Q))
            pv=[r for r in projections if r['group']==group and r['arm']==item['arm']]
            for role in ['FIT','HOLDOUT']:
                ss=[r for r in pv if r['role']==role];vv=[r['IoU'] for r in ss if r['IoU'] is not None];item[role+'_views_expected']=len(ss);item[role+'_views_evaluable']=len(vv);item[role+'_IoU_admitted_subset']=float(np.mean(vv)) if vv else None;item[role+'_IoU_all_frozen']=float(np.mean(vv)) if len(vv)==len(ss) and vv else None
            shape.append(item)
        if (OUT/group/'004/body/B1/TASK_PREDICTION_FROZEN.json').exists() and (OUT/group/'004/body/B2/TASK_PREDICTION_FROZEN.json').exists():
            norm=p.read(c['static']['NORMALIZATION.json']['path']);chart=p.read(c['static']['CHART.json']['path']);fit=[v for v in selected if v['meta']['case']==group and v['meta']['video']=='004' and v['meta']['role']=='FIT'];case=__import__('types').SimpleNamespace(name=group+'_004',V=initial['V'],center=np.array(norm['center']),scale=norm['scale_mm'],fit=[v['meta']['id'] for v in fit],views={v['meta']['id']:dict(meta=v['meta']) for v in fit});depth=historical_depth(case,chart,OUT/group/'004/body/DEPTH_INPUT',folder)
            for arm in ['B0','B1','B2']:
                path=Path(c['initial']['path']) if arm=='B0' else OUT/group/'004/body'/arm/'FINAL.npz';body=dict(np.load(path));V=torch.tensor(body['V'],dtype=torch.float64,device='cuda');M=mesh(V,body['F'],case)
                for cid in case.fit:
                    with torch.no_grad():loss,info,data=depth.term(M,cid,True)
                    row=dict(group=group,video='004',arm=arm,**info,coverage=info['active_N']/info['fixed_N']);depthrows.append(row);dd=folder/'depth'/arm;dd.mkdir(parents=True,exist_ok=True);np.savez_compressed(dd/(cid+'.npz'),**data)
        save_json(OUT/'BODY_SHAPE_METRICS_PARTIAL.json',shape)
        print('EVALUATED',group,[(r['arm'],r['GT_MAE_mm']) for r in shape if r['group']==group],flush=True)
    save_json(OUT/'BODY_SHAPE_METRICS.json',shape)
    p.table(T/'metrics/ACTUAL_BODY_METRICS.csv',shape);p.table(T/'metrics/PER_VIEW_METRICS.csv',projections);p.table(T/'metrics/GEOMETRY_METRICS.csv',geometry);p.table(T/'metrics/DEPTH_METRICS.csv',depthrows)
    save_json(OUT/'GT_EVALUATION_COMPLETE.json',dict(status='PASS',prediction_freeze_sha256=sha256(freeze_path),world_meshes_unchanged=True,shape_metrics_only_no_absolute_HERO_position_claim=True))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['freeze','evaluate']);a=ap.parse_args();{'freeze':freeze,'evaluate':evaluate}[a.stage]()
