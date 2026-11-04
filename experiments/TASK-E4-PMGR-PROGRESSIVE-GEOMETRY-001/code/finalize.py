"""Aggregate every planned run without filtering unfavourable outcomes."""
from inputs import *
from collections import Counter
import itertools
def main():
    pr=protocol();rows=[];stages=[];modes=[];spectra=[];views=[];failure=[];checkpoints=[];paired=[];index=[]
    for scene,initial,seed,arm in itertools.product(pr['scenes'],pr['initials'],pr['seeds'],pr['arms']+pr['supplemental']):
        key=f'{scene}__{initial}__s{seed}__{arm}';file=R/'metrics/runs'/(key+'.json')
        if not file.exists():rows.append(dict(scene=scene,initial=initial,seed=seed,arm=arm,status='NOT_RUN',stage_count=0));failure.append(dict(case_id=key,reason='NOT_RUN',GT='NOT_EVALUABLE'));continue
        x=load(file);index.append(asset(file));ss=x.get('stages',[]);reasons=Counter(reason.split(':')[0]for step in x.get('steps',[])for trial in step['rejected']for reason in trial['reasons']);r=dict(case_id=key,scene=scene,source_video=scene,initial=initial,seed=seed,arm=arm,status=x['status'],stage_count=len(ss),qualification=pr['scenes'][scene]['tier'],A_refs=pr['scenes'][scene]['A'],B_ref=pr['scenes'][scene]['B'],gradient_evaluations=x.get('gradient_evaluations',0),accepted_updates=x.get('accepted_updates',0),accepted_nonzero_updates=sum(s['accepted']and s['geometry_checks'].get('max_step_mm',0)>1e-8 for s in x.get('steps',[])),rejected_updates=sum(not s['accepted']for s in x.get('steps',[])),line_search_rejection_reasons=dict(reasons),seconds=x['seconds'],render_calls=x.get('render_calls'),J_seconds=sum(j['seconds']for j in x.get('spectra',[])),J_render_calls=sum(j['render_calls']for j in x.get('spectra',[])),peak_GPU_bytes=x.get('peak_GPU_bytes'),tau_mm=x.get('trust_tau_mm'),P0_ring_inside_N=x.get('P0_ring_inside_N'),P0_ring_min_signed_mm=x.get('P0_ring_min_signed_mm'))
        if len(ss)==4:
            end=ss[-1];r.update(final_active=end['active_N'],max_displacement_mm=end['max_P0_displacement_mm'],nonzero_deformation=end['max_P0_displacement_mm']>1e-6,volume_ratio=end['geometry']['volume_mm3']/ss[0]['geometry']['volume_mm3'])
            for role in ['A','B']:
                ev=[v for v in end['evaluations']if v['role']==role];base=[v for v in ss[0]['evaluations']if v['role']==role];r.update({role+'_IoU':float(np.mean([v['IoU']for v in ev])),role+'_IoU_change':float(np.mean([a['IoU']-b['IoU']for a,b in zip(ev,base)])),role+'_depth_hit_N':sum(v['depth_hit_N']for v in ev),role+'_fixed_depth_N':sum(v['depth_fixed_N']for v in ev),role+'_relative_D_MAE_mm':float(np.mean([v['relative_depth_error_mm']['MAE']for v in ev])),role+'_common_relative_D_MAE_mm':float(np.mean([v['common_P0_relative_depth_mm']['MAE']for v in ev])),role+'_common_P0_relative_D_MAE_mm':float(np.mean([v['P0_common_relative_depth_mm']['MAE']for v in ev]))})
            if r['B_depth_hit_N']<sum(v['depth_hit_N']for v in ss[0]['evaluations']if v['role']=='B'):failure.append(dict(case_id=key,reason='HELDOUT_FIXED_COVERAGE_DECREASE',before=sum(v['depth_hit_N']for v in ss[0]['evaluations']if v['role']=='B'),after=r['B_depth_hit_N']))
            for st in ss:
                si=ss.index(st);cp=np.load(R/'local_results'/key/(st['stage']+'.npz'));prev=np.load(R/'local_results'/key/(ss[max(0,si-1)]['stage']+'.npz'));stage_steps=[s for s in x['steps']if s['stage']==st['stage']]
                stages.append(dict(case_id=key,scene=scene,initial=initial,seed=seed,arm=arm,stage=st['stage'],active_N=st['active_N'],gradient_evaluations=st['gradient_evaluations'],accepted_updates=st['accepted_updates'],stage_accepted_updates=sum(s['accepted']for s in stage_steps),stage_rejected_updates=sum(not s['accepted']for s in stage_steps),max_previous_stage_displacement_mm=float(np.linalg.norm(cp['V']-prev['V'],axis=1).max()),max_P0_displacement_mm=st['max_P0_displacement_mm'],**st['geometry']))
                for ev in st['evaluations']:
                    native=np.load(R/'local_results'/key/(st['stage']+'__'+ev['source']+'.npz'));zz=native['z'];cad=obs(ev['source'])['cad'];extra=dict(CAD_occluded_native_N=int((np.isfinite(zz)&(zz>cad+.05)).sum()),no_first_surface_native_N=int((~np.isfinite(zz)).sum()),depth_unknown_N=int((~native['hit']).sum()))
                    extra.update(A_mask_loss=None,A_relative_D_loss=None,A_soft_H_loss=None,A_data_loss=None,A_visible_H_anchor_N=None)
                    if ev['role']=='A':
                        vi=pr['scenes'][scene]['A'].index(ev['source']);vp=st['per_view'][vi];extra.update(A_mask_loss=vp['M'],A_relative_D_loss=vp['D'],A_soft_H_loss=vp['H'],A_data_loss=vp['loss'],A_visible_H_anchor_N=vp['H_N'])
                        if st['stage']=='P3':
                            original=ss[0]['per_view'][vi]
                            if vp['H_N']<original['H_N']:failure.append(dict(case_id=key,source=ev['source'],reason='A_VISIBLE_ANCHOR_COUNT_DECREASE',before=original['H_N'],after=vp['H_N']))
                            original_eval=next(vv for vv in ss[0]['evaluations']if vv['source']==ev['source'])
                            if ev['mask_hit_N']<original_eval['mask_hit_N']:failure.append(dict(case_id=key,source=ev['source'],reason='A_FIXED_MASK_COVERAGE_DECREASE',before=original_eval['mask_hit_N'],after=ev['mask_hit_N'],fixed_N=ev['fixed_mask_N']))
                    views.append(dict(case_id=key,scene=scene,initial=initial,seed=seed,arm=arm,stage=st['stage'],**ev,**extra))
            for st in ss:
                path=R/'local_results'/key/(st['stage']+'.npz');checkpoints.append(dict(case_id=key,stage=st['stage'],**asset(path),required_frozen_basis=asset(R/'inputs'/f'{scene}_{initial}_basis.npz'),state='a,Adam m/v/time,active,seed,gradient evaluations; fixed-lr no scheduler'))
        basis=dict(np.load(R/'inputs'/f'{scene}_{initial}_basis.npz'));energy=basis['mass'][:,None]*basis['phi']**2;area=energy.sum(0)**2/np.maximum((basis['mass'][:,None]*basis['phi']**4).sum(0),1e-15)
        for m in x.get('mode_rows',[]):
            label='MULTI_PARTITION_CONSISTENT_PROXY'if m['classification']=='MULTI_INDEPENDENT_CONSISTENT'else m['classification']
            modes.append(dict(case_id=key,arm=arm,stage=m['stage'],mode=m['mode'],frequency=m['frequency'],effective_support_area_mm2=float(area[m['mode']]),counterfactual_gate_status=m['status'],gate_applied=arm=='PMGR',activation_status=('ACTIVE'if m['actual_active']else'INACTIVE'),actual_active=m['actual_active'],gate_reasons='|'.join(m['reasons']),J_norm=m['J_norm'],independent_ratio=m['independent_ratio'],source_support_N=m['source_support_N'],partition_support_N=m['partition_support_N'],conflict_fraction=m['gradient_conflict_fraction'],classification=label,raw_gate_label=m['classification'],statistical_independence_certified=False))
        for j in x.get('spectra',[]):spectra.append(dict(case_id=key,stage=j['stage'],candidate_plus_P0_rank=j['rank'],condition=j['condition'],valid_row_N=j['valid_row_N'],censored_row_N=j['censored_row_N'],seconds=j['seconds'],render_calls=j['render_calls'],singular_values=j['singular_values'],source_gradient_cosine=j['cosine'],FD_controls=j['fd_controls']))
        for reason in x.get('failures',[]):failure.append(dict(case_id=key,reason=reason))
        if x.get('P0_ring_inside_N',0):failure.append(dict(case_id=key,reason='FROZEN_P0_ALREADY_HAS_RING_COLLISION_PROXY',N=x['P0_ring_inside_N'],min_signed_mm=x['P0_ring_min_signed_mm']))
        rows.append(r)
    for scene,initial,seed in itertools.product(pr['scenes'],pr['initials'],pr['seeds']):
        rr={r['arm']:r for r in rows if(r['scene'],r['initial'],r['seed'])==(scene,initial,seed)and r['status']=='FIXED_BUDGET_COMPLETED'}
        if'PMGR'not in rr:continue
        p=rr['PMGR']
        for arm,c in rr.items():
            if arm=='PMGR':continue
            cid=pr['scenes'][scene]['B'][0];o=obs(cid);base=R/'local_results';pa=np.load(base/p['case_id']/('P3__'+cid+'.npz'));ca=np.load(base/c['case_id']/('P3__'+cid+'.npz'));p0=np.load(base/p['case_id']/('P0__'+cid+'.npz'));common=pa['pair_hit']&ca['pair_hit']&p0['pair_hit'];pp=o['pairs'][common]
            errors=[z[pp[:,0]]-z[pp[:,1]]-o['delta'][common]for z in [pa['z'],ca['z'],p0['z']]];mae=[float(abs(e).mean())if len(e)else np.nan for e in errors]
            paired.append(dict(scene=scene,initial=initial,seed=seed,control=arm,PMGR_active=p['final_active'],control_active=c['final_active'],B_IoU_PMGR_minus_control=p['B_IoU']-c['B_IoU'],B_common_relative_D_PMGR_minus_control_mm=mae[0]-mae[1],B_joint_common_fixed_pair_N=int(common.sum()),B_registered_fixed_pair_N=256,B_joint_common_PMGR_MAE_mm=mae[0],B_joint_common_control_MAE_mm=mae[1],B_joint_common_P0_MAE_mm=mae[2],A_IoU_PMGR_minus_control=p['A_IoU']-c['A_IoU'],PMGR_gradient_evaluations=p['gradient_evaluations'],control_gradient_evaluations=c['gradient_evaluations'],PMGR_seconds=p['seconds'],control_seconds=c['seconds']))
    control=load(R/'metrics/LAPLACIAN_SYNTHETIC_CONSISTENCY.json')if(R/'metrics/LAPLACIAN_SYNTHETIC_CONSISTENCY.json').exists()else{}
    if control and not control['passed']:failure.append(dict(case_id='SYNTHETIC_SPHERE_CONTROL_NOT_A_PHYSICAL_GROUP',reason='ARPACK_REPEATED_EIGENVALUE_COMPLETENESS_FAIL',details='Original failed test preserved; actual8 frozen spectra independently checked against dense reference; no fitting inputs changed'))
    table('metrics/CASE_ARM_SEED_RESULTS.csv',rows);save('metrics/CASE_ARM_SEED_RESULTS.json',rows);table('metrics/STAGE_METRICS.csv',stages);table('metrics/PER_VIEW_LOSS.csv',views);table('metrics/MODE_UNLOCK.csv',modes);table('metrics/JACOBIAN_SPECTRUM.csv',spectra);table('metrics/FAILURES.csv',failure);save('metrics/FAILURES.json',failure);table('metrics/PAIRED_ABLATION.csv',paired);save('metrics/PAIRED_ABLATION.json',paired);save('assets_index/CHECKPOINTS.json',checkpoints);save('assets_index/FULL_RUN_JOURNALS.json',index)
    table('metrics/EXECUTION_COVERAGE.csv',[dict(case_id=x['case_id'],scene=x['scene'],initial=x['initial'],seed=x['seed'],arm=x['arm'],qualification=x['qualification'],P0='DONE'if x['stage_count']>=1 else'NOT_RUN',P1='DONE'if x['stage_count']>=2 else'NOT_RUN',P2='DONE'if x['stage_count']>=3 else'NOT_RUN',P3='DONE'if x['stage_count']>=4 else'NOT_RUN',status=x['status'])for x in rows])
    summary=dict(planned_runs=80,completed=sum(r['status']=='FIXED_BUDGET_COMPLETED'for r in rows),hard_failures=sum(r['status']=='HARD_FAILURE'for r in rows),not_run=sum(r['status']=='NOT_RUN'for r in rows),physical_groups=4,strict_independent_scientific_success=0,GT='NOT_EVALUABLE',total_seconds=sum(r['seconds']for r in rows),gradient_evaluations=sum(r['gradient_evaluations']for r in rows),per_scene={})
    for scene in pr['scenes']:
        summary['per_scene'][scene]={}
        for arm in pr['arms']+pr['supplemental']:
            rr=[r for r in rows if r['scene']==scene and r['arm']==arm and r['status']=='FIXED_BUDGET_COMPLETED'];summary['per_scene'][scene][arm]=dict(N=len(rr),**{k:float(np.mean([r[k]for r in rr]))if rr else None for k in ['A_IoU','B_IoU','A_IoU_change','B_IoU_change','B_relative_D_MAE_mm','B_common_relative_D_MAE_mm','B_common_P0_relative_D_MAE_mm','A_depth_hit_N','B_depth_hit_N','final_active','max_displacement_mm','volume_ratio']})
    save('metrics/SUMMARY.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
