"""E3-C hosts byte-identical E3-B local fields; only evidence logic is new."""
from mesh_local_field import *
import gzip,time,traceback
B=REPO/'experiments/TASK-E3-B-LOCAL-HERO-FIELDS-001'
PARENT='a7c6233f33f9a2ec84b4ce19f668a187bd90b9c8'
@lru_cache(None)
def model(cid):return MeshLocalField(cid)
@lru_cache(None)
def pf(cid):return ProjectiveLocalField(cid)
def protocol():return load(R/'config/CONSENSUS_PROTOCOL_FROZEN.json')
def scene_ids():return [o['scene']for o in ORG if o['reference_screened_sources']]
def scene_sources(sid):return next(o['reference_screened_sources']for o in ORG if o['scene']==sid)
def ordered_sources(sid):
    refs=scene_sources(sid);return sorted(refs,key=lambda r:(['CORE','BRIDGE','RESERVED'].index(ROLES[r]),refs.index(r)))
def stages(sid):return dict(REP_OBSERVERS=[s for s in ordered_sources(sid)if ROLES[s]!='RESERVED'],ALL_OBSERVERS=ordered_sources(sid))
def array_hash(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def fixed_indices(mask,budget):
    ids=np.flatnonzero(mask);return ids[np.unique(np.linspace(0,len(ids)-1,min(len(ids),budget)).astype(int))]if len(ids)else np.array([],int)
def prepare():
    assert git(REPO,'rev-parse','HEAD')==PARENT
    assert len(IDS)==17 and len(REP)==12
    inherited=[]
    for name in ['hero_native_adapter.py','projective_local_field.py','mesh_local_field.py']:
        src=B/'code'/name;dst=R/'code'/name;assert sha(src)==sha(dst);inherited.append(dict(source=asset(src),hosted=asset(dst),change='NONE; __file__ relocates task output root only'))
    assert sha(B/'HERO_NATIVE_INPUT_MANIFEST.json')==sha(R/'HERO_NATIVE_INPUT_MANIFEST.json')
    assert sha(B/'config/PROTOCOL_FROZEN.json')==sha(R/'config/PROTOCOL_FROZEN.json')
    save('provenance/INHERITED_LOCAL_FIELDS.json',dict(parent_commit=PARENT,code=inherited,whitelist=asset(B/'HERO_NATIVE_INPUT_MANIFEST.json'),local_field_manifest=asset(B/'LOCAL_FIELD_MANIFEST.json'),
        source_DAG=asset(A/'provenance/E3_SOURCE_DAG.json'),roles=asset(A/'provenance/SOURCE_ROLES.json'),ROI=asset(A/'config/GLOBAL_ROI_FROZEN.json'),source_selection_rerun=False,source_audit_rerun=False,
        note='Original E3-B initialization/audit mains never called; immutable loader assertions remain runtime invariants'))
    save('config/CONSENSUS_PROTOCOL_FROZEN.json',dict(task=R.name,parent=PARENT,source_N=17,
        candidates=dict(base=2048,legal_visible=256,boundary=256,source_unique=256,stretch=256,minor_component=128,Ring_near=256,possible_stalk=128,
            point='original triangle centroid, one fixed point per selected face; strata union, sorted original IDs; no geometry interpolation',Ring_near_distance_mm=.5,
            max_per_source=3584,statistical_meaning='deterministic stratified candidate frequencies; not population error rates or independently certified physical truth'),
        depth_halfwidth_mm=.25,depth_footprints=3,uncertainty='sum of source axial interval transformed to observer axial frame + observer interval, NOT calibrated standard deviation',
        support_kernel='exp(-0.5*(native_delta/pair_halfwidth)^2)',support_count_response_min=float(np.exp(-.5)),
        occlusion_and_free_transition_fraction=.25,ordering_epsilon_mm=.002,native_Raw_alignment_mm=.25,mask_inner_distance_px=2,Ring_mask_distance_px=2,
        normal_coherence_min=.85,incidence_abs_min=.2,support_abs_normal_cos_min=.8,
        V0='numeric Support response only; no absence conclusion; field admissibility stored separately',
        V1='Support plus behind-observed-surface/CAD occlusion states; does not treat occlusion as negative evidence',
        V2='V1 plus interval-separated free-space proxy; minimum frozen-camera/Polyp-Mask/numeric-depth/CAD gates always apply',
        V3='V2 plus stricter Ring/Mask/local-quality/native-Raw consistency, origin visibility, upstream-camera proxy and source correlation; never deletes geometry',
        forbidden_counterfactual='ungated numeric free response may be shown for diagnosis only, never classified as admissible free evidence',
        correlation='w_j=1/(1+Jaccard(origin,j)+sum Jaccard(j,k) over other active observers); q_camera=1 if all parents noncandidate else .5; vote mass is not effective independent sample size',
        single_source_protection='origin anchor retained independently of other views; no-observation is not opposition; unique flag never a deletion gate',
        stages='REP observers first, then add RESERVED. Candidate cohort and own-source anchors fixed across stages; origin never counted as an external observer',
        classifications=['MULTI_SUPPORTED','SINGLE_SUPPORTED_UNVERIFIED','FREE_SPACE_CONFLICT','CAD_OCCLUDED','CORRESPONDENCE_UNRESOLVED','UNKNOWN'],physical_truth='UNRESOLVED',
        ray_windows=dict(regular_per_scene=2,separated_05_to_1mm_per_scene=2,selection='lexicographic source, original face, observer within preregistered eligibility, not best score',
            samples=193,mode_sources='original candidate + observer native depth + first ray intersections of each original raw mesh; all on same frozen observer ray',
            interval='local plane axial-error propagation, retain broad/ambiguous modes; no depth average or mode winner',margin_mm=.5),
        budget=dict(max_candidate_observer_queries=1000000,max_ray_queries=100000,CPU_threads=2,max_RAM_GiB=8,max_seconds_per_scene=600),
        GPU=0,new_HERO=0,new_fusion=0,global_fit=0,geometry_deletion=0,geometry_deformation=0,GT=False))
    if(R/'provenance/PROTECTED_START.json').exists():assert load(R/'provenance/PROTECTED_START.json')==protected_state()
    else:save('provenance/PROTECTED_START.json',protected_state())
    freeze('BEFORE_CANDIDATES_AND_EVIDENCE.json')
    print('E3C_PROTOCOL_FROZEN',flush=True)
if __name__=='__main__':prepare()
