"""Freeze bounded protocol before any new model outputs or optimizer updates."""
from common import *
def main():
    assert git(REPO,'rev-parse','HEAD')=='a69a17099e4ed5ff34ed8e1be49157fbda329615'
    config=dict(task=R.name,scene=SCENE,references=REFS,parent_commit='a69a17099e4ed5ff34ed8e1be49157fbda329615',seed=20261031,
        initialization=load(E26/'config/SHELL_CALIBRATION_FROZEN.json')[SCENE],domain=domain(),
        arms=dict(A=dict(anchor=0.),B=dict(anchor=.01)),source_component_weight=1/3,
        train_split='extra',monitor_split='small',train_rays_per_ref=64,train_HERO_per_ref=32,monitor_rays_per_ref=16,monitor_HERO_per_ref=6,
        Eikonal='first6 fixed P_INTERIOR extra midpoints per reference,18 total; one shared regularizer',
        losses=dict(rgb=1.,depth=.1,mask=.1,eikonal=.1,RGB_Huber=.05,Depth_Huber_mm=.5,Anchor_Huber_mm=.5),
        optimizer=dict(type='Adam',implicit_lr=1e-4,rendering_lr=1e-4,beta_lr=1e-5,betas=[.9,.999],weight_decay=0),
        MAX_STEPS=100,max_seconds_per_arm=1800,max_allocated_bytes=5*2**30,checkpoint_steps=[0,25,50,75,100],monitor_every=5,
        source_gradient_accumulation='sum3 per-reference backward(loss/3), then shared Eikonal once; one optimizer.step',
        AMP=False,TF32=False,augmentation=False,adaptive_sampler=False,
        parity=dict(loss_atol=.002,loss_rtol=.002,implicit_cosine_min=.995,implicit_norm_relative_max=.02,
            depth_max_abs_mm=.05,front_cross_max_abs_mm=.05,opacity_max_abs=.002,RGB_max_abs=.002,hit_set_equal=True),
        sampler_compare=dict(cells=[128,256],rule='128 only if every source/split passes; otherwise256, record NOT_FULLY_CONVERGED; no further density search',
            mask_relative_max=.02,depth_max_abs_mm=.05,opacity_max_abs=.01,RGB_max_abs=.01,implicit_cosine_min=.995,implicit_norm_relative_max=.10,hit_set_equal=True),
        stopping=dict(nonfinite=True,zero_hits=True,minimum_per_reference_coverage=.5,coverage_drop_pp=.10,consecutive_fixed_probes=3,
            CAD_penetration_mm=.1,CAD_fraction=.01,unknown_or_behind_Ring=True),
        baseline_E26=dict(extra=[27,29,31],small=[6,6,6]),
        geometry_probe=dict(grid_N=49,extent_ROI=1.,surface_grid_final_N=65,slice_axis='xz, y=ROI origin',render_stride=4,
            mesh_support='project fixed cameras; positive source Mask; in visible ROI/CAD prefix; nearest native HERO residual <=1mm supports, >1mm conflict; else unknown',
            HERO_support_tolerance_mm=1.,invisible_faces='omit from visible surface, never close or fill'),
        evaluation=dict(pixel_monitor_only=True,strict_view_holdout_N=0,GT_opened=False,
            beneficial='B final has no per-source/split coverage loss vs A or own init; >=5% reductions in >=2 of small RGB/Depth/Mask, third <=5% worse; no new CAD/zero-set failure',
            feasible='complete100 steps; no per-source monitor coverage decrease; >=5% reductions in >=2 of small RGB/Depth/Mask, third<=5% worse; changed surface and no topology/CAD inflation flags',
            geometry_flags='ROI boundary negative fraction>0.05; >1 substantial zero-surface components; >10% source Polyp spill increase; any Ring penetration stop; raw mesh unsealed'),
        authorized=['G01_005 official neural GPU updates','Adam','small state_dict checkpoints','serial A/B <=100 steps each'],
        forbidden=['G01_004 training','GT/Oracle','MapAnything','upstream edits','HERO/camera/CAD correction','longer training','hyperparameter search'])
    save('config/PREREGISTERED.json',config);save('config/TRAINING_CONFIG.json',{k:config[k] for k in ['scene','references','arms','optimizer','losses','MAX_STEPS','max_seconds_per_arm','max_allocated_bytes','source_gradient_accumulation']})
    probes=[];eik=[]
    for ref in REFS:
        for split in ['extra','small']:
            b=packet(ref,split);probes.append(dict(source=ref,split=split,pixel=b['source_pixel'],packet=asset(E26/f'local_results/packets/{ref}_{split}.npz'),observed_N=int((b['depth_weight']>0).sum())))
        a=packet(ref,'extra');assert np.all(a['sampling_class'][:6]==0)
        eik.extend(a['origin'][:6]+a['direction'][:6]*((a['start'][:6]+a['end'][:6])/2)[:,None])
        assert not np.intersect1d(a['source_pixel'],packet(ref,'small')['source_pixel']).size
    save('provenance/SOURCE_PIXELS.json',probes);save('config/EIKONAL_TRAIN_POINTS.json',eik)
    save('provenance/PROTECTED_START.json',protected_state());freeze('BEFORE_NEW_MODEL_OUTPUTS.json',dict(optimizer_step_N=0,GPU_authorized=True,no_old_audits_rerun=True))
    print('E27_PREREGISTERED',6,'fixed packets; no GPU or new model forward yet')
if __name__=='__main__':main()
