"""Read-only scientific delivery invariants. No model import or GPU computation."""
from common import *
def main():
    p=protocol();expected={f'{s}_{order}_F{i}'for s,ii in p['orders'].items()for order in ['forward','reverse']for i in range(len(ii))};assert len(expected)==26
    denominators={};model_total=0;max_gpu=0.;mesh_inventory=[]
    for scene,ii in p['orders'].items():
        native_denom=sum(int(native(c)['valid'].sum())for c in ii);denominators[scene]=native_denom
        for order in ['forward','reverse']:
            source_order=p['orders'][scene]if order=='forward'else p['reverse_orders'][scene];previous_known=None;previous_count=None
            assert source_order==(ii if order=='forward'else list(reversed(ii)))
            start=load(R/f'provenance/{scene}_{order}_SEQUENCE_START.json');done=load(R/f'provenance/{scene}_{order}_SEQUENCE_DONE.json');assert start['empty_initial_count']and start['empty_initial_latent']and done['completed_prefixes']==len(ii)
            assert not done['denials'];assert not any('/meshes/'in name or name.endswith('.glb')or name.endswith('.ply')for name in done['read_files']),'PREDICTION_MUST_NOT_READ_FUSED_MESH'
            for i,cid in enumerate(source_order):
                tag=f'{scene}_{order}_F{i}';run=load(R/f'metrics/{tag}_RUN.json');m=load(R/f'metrics/{tag}_METRICS.json');assert run['sources']==source_order[:i+1]and run['source_added']==cid
                assert run['weights_bitwise_unchanged']and run['optimizer_steps']==0 and run['strict_parameter_N']==1403920 and not run['GT'];assert run['official_GPU_unprojection_max_mm']<1e-4
                ev=run['actual_official_call_events'];assert [r['module']for r in ev]==['_extractor','_fusion','_integrator','_translator'];assert ev[-1]['input_shapes'][0][0]==run['known_voxel_N'];model_total+=1;max_gpu=max(max_gpu,run['peak_GPU_MiB'])
                field=np.load(R/'local_results'/f'{tag}_field.npz');state=np.load(R/'local_results'/f'{tag}_latent.npz');known=field['known'];latent=state['latent'];counter=latent[:,:,:,-1]
                assert latent.shape==(128,128,128,17)and state['count'].shape==(128,128,128);assert np.isfinite(latent).all()and np.isfinite(field['sdf_raw']).all();assert np.array_equal(known,np.abs(latent).sum(3)>0);assert np.array_equal(counter>0,known);assert state['count'].max()==0;assert counter.max()<=i+1
                if previous_known is not None:assert not (previous_known&~known).any();assert (counter>=previous_count).all()
                previous_known=known;previous_count=counter.copy();assert np.all(field['sdf_MC_unknown_positive_sentinel'][~known]==np.float32(.04))
                rr=m['rays'];assert sum(a['fixed_original_native_N']for a in rr)==native_denom
                for a in rr:
                    assert a['CAD_visible_N']+a['CAD_occluded_N']==a['fixed_original_native_N'];assert a['hit_N']+a['miss_N']==a['CAD_visible_N'];assert a['agree_N']+a['near_N']+a['far_N']==a['hit_N'];assert a['cleanup_removed_N']+a['input_available_N']==a['fixed_original_native_N']
                for suffix in ['raw_mm.ply','flat_mm.ply','smooth_normals_mm.ply','SI_m.glb']:mesh_inventory.append(asset(R/'meshes'/f'{tag}_{suffix}'))
    for a in load(R/'provenance/BEFORE_GPU.json')['inputs']:
        old=Path(a['path']);assert sha(R/'frozen_inputs'/old.parent.name/old.name)==a['sha256']
    for a in load(R/'provenance/ORIGINAL_SHA_START.json')['files']:assert sha(a['path'])==a['sha256']
    for a in load(R/'provenance/OFFICIAL_CHECKED_FILES.json')['files']:assert sha(a['path'])==a['sha256']
    for a in load(R/'provenance/DELIVERY_CODE.json')['files']:assert sha(a['path'])==a['sha256']
    required=['TECHNICAL_VERSION_LOCK.md','VIEW_SELECTION_8.md','NEURALFUSION_OFFICIAL_PIPELINE_AUDIT.md','TECHNICAL_REPORT.md','FAILURE_LEDGER.md','VIEW_EXPANSION_20_30_PLAN.md','REPRODUCE.md']
    assert all((R/name).stat().st_size>100 for name in required);assert len(list((R/'figures').glob('Fig*.png')))==4
    assert all(a['MC_replayed_exact']=='True'and a['flat_smooth_geometry_identical']=='True'for a in rows(R/'metrics/MESH_EXTRACTION_AND_SHADING_AUDIT.csv'))
    status=load(R/'TASK_STATUS.json');assert status['GPU_forward_N']==26 and status['optimizer_steps']==0 and status['new_HERO_N']==0 and not status['enhanced_20_30_run']
    result=dict(status='PASS_DELIVERY_AND_ENGINEERING_INVARIANTS_NOT_PHYSICAL_ACCURACY',prefix_N=model_total,mesh_deliverable_files_N=len(mesh_inventory),fixed_original_native_denominators=denominators,peak_GPU_MiB=max_gpu,input_and_model_SHA_unchanged=True,code_SHA_verified=True,all_prefix_Translator_calls=True,latent_count_and_masks_consistent=True,raw_observation_arithmetic=True,mesh_geometry_replayed_N=26,GT=False,optimizer_steps=0)
    save('metrics/DELIVERY_VERIFICATION.json',result);table('metrics/MESH_ARTIFACTS.csv',mesh_inventory);print(clean(result))
if __name__=='__main__':main()
