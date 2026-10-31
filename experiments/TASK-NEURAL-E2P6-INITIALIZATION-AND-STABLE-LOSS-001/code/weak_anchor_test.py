"""Conditional candidate: real full-network weak surface gradients, NOT training."""
from common import *
from stable_losses import weak_anchor,packet
from stable_test import field_case_bias

def main():
    gate=load(R/'metrics/STABLE_MASK_GATE.json');assert gate['weak_HERO_anchor_necessary']
    freeze('P3_WEAK_ANCHOR_BEFORE_RUN.json',dict(trigger='stable Mask all-negative geometric gradients uninformative',weight=cfg()['weak_anchor']['weight']))
    rows=[];point_rows=[];states=[]
    p2_states=load(R/'provenance/STABLE_TEST_MODEL_STATES.json')
    for scene,refs in selected().items():
        domain=domains()[scene]
        for precision,dtype in [('FP64',torch.float64),('FP32',torch.float32)]:
            for field in ['POSITIVE','NEGATIVE']:
                model,ports=build_model(domain,field_case_bias(scene,field),dtype);before=e25.parameter_hash(model)
                expected=next(x for x in p2_states if x['scene']==scene and x['precision']==precision and x['field_control']==field)
                assert before==expected['parameter_SHA_before']
                anchors=[];gradients=[]
                for ref in refs:
                    b=packet(ref,'small');q=weak_anchor(model,domain,b,dtype);meta,g=full_gradient(q['loss'],model)
                    anchors.append((ref,b,q,meta));gradients.append(g)
                joint=cfg()['weak_anchor']['weight']*torch.stack(gradients).mean(0)
                for ref,b,q,meta in anchors:
                    recovery=[]
                    for k in range(min(cfg()['weak_anchor']['per_reference_direction_probe_N'],len(q['ids']))):
                        f=q['f'][k];jac,jvec=full_gradient(f,model)
                        directional=float(torch.dot(jvec,-joint));toward=float(f.detach())*directional<0
                        recovery.append(toward)
                        point_rows.append(dict(scene=scene,source=ref,precision=precision,field_control=field,
                            source_pixel=int(b['source_pixel'][q['ids'][k]]),SDF_mm=float(f.detach()),
                            directional_df_along_negative_full_parameter_anchor_gradient=directional,
                            first_order_toward_zero=toward,scalar_output_offset_not_used=True,
                            actual_model_parameter_step_N=0,front_crossing_recovery_observed=False))
                    rel=np.load(e2_asset('local_results/'+ref+'_depth_reliability.npz'));pixel=b['source_pixel'][q['ids']];weight=rel['pixel_weight'][pixel]
                    rows.append(dict(scene=scene,source=ref,precision=precision,field_control=field,
                        observed_N=len(q['ids']),anchor_loss_mm=float(q['loss'].detach()),
                        full_parameter_gradient_norm=meta['full_norm'],geometry_gradient_norm=meta['implicit_norm'],trunk_gradient_norm=meta['trunk_norm'],head_gradient_norm=meta['head_norm'],
                        beta_gradient_norm=meta['beta_norm'],all_parameter_gradients_finite=meta['finite'],full_parameter_N=meta['parameter_N'],
                        source_component_weight=1/3,source_conflict_weight025_N=int((weight==.25).sum()),source_weight1_N=int((weight==1).sum()),
                        fraction_probe_points_toward_zero=float(np.mean(recovery)),
                        visible_HERO_only=True,predicted_hit_not_used_for_anchor=True,raw_depth_modified=False,
                        candidate_only=True,first_order_point_response_not_observed_surface_recovery=True))
                assert before==e25.parameter_hash(model)
                states.append(dict(scene=scene,precision=precision,field_control=field,parameter_SHA256=before,unchanged=True,CPU_ports=ports))
                print('WEAK_SURFACE_ANCHOR',scene,precision,field,'full neural gradients; no parameter step',flush=True)
                del anchors,gradients,model,joint;gc.collect()
                table('metrics/WEAK_HERO_ANCHOR_GRADIENTS.csv',rows);table('metrics/WEAK_HERO_POINT_DIRECTIONS.csv',point_rows)
    passed=all(r['geometry_gradient_norm']>cfg()['useful_geometry_gradient_norm_min'] and r['trunk_gradient_norm']>cfg()['useful_geometry_gradient_norm_min'] and r['all_parameter_gradients_finite'] and
        r['fraction_probe_points_toward_zero']>=cfg()['weak_anchor']['minimum_toward_zero_direction_fraction'] for r in rows)
    save('metrics/WEAK_ANCHOR_GATE.json',dict(candidate_first_order_gradient_gate=passed,first_order_probe_N=len(point_rows),
        observed_zero_crossing_recovery_verified=False,reason='optimizer/parameter steps prohibited; only actual-neural differential direction verified',
        stable_mask_alone_not_sufficient=True,additional_free_space_constraint_added=False,
        no_ROI_entry_outside_assumption=True,mainline_adoption=False,optimizer_step_N=0,GPU='NOT_AUTHORIZED'))
    save('provenance/WEAK_ANCHOR_MODEL_STATES.json',states)
    print('WEAK_ANCHOR_CANDIDATE_COMPLETE',passed,'first-order point recovery; surface recovery not claimed')

if __name__=='__main__':main()
