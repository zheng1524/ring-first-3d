"""Post-output attribution and failure audit; no changes to selected geometry."""
from evaluate_d import *
def main():
    rows=[];sourceaudit=[];groups=[]
    for sid in scene_ids():
        a=pointset(sid,'ViewPartition_Cleaned_F2');mask=np.array([not case(a['references'][j]).get('new_reference',False)for j in a['reference_index']]);P=a['P'][mask];C=a['C'][mask];historical=dict(P=P,C=C,reference_index=a['reference_index'][mask],original_ids=a['original_ids'][mask],references=a['references']);ncov=normal_coverage(historical)
        for t in eval_targets(sid):
            base=projection(P,C,t);full=projection(a['P'],a['C'],t);B=metric(base,t);F=metric(full,t);rows.append(dict(scene=sid,group=sid[:3],target=t['id'],role=t['role'],without_new_HERO=B,with_new_HERO=F,coverage_delta=float(F['coverage']-B['coverage']),common=common_metric(base,full,t),interpretation='marginal source attribution on frozen F2 output; not a separately retuned method',normal_coverage_without_new_HERO=ncov))
        for rank,cid in enumerate(a['references']):
            z=np.load(R/f'local_results/pointcloud_blocks/{sid}/ViewPartition_Cleaned_F2/{cid}.npz');raw=np.load(R/f'local_results/pointcloud_blocks/{sid}/Raw_F2/{cid}.npz');s=source(cid);cl=np.load(R/f'local_results/cleaned/{cid}.npz');accepted=z['accepted'];F=s['F'][accepted[s['F']].all(1)];new=accepted&(raw['class_id']==EXPLAINED)if rank else np.zeros(len(accepted),bool);face_areas=area(s['P'],F);face_labels=face_components(F);component_areas=np.bincount(face_labels,weights=face_areas)if len(F)else np.zeros(0);sourceaudit.append(dict(scene=sid,reference=cid,rank=rank,new_HERO=case(cid).get('new_reference',False),accepted_N=int(accepted.sum()),became_novel_after_cleaning_raw_explained_N=int(new.sum()),accepted_unreliable_normal_N=int((accepted&~z['normal_reliable']).sum()),accepted_unreferenced_by_complete_faces_N=int((accepted&~np.isin(np.arange(len(accepted)),np.unique(F))).sum()),accepted_complete_original_faces=len(F),accepted_complete_face_components=len(np.unique(face_labels)),accepted_complete_original_face_area_mm2=float(face_areas.sum()),largest_complete_source_face_component_mm2=float(component_areas.max())if len(component_areas)else 0.,protected_possible_stalk_N=int(cl['protected_possible_stalk'].sum()),stalk_in_Cleaned_N=int((cl['protected_possible_stalk']&~cl['clean_removed']).sum()),stalk_in_F2_source_N=int((cl['protected_possible_stalk']&accepted).sum()),not_true_anatomical_labels=True))
    both('new_HERO_marginal_validation',rows);both('F2_source_structure_audit',sourceaudit)
    for g in ['G01','G06','G07','G08']:
        cc=[c for c in cases()if c['group']==g];ss=[r for r in load(R/'metrics/multigroup_summary.json')if r['group']==g];groups.append(dict(group=g,videos=len(set(c['video']for c in cc)),total_references=len(cc),new_HERO_references=sum(c.get('new_reference',False)for c in cc),raw_observation_exposures=sum(c['points']for c in cc),F2_numeric_output_scenes=len(ss),certified_physical_measurement_success=False,normal_or_stress='UNQUALIFIED_CAMERA_STRESS'if g=='G07'else'LIMITED_STRESS'if g=='G08'else'NORMAL_CONDITIONAL',only_one_physical_case=True))
    both('physical_group_summary',groups)
    failures=[]
    for e in load(R/'metrics/registration_edges.json'):
        if e['status']!='VERIFIED_ADJACENT_CONSTRAINT':failures.append(dict(group=e['group'],stage='P5/P6',source=e['id'],status=e['status'],reason=str(e.get('constraints',{}))+'; '+e.get('independent_frame_status','no independent frame'),evidence='figures/P5_adjacent_registration/'+('G07_G08'if e['group']in ['G07','G08']else e['group'])+'.png'))
    for r in load(R/'metrics/new_reference_sources.json'):
        if not r['success']:failures.append(dict(group=r['group'],stage='P7',source=r['reference'],status=r.get('status','FAILED'),reason=r.get('failure',''),evidence='figures/P4_mast3r_matching/G01.png'))
    gate=load(R/'metrics/CROSSVIDEO_GATE.json');failures.append(dict(group='G01',stage='P9',source='004↔005',status=gate['status'],reason='independent geometry checks failed despite conditional matches/poses; depth conflicts and residual double layers persist',evidence='figures/P9_final_comparison/G01.png'))
    for r in sourceaudit:
        if r['rank']and(r['accepted_unreliable_normal_N']or r['accepted_complete_face_components']>1):failures.append(dict(group=r['scene'][:3],stage='P8',source=r['reference'],status='OBSERVED_ADDITION_NOT_GEOMETRY_CERTIFIED',reason=str(r),evidence='figures/P8_selective_pointcloud/'+('G07_G08'if r['scene'][:3]in ['G07','G08']else r['scene'][:3])+'.png'))
    both('failure_ledger',failures);print('ATTRIBUTION complete; frozen F2 unchanged',flush=True)
if __name__=='__main__':main()
