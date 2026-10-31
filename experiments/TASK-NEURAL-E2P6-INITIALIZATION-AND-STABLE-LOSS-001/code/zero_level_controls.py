"""Separate opacity from front crossing on the SAME frozen real-neural controls."""
from common import *
from stable_losses import sdf_only,packet
from stable_test import field_case_bias

def main():
    rows=[];trace_fixes=[];states=[]
    for scene,refs in selected().items():
        domain=domains()[scene]
        for field in ['NORMAL','POSITIVE','NEGATIVE']:
            model,ports=build_model(domain,field_case_bias(scene,field));before=e25.parameter_hash(model)
            if field=='NORMAL':assert before==load(R/'config/SHELL_CALIBRATION_FROZEN.json')[scene]['model_parameter_SHA256']
            for split in ['small','extra']:
                for ref in refs:
                    b=packet(ref,split);p=sdf_only(model,domain,b);obs=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0)
                    high=(p['opacity']>.98)&obs;no_front=high&~p['raw_front_cross'];inside=obs&(p['start_sdf']<0)
                    f=p['raw_sdf'];positive_tail=no_front&(p['start_sdf']>=0)&np.all(np.where(np.isfinite(f),f,np.inf)>0,axis=1)
                    rows.append(dict(scene=scene,source=ref,split=split,control=field,observed_N=int(obs.sum()),
                        front_cross_N=int((obs&p['raw_front_cross']).sum()),front_hit_N=int((obs&p['render_hit']).sum()),
                        high_opacity_N=int(high.sum()),high_opacity_without_front_cross_N=int(no_front.sum()),
                        observed_prefix_starts_inside_N=int(inside.sum()),positive_tail_high_opacity_without_zero_N=int(positive_tail.sum()),
                        high_opacity_is_NOT_zero_crossing=True,ROI_entry_outside_assumed=False,loss_gradient_not_from_hit_count=True))
                    if field=='NORMAL':
                        path=R/f'local_results/initialization/{ref}_{split}.npz';old=np.load(path);before_sha=sha(path)
                        # Fix the trace-only start-SDF placeholder. Primary
                        # opacity/front classification already used true starts.
                        assert np.array_equal(old['render_hit'],p['render_hit']) and np.array_equal(old['raw_front_cross'],p['raw_front_cross'])
                        assert np.max(abs(old['opacity']-p['opacity']))<1e-12
                        data={k:old[k] for k in old.files};data['start_sdf']=p['start_sdf'];np.savez_compressed(path,**data)
                        trace_fixes.append(dict(source=ref,split=split,old_SHA256=before_sha,new_SHA256=sha(path),
                            corrected_field='start_sdf trace only',opacity_and_front_hit_unchanged=True))
            assert before==e25.parameter_hash(model);states.append(dict(scene=scene,control=field,parameter_SHA256=before,unchanged=True,new_calibration_candidate=False))
            print('ZERO_VS_OPACITY',scene,field,'actual entry signs and front crossings; no new calibration',flush=True)
            del model;gc.collect()
    table('metrics/ZERO_LEVEL_VS_OPACITY.csv',rows)
    save('provenance/START_SDF_TRACE_CORRECTION.json',dict(reason='trace returned NaN placeholder although actual front classification already used computed start SDF',
        files=trace_fixes,scientific_metrics_changed=False,gate_changed=False,additional_initialization_search=False))
    save('provenance/ZERO_LEVEL_CONTROL_STATES.json',states)
    print('ZERO_LEVEL_OPACITY_CONTROL_COMPLETE; fixed observations and parameters unchanged')

if __name__=='__main__':main()
