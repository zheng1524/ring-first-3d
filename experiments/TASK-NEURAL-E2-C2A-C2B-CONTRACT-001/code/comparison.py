"""Future scientific variables and held-out identity. No target images opened."""
from context import *

def main():
    require_c2a();D=registry();targets=[]
    for t in D['targets']:
        if t['scene']not in selected():continue
        targets.append(dict(scene=t['scene'],target=t['target'],RGB_SHA256=t['RGB_SHA256'],Mask_SHA256=t['Mask_SHA256'],
            role=t['holdout_tier'],strict_holdout=False,E2_target_pixel_access='NONE_METADATA_ONLY',
            excluded_from_training=True,forbidden_for_parameter_selection=True,reason=t['strict_reason']))
    save('provenance/EVALUATION_IDENTITIES_FROZEN.json',dict(targets=targets,strict_holdout_N=0,
        source='E1 identity/ancestry results reused; no new E1 audit',
        GT='sealed; world transform uncertified; absolute shape error NOT_EVALUABLE'))
    variables=[
        dict(arm='SDF',name='S0_VALID',change='shared SDF + RGB/HERO-Z/Eikonal; no explicit Mask BCE',inputs='same triple and source qualification; existing segmentation still defines data/ROI, so not a segmentation-free claim',status='PROPOSED_NOT_RUN'),
        dict(arm='SDF',name='S1_MASK',change='S0 + finite Polyp Mask BCE; RA region quotas and population correction',inputs='same source set/budget; only explicit silhouette term changes',status='CPU_MASK_CONTRACT_ONLY'),
        dict(arm='SDF',name='S2_CAD',change='S1 + fixed CAD first-hit visibility stop',inputs='same source set; no Ring SDF learning',status='CPU_CAD_CONTRACT_ONLY'),
        dict(arm='SDF',name='S3_UNCERTAIN',change='S2 + source-component normalization and frozen conflict weights',inputs='same source set; source weights never chosen by target/GT',status='CPU_LOSS_CONTRACT_ONLY'),
        dict(arm='SDF',name='S4_ANCHOR_OPTIONAL',change='verified physical MASt3R anchor gradients only if separately wired',inputs='no fake correspondences or pose fitting',status='NOT_IMPLEMENTED_NOT_RUN'),
        dict(arm='SDF',name='BG0/BG1',change='unknown BG censored / qualified cached observed BG proxy enabled',inputs='same RGB; eligible-ray denominators differ and must be reported',status='PROPOSED_NOT_RUN'),
        dict(arm='Map',name='M0',change='RGB + frozen K/pose',inputs='same triple',status='CPU_INPUT_CONTRACT_ONLY'),
        dict(arm='Map',name='M1',change='M0 + native HERO full-depth',inputs='full native depth differs from Polyp-only SDF loss; matched-information profile needed',status='CPU_INPUT_CONTRACT_ONLY'),
        dict(arm='Map',name='M2',change='M0 + one frozen Cleaned depth layer',inputs='same real RGBs, one depth hypothesis per view',status='CPU_INPUT_CONTRACT_ONLY'),
        dict(arm='Map',name='M3',change='M1 + qualified visible CAD Ring pixel axial-Z',inputs='CAD error is now self-consistency, not independent Polyp accuracy',status='CPU_INPUT_CONTRACT_ONLY'),
        dict(arm='Map',name='M4',change='M2 switch F1/F2/F3, three bounded mutually exclusive profiles',inputs='historical ancestor information advantage disclosed; Raw only diagnostic',status='CPU_INPUT_CONTRACT_ONLY')]
    table('metrics/FUTURE_EXPERIMENT_VARIABLES.csv',variables)
    metrics=[
        dict(metric='visible Mask IoU / boundary F1',denominator='all eligible target Polyp pixels plus unknown/censored counts',meaning='observable silhouette, not inferred hidden contour'),
        dict(metric='A→B RGB error median/MAE/p95/max + coverage/spill',denominator='fixed full target pixels and paired common successful pixels',meaning='source RGB only; no B recoloring; low coverage cannot be hidden'),
        dict(metric='fixed Ring CAD distance median/p95/max; penetration',denominator='all valid Ring output pixels plus full input Ring denominator',meaning='metric rigid-anchor consistency, not Polyp GT'),
        dict(metric='predicted vs frozen input pose residual',denominator='each source/target camera; raw + predeclared gauge',meaning='Map output pose never overwrites Ring-First'),
        dict(metric='HERO cross-source axial-depth consistency',denominator='all co-visible source observations and correlated-parent groups',meaning='estimated-prior agreement, not independent depth accuracy'),
        dict(metric='observed support / conflict / prior / unknown',denominator='full candidate points/faces and independent-source identities',meaning='no unobserved backside area/volume claims'),
        dict(metric='independent group coverage / MedARE / MAE / p95 / max / paired comparison',denominator='G01 one physical group; 004/005 are two scenes, not two cases',meaning='absolute 3D/diameter error NaN until eligible independent GT exists')]
    table('metrics/FUTURE_EVALUATION_METRICS.csv',metrics)
    save('config/FUTURE_COMPARISON.json',dict(variables=variables,metrics=metrics,source_sets=selected(),
        information_tables=['common three-reference data, explicit per-pixel information use','best allowed information with extra historical prior ancestors'],
        matched_information_requirement='RA Map M1 full-view HERO includes BG/Ring; a separately frozen Polyp-visible M1 profile is needed for strict per-pixel comparison with the SDF depth loss. RA M3 consumes CAD so CAD agreement is not independent validation.',
        fixed=['source K/c2w','CAD dimensions','ROIs','source identities','heldout target identities','predeclared metric denominators'],
        scientific_budgets='NOT_SET_REQUIRES_FUTURE_PREREGISTRATION',GPU='NOT_GRANTED',official_forward_N=0))
    save('metrics/GPU_READINESS.json',dict(C2a_engineering='CPU_PASS_WITH_LIMITATIONS',C2b_engineering='CPU_PASS_WITH_LIMITATIONS',
        formal_GPU_scientific_experiment_ready=False,GPU_authorization='NOT_GRANTED',
        remaining_gates=[
            'authorized minimal official MonoSDF raw-implicit / finite-cell / RGB / Eikonal / loss-gradient integration gate, not yet executed',
            'freeze official raw-SDF geometric initialization with a front zero crossing inside ROI, and beta in physical units; E1 gauges imply old beta_mm about2.84/3.41, distinct from0.08mm analytic controls',
            'review the2763 source HERO visibility conflicts: their positive Mask is retained while only contradictory depth is rejected; freeze all per-view denominators',
            'no opaque real BG triangle mesh is certified; point observations only bound same-source free-space; approve uncertainty ablation or certify an existing real mesh',
            'accept shared-HERO dependence (one component per video), strict holdout0 and conditional camera limits, or obtain independently qualified new evaluation data in another task',
            'freeze matched-information comparison including RA M1 full-depth vs Polyp-only distinction, scientific budgets/seeds/stopping rules and non-circular CAD/pose gates',
            'explicit researcher/RA acceptance and a separate GPU grant'],
        recommended_next='submit CPU evidence for review; only after new authorization perform bounded official-runtime wiring validation, then decide scientific runs'))
    print('COMPARISON_FROZEN',len(targets),'fixed diagnostic/reconstruction-only target identities; strict0',flush=True)

if __name__=='__main__':main()
