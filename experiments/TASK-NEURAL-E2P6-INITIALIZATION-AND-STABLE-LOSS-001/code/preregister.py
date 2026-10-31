"""One uniform initialization rule, fixed input probes and gates BEFORE predictions."""
from common import *

def make_dense(ref,index,old_pixels):
    c,p,r=source(ref);rng=np.random.default_rng(20261101+index);quota=[32,12,10,6,4];ix=[];importance=[]
    excluded=np.zeros(230400,bool);excluded[old_pixels]=True
    for region,n in enumerate(quota):
        pool=np.flatnonzero((r['sampling_class']==region)&~excluded);chosen=rng.choice(pool,min(n,len(pool)),replace=False)
        ix.extend(chosen);importance.extend([int((r['sampling_class']==region).sum())/len(chosen)]*len(chosen))
    ix=np.asarray(ix);uv=np.c_[ix%640,ix//640];ray=vis.camera_rays(uv,r['K'],r['c2w_mm']);factor=np.linalg.norm(ray[:,3:],axis=1)
    rel=np.load(e2_asset('local_results/'+ref+'_depth_reliability.npz'));w=rel['pixel_weight'][ix]
    rgb=np.asarray(Image.open(c['RGB']).convert('RGB'))
    return dict(source=ref,source_pixel=ix,origin=ray[:,:3],direction=ray[:,3:]/factor[:,None],cosine=1/factor,
        start=r['ROI_start_t_mm'][ix],end=r['ROI_end_t_mm'][ix],valid=r['ROI_valid'][ix],sampling_class=r['sampling_class'][ix],
        mask_target=r['mask_target'][ix],mask_weight=r['mask_weight'][ix]*importance,depth_weight=w*np.asarray(importance),
        target_Z=r['native_axial_Z_mm'][ix],RGB=rgb[uv[:,1],uv[:,0]]/255.,
        source_K=r['K'],source_c2w_mm=r['c2w_mm'],Ring_t_mm=r['ring_first_t_mm'][ix],
        source_native_HERO_SHA256=np.array(c['E1_actual_native']['sha256']))

def main():
    save('config/PREREGISTERED.json',dict(task=R.name,seed=20261031,source_seed_extra=20261101,
        calibration_rule='ONE_RULE: bias0 seeded official raw head; median128 Fibonacci shell raw outputs; same-seed reconstruct with that bias',
        shell_radius_fraction=.5,shell_point_N=128,calibration_scenes=selected(),beta_mm=.08,beta_min_network=.0001,
        sample_cells=128,old_small_quota=[6,3,3,3,1],extra_quota=[32,12,10,6,4],extra_excludes_old_small_pixels=True,
        source_selection='frozen source regions only; no model predictions/GT/targets',minimum_HERO_front_hit_fraction=.5,
        useful_geometry_gradient_norm_min=1e-10,inside_sign_required_fraction=.95,outside_sign_required_fraction=.95,
        shell_median_abs_tolerance_mm=1e-5,physical_beta_abs_tolerance_mm=1e-6,
        FP32_FP64_loss_atol=.002,FP32_FP64_loss_rtol=.002,gradient_norm_relative_tolerance=.02,gradient_cosine_min=.995,
        mathematical_reference='mpmath80digits on same actual raw samples; stable log finite-opacity BCE',reference_atol=1e-6,reference_rtol=1e-6,
        pathological_controls=['CALIBRATED_NORMAL','ALL_POSITIVE_FIELD','EMPTY_POSITIVE_RAYS','ALL_NEGATIVE_FIELD','RING_OCCLUDED_PREFIX'],
        pathological_bias_delta_ROI=2.,controls_are_not_initialization_search=True,
        weak_anchor=dict(condition='only if stable Mask lacks useful geometric gradient/no-front recovery',type='qualified native HERO SDF Huber',
            delta_mm=.5,weight=.01,source_weights='same component1/3; existing pixel conflict1/0.25; NEVER hit-gated',
            per_reference_direction_probe_N=4,minimum_toward_zero_direction_fraction=.9,candidate_only=True),
        loss_weights=dict(rgb=1.,depth=.1,mask=.1,eikonal=.1,anchor=.01),
        coverage_evaluation='any per-source fixed-observed coverage decrease is POTENTIAL_FAILURE regardless of lower total loss',
        model_update_N=0,optimizer_step_N=0,GPU='NOT_AUTHORIZED',MapAnything_forward_N=0,GT=False))
    packets=R/'local_results/packets';packets.mkdir(exist_ok=True);ids=[]
    oldcfg=load(E25/'config/PREREGISTERED.json')
    for scene,refs in selected().items():
        small=e25.packets_for(scene,refs,oldcfg)
        for index,b in enumerate(small):
            ref=b['source'];oldids=load(E25/f'provenance/{ref}_CPU_PIXEL_SELECTION.json')['pixel'];assert np.array_equal(b['source_pixel'],oldids)
            c,p,r=source(ref);b['Ring_t_mm']=r['ring_first_t_mm'][b['source_pixel']]
            dense=make_dense(ref,index,oldids)
            for split,bb in [('small',b),('extra',dense)]:
                out=packets/(ref+'_'+split+'.npz');np.savez_compressed(out,**bb)
                ids.append(dict(scene=scene,source=ref,split=split,ray_N=len(bb['source_pixel']),observed_HERO_N=int((bb['depth_weight']>0).sum()),
                    pixel=bb['source_pixel'],packet=asset(out),prediction_independent=True))
    save('provenance/SOURCE_PROBES_FROZEN.json',ids);save('provenance/PROTECTED_START.json',protected_state())
    save('provenance/AUTHORIZATION.json',dict(task=R.name,base_commit='1eb9cc7fd49b70cf8370582dded7decb1d1cd4be',
        user_grant='ONE uniform initialization calibration; stable Mask actual full-network CPU gradients; conditional weak HERO anchor; fixed coverage diagnostics',
        forbidden=['GPU','optimizer.step','training','MapAnything inference','GT/target selection','upstream modifications','unbounded calibration search'],
        historical_audits_rerun=False,worktree_incident='new sparse info directory repaired; no old worktree reset'))
    freeze('BEFORE_CALIBRATION_AND_LOSS_TESTS.json',dict(probe_N=len(ids),new_rule_N=1,official_neural_model_outputs_examined=False))
    print('E2P6_FROZEN_ONE_RULE',len(ids),'source packets; small16 + disjoint extra64 per reference; no prediction-selected pixels')

if __name__=='__main__':main()
