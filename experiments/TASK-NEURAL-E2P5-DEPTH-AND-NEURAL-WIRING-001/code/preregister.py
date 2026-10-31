"""Freeze the two work packages before diagnostic results exist."""
from common import *

def main():
    cfg=dict(seed=20261031,scope=selected(),pixel_correspondence='nearest native B pixel; no depth interpolation',
        regions=['BODY_PROXY','INNER_BOUNDARY_2PX','RING_NEAR_8PX','GRAZING_NORMAL_PROXY'],region_priority='RingNear > Boundary > Grazing > Body',
        native_depth='unmodified axial HERO Z',source_visibility='positive Mask + finite native Z inside original finite ROI/CAD limits; boundary retained for diagnostic',
        known_occlusion='first positive CAD hit, projected-A self z-buffer',self_z_tolerance_mm=.5,
        comparison_tiers=['LOOSE_PROJECTIVE_CANDIDATE','CONDITIONAL_CYCLE_NORMAL'],cycle_max_px=2.,normal_dot_min=.2,
        uncertified_depth_order='residual magnitude/sign NEVER used to drop a candidate; mark ambiguity separately',
        depth_conflict_mm=.5,conflict_pixel_footprints=3.,tile_size_px=40,min_component_pixels=8,
        bias_min_comparisons=100,bias_signed_threshold_mm=.1,bias_offset_bounds_mm=[-1.,1.],
        bias_fit='NOT_PLANNED; design identifiability + Ring-based linearized diagnostic only; no corrected training inputs',
        ring_mask_erode_px=1,CAD_mask_erode_px=1,ring_min_incidence=.2,ring_selection='NO residual-based agreement filter; native Ring depth only',
        CPU_neural_candidates=['A_LEGACY_INIT_CONTROL','B_SOURCE_ROI_PHYSICAL'],max_candidate_N=2,
        A=dict(geometric_bias_network=.6,beta_parameter_network=.1,beta_min_network=.0001),
        B=dict(radius_rule='0.5*frozen source ROI radius',beta_mm=.08,beta_min_network=.0001),
        model='official MonoSDFNetwork with official plain MLP branch; width256 x8, feature256, multires6, official rendering conf',
        sampler='FIXED_SAMPLER_DIAGNOSTIC_ONLY',sample_cells=128,
        per_reference_CPU_quota=[6,3,3,3,1],source_pixel_selection='fixed RNG subselect within existing frozen E2 batch; no prediction-driven selection',
        test_loss_weights=dict(rgb=1.,mask=.1,depth=.1,eikonal=.1),
        neural_parameter_update_N=0,MapAnything_forward_N=0,GPU='NOT_AUTHORIZED')
    save('config/PREREGISTERED.json',cfg)
    request=Path('/home/liu/.codex/attachments/d070bae0-18b3-4cdb-89f6-e7b973aa95aa/Pasted text.txt')
    (R/'inputs/USER_TASK.md').write_bytes(request.read_bytes())
    save('provenance/AUTHORIZATION.json',dict(task=R.name,request=asset(request),copied_request=asset(R/'inputs/USER_TASK.md'),
        base_commit='c530fcb375d3412d49a6f2ce0346af6aa4def74a',previous_audits_rerun=False,
        CPU_official_network_forward_backward='EXPLICITLY_GRANTED_IN_USER_REQUEST',GPU='NOT_AUTHORIZED',optimizer_step_N=0,
        forbidden=['GT/target parameter selection','HERO/camera/CAD/P0/Dxy modification','MapAnything inference','training','old artifact deletion'],
        worktree_incident='inherited sparse checkout info missing; repaired only the new worktree administrative directory'))
    save('provenance/PROTECTED_START.json',protected_state());freeze('P1_BEFORE_DIAGNOSTICS.json')
    print('E2P5_PREREGISTERED; P1 first, then official CPU neural wiring; GPU denied')

if __name__=='__main__':main()
