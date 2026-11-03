"""Current Gate receipt, fixed source selection, inherited cleanup and metric domains."""
from common import *
import common as shared
import shutil
from scipy import ndimage


def main():
    assert not(TASK/'config/EXPERIMENT_FROZEN.json').exists(),'ALREADY_PREPARED'
    gate=load(HISTORY_N0/'config/CAMERA_GATE_RESULTS.json');rules=load(HISTORY_N0/'config/CAMERA_GATE_RULES.json')
    by={r['source']:r for r in gate['sources']};checks=[]
    for cid in ALL_IDS:
        r=by[cid];rr=next(v for v in gate['Ring']if v['camera']==cid)
        assert rr['Ring_pass']==(rr['adequate']and rr['visible_contour']['MAE']<=rules['ring_max_MAE_px']and rr['visible_contour']['p95']<=rules['ring_max_p95_px'])
        relations=[v for v in gate['pairs']if v['selected_for_gate']and cid in [v['A'],v['B']]]
        contradiction=rr['clear_contradiction']or any(v['clear_contradiction']for v in relations)
        required=set(gate['anchors'][r['scene']])-{cid};present={v['B']if v['A']==cid else v['A']for v in relations}
        incomplete=(not rr['Ring_pass'])or bool(required-present)or any(not v['pair_pass']for v in relations)or not r['observability']['full_local_numerical_rank']
        status='UNQUALIFIED_GEOMETRY'if contradiction else('INSUFFICIENT_EVIDENCE'if incomplete else'CONDITIONAL_USABLE')
        assert status==r['qualification']and not contradiction and r['admission']=='CONDITIONAL_RESEARCH_INPUT'
        c=CC[cid]
        for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:assert sha(c[k])==c['files'][k]['sha256']
        checks.append(dict(source=cid,scene=r['scene'],block=r['block'],qualification=status,admission=r['admission'],Ring_pass=r['Ring_pass'],Ring_p95_px=r['Ring_p95_px'],current_rule_recomputed=True,legacy_source_camera_qualified=c['source_camera_qualified']))
    # Save global selection before any network inference or cleanup output.
    old_R=shared.R;shared.R=TASK;globals()['R']=TASK
    save('config/CAMERA_GATE_RULES.json',rules);save('config/CAMERA_GATE_RESULTS.json',gate)
    save('config/SOURCE_SELECTION.json',dict(orders=ORDERS,reason='G01 fixed CORE; G06 first3 frozen N0 order coverB2/B1/B3; G08 legacy CORE plus strictly conditional-usable B3/B4, source indices fixed',G07_not_selected='only2 admitted blocks; other B3 sources NOT_ADMITTED, no relaxed thresholds',selection_before_new_model=True,N_M1_historical=0,approved_new_baseline=1000,target_total_updates=10000))
    table('metrics/CURRENT_CAMERA_GATE_RECHECK.csv',checks)
    save('provenance/VERSION_RECEIPT.json',dict(files=[asset(REPO/'docs/KEY_TECHNICAL_VERSION_v1.0.md'),asset(REPO/'docs/KEY_TECHNICAL_VERSION_E3_SDF_CANDIDATE_v0.1.md'),asset(HISTORY_N0/'config/CAMERA_GATE_RULES.json'),asset(HISTORY_N0/'config/CAMERA_GATE_RESULTS.json'),asset(HISTORY_N0/'code/prepare.py'),asset(PREV/'config/PREREGISTERED.json')],old_G06_G08_camera_boolean_not_used_as_current_qualification=True))
    for folder in ['native','crops']:(TASK/'frozen_inputs'/folder).mkdir(parents=True,exist_ok=True)
    for scene in ['G01_004','G06_004']:
        for cid in ORDERS[scene]:
            for folder in ['native','crops']:
                src=HISTORY_N0/'frozen_inputs'/folder/(cid+'.npz');dst=TASK/'frozen_inputs'/folder/(cid+'.npz');shutil.copy2(src,dst);assert sha(src)==sha(dst)
    extract(A2/'code/common.py',['neighbours'],globals())
    # Exact N0 one-pass algorithm, only the selected G08 input set is new.
    globals()['LEGACY_V6']=[];globals()['CORE']=ORDERS['G01_004']
    extract(HISTORY_N0/'code/prepare.py',['baseline','cleanup','make_domain'],globals())
    cleanup('G08_005',ORDERS['G08_005'],by)
    for cid in ORDERS['G08_005']:
        cp=make_crop(cleaned(cid));np.savez_compressed(TASK/'frozen_inputs/crops'/(cid+'.npz'),**cp)
    domains=load(HISTORY_N0/'config/EXPERIMENT_FROZEN.json')['domains']
    domains={scene:domains[scene]for scene in ['G01_004','G06_004']}
    domains['G08_005']=make_domain('G08_005',ORDERS['G08_005'])
    save('config/EXPERIMENT_FROZEN.json',dict(domains=domains,orders=ORDERS,source_selection=asset(TASK/'config/SOURCE_SELECTION.json'),camera_rules=asset(TASK/'config/CAMERA_GATE_RULES.json'),geometry_generated_by_own_route=True,GT=False))
    save('provenance/NATIVE_AND_CROP_INPUTS.json',dict(files=[asset(TASK/'frozen_inputs'/d/(cid+'.npz'))for d in ['native','crops']for cid in ALL_IDS]))
    globals()['R']=old_R;shared.R=old_R
    print('ASSETS_PREPARED',ORDERS,'domains',clean(domains),flush=True)


if __name__=='__main__':main()
