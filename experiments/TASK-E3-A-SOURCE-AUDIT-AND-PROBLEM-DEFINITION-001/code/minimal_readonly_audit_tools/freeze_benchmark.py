"""Freeze evidence identities and future evaluation rules; no candidate method run."""
from common import *

def read_receipts():
    # This receipt was supplied after actual reading by the primary agent.
    # A reproduction may verify it; file availability never establishes reading.
    receipts=load(R/'provenance/RA_READING_RECEIPTS.json');access=[]
    for name,lines in [('RA_PHASE_E3_LOCAL_TO_GLOBAL_SDF_FUSION_REVIEW_v1.1.md',725),('RA_PHASE_E3_ALGORITHM_AND_EXPERIMENT_BLUEPRINT_v1.2.md',355)]:
        p=Path('/home/liu/下载')/name;a=asset(p);assert receipts[name]['sha256']==a['sha256']and receipts[name]['lines_read']==[1,lines]and receipts[name]['read_complete']
        access.append(dict(name=name,**a,read_complete=True,access_status='READ_COMPLETE',authority='design evidence; current explicit E3-A task defines execution scope'))
    save('provenance/RA_DOCUMENT_ACCESS.json',access)

def reuse():
    entries=[
        (OLD/'surface_fusion_v1/scripts/run_mvs_adapter3.py',['load_official'],'native HERO adapter','RGB + fixed K/c2w -> archived native depth; no new call','mm native axial Z','STATIC_ONLY_INFERENCE_NOT_AUTHORIZED','native packs exist for 40 sources; weights not opened','No inference adapter required this round'),
        (OLD/'ring_first_v1/scripts/common.py',['unproject','depth_mesh'],'original geometric pipeline','Z,pose,UV,K -> XYZ; depth/mask/color -> original image-adjacent faces','mm axial Z / world mm','unproject executed all36; depth_mesh static only','36 raw mesh / original UV+faces exist; cfg file present','Keep archived face IDs; do not retriangulate; archived .75mm jump cfg required'),
        (E0/'code/evidence.py',['points','combine','f3'],'exact source-index geometry loader','frozen source registry -> original XYZ/RGB/UV/faces; historical face subsets','mm','EXECUTED_EXACT_AST','all36 raw/Cleaned; first14 F2; five F3 joint NPZ','source-only namespace; skip legacy neural/MapAnything mains'),
        (SPARSE/'code/run.py',['source_components','face_components','edge_counts'],'original face topology','original faces -> shared-edge components/boundary counts','indices; areas separately mm2','EXECUTED_EXACT_AST','all36 indexed original meshes','bind returned namespace explicitly; no topology mutation'),
        (GROW/'code/geometry.py',['mesh_scene','raymesh','projection','common_metric','area','topology','direction'],'historical reprojection and geometry','original XYZ/F + frozen target K/c2w -> ray hits / fixed-pixel statistics','camera axial mm; area mm2','STATIC_AUDIT_AND_MATCHED_CURRENT_WRAPPERS','five scene meshes/cameras available','CID wrapper uses same Open3D BVH + existing camera_rays; full old module main prohibited'),
        (GROW/'code/cad_audit.py',['main'],'historical CAD audit','fixed Ring + source geometry -> archived CAD diagnostics','mm','STATIC_ONLY_MAIN_NOT_CALLED','Ring CAD files and old reports available','reuse SameCameraScene for queries; never call historical main'),
        (PART/'code/matching.py',['backmap','main'],'MASt3R historical matches','RGB pair + affine maps -> existing match candidate NPZ','pixels; NOT metric geometry','CACHE_ONLY_MAIN_NOT_CALLED','matching_comparison.json, registration_edges.json, CROSSVIDEO_GATE.json exist','cached matches are not independent physical correspondence labels'),
        (PART/'code/registration.py',['anchors','qualify_independent','pose_graph'],'historical pose qualification','cached matches + frozen geometry -> archived candidate transform / diagnostic checks','mm','STATIC_ONLY_NO_PNP_OR_OPTIMIZATION','cross-video gate fusion_certified=false; photos c2w null','do not adopt pose_graph operational unified flag as certified registration'),
        (REPO/'visualization/real_p0_renderer.py',['basis','configure','project_camera','camera_rays'],'shared frozen renderer/camera','real XYZ,K,c2w -> projected UV and unnormalized world rays','axial ray t = camera Z mm','EXECUTED','bundled original renderer and provenance available','audit figures add original triangle PolyCollection using exact basis; P0 code unchanged'),
        (REPO/'visualization/same_camera_scene.py',['SameCameraScene'],'fixed opaque CAD raycast','CAD,K,c2w,image_size -> original CAD first ray intersections','axial Z mm','EXECUTED','both Ring CAD assets exist','existing .002mm raster ordering epsilon, separate future uncertainty margin'),
        (E1/'code/common.py',['extract','guard','protected_state'],'source guard and integrity','exact AST helpers -> scoped read-only inputs / source SHAs / worktree status','N/A','EXECUTED_EXACT_AST','E1 registry/reuse source and all history worktrees exist','deny Torch/checkpoint imports and scope writes to E3-A'),
        (E27/'code/common.py',[],'E2.7 failure lineage','small existing report/metrics -> failed one-step pilot evidence','mm; voxel volume is not physical volume','STATIC_ONLY_NO_IMPORT','E2.7 technical report exists','never import neural/GPU-authorized runtime; no E2.7 re-execution')]
    rows=[]
    for path,names,cap,io,units,run,available,adapt in entries:
        textcode=path.read_text();tree=ast.parse(textcode);repo=REPO if path.is_relative_to(REPO)else next((p for p in path.parents if(p/'.git').exists()),None)
        defs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};assert set(names)<=set(defs),(path,names)
        rows.append(dict(capability=cap,path=str(path),sha256=sha(path),branch=git(repo,'branch','--show-current')if repo else'LOCAL_ARCHIVE',commit=git(repo,'rev-parse','HEAD')if repo else None,
            functions=[dict(name=n,line=defs[n].lineno,signature=ast.unparse(defs[n].args)if isinstance(defs[n],ast.FunctionDef)else'class',AST_SHA256=hashlib.sha256(ast.dump(defs[n],include_attributes=False).encode()).hexdigest())for n in names],
            input_output=io,units=units,local_unuploaded_dependency=True,validation=run,required_inputs=available,minimum_adaptation=adapt))
    save('provenance/E3_CODE_REUSE_AUDIT.json',rows)

def benchmark():
    full=readrows(R/'metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv');main=[r for r in full if r.get('source_id')in CC and r['record_kind']=='HERO_SOURCE'];roi=load(R/'config/GLOBAL_ROI_FROZEN.json');organization=load(R/'provenance/SOURCE_ORGANIZATION.json');raw=readrows(R/'metrics/E3_RAW_SURFACE_DIAGNOSTICS.csv');evals=readrows(E1/'provenance/SOURCE_LEAKAGE_LEDGER.csv');members=readrows(E1/'provenance/ALL_FRAME_HERO_MEMBERSHIP.csv')
    observations=[];protection=[]
    for row in main:
        cid=row['source_id'];s=source(cid);q=np.load(R/f'local_results/face_facts/{cid}.npz');own=np.load(R/f'local_results/own/{cid}.npz');mask=s['labels']==1;depth=mask&np.isfinite(s['depth'])&(s['depth']>0);base=mask&own['visible']
        # Frozen cohort is a source quality proxy, not a certified-anatomy label.
        F=s['F'];face=own['raw_face'];ids=np.unique(face[base]);ids=ids[ids<len(F)];cohort=np.zeros(len(F),bool);cohort[ids]=True;cohort&=q['clean_kept']&~q['stretch_proxy']
        def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
        observations.append(dict(source_id=cid,full_Mask_N=int(mask.sum()),full_Mask_packbits_SHA256=digest(np.packbits(mask)),numeric_Polyp_HERO_N=int(depth.sum()),
            numeric_HERO_valid_packbits_SHA256=digest(np.packbits(depth)),baseline_raw_visible_first_triangle_N=int(base.sum()),baseline_first_hit_packbits_SHA256=digest(np.packbits(base)),
            raster_policy='all 640x360 integer pixel centers; no erosion/resampling; triangle and CAD order epsilon=.002mm',
            local_evidence_cache=asset(R/f'local_results/own/{cid}.npz'),formal_qualification=row['qualification']))
        protection.append(dict(source_id=cid,definition='original faces hit by positive source Mask AND CAD-visible AND existing Cleaned keep AND not stretch proxy; never claim anatomical GT',
            original_face_N=int(cohort.sum()),face_id_uint32_SHA256=digest(np.flatnonzero(cohort).astype(np.uint32)),
            stalk_or_Ring_protection_proxy_N=int(q['protected_proxy'].sum()),labels_asset=asset(s['c']['cleaned_flags']['path']),human_verified_anatomy='NOT_PROVIDED',
            future_non_degradation='preserve every cohort source ray and original face lineage; any unexplained loss blocks improvement; no silent cohort updates'))
    table('metrics/E3_FIXED_OBSERVATION_DENOMINATORS.csv',observations);save('provenance/E3_PROTECTED_GEOMETRY_COHORTS.json',protection)
    targetrows=[]
    for e in evals:
        v=VV[e['target']];mask=cv2.imread(v['Mask'],0)==1;assert int(mask.sum())==int(e['target_Polyp_pixels'])
        targetrows.append(dict(**e,RGB_asset=asset(v['RGB'],expected=e['RGB_SHA256']),Mask_asset=asset(v['Mask'],expected=e['Mask_SHA256']),
            K=v['K'],c2w=v.get('c2w'),pose_status=v.get('pose_status'),camera_candidate_only=v.get('camera_candidate_only'),
            frozen_full_Polyp_denominator=int(mask.sum()),full_pipeline_status='FULL_PIPELINE_INDEPENDENCE_NOT_AVAILABLE',
            exposure=dict(HERO=e['known_HERO_input_of'],camera_recovery='HISTORICAL_EXPOSURE',matching='HISTORICAL_EXPOSURE_NOT_BLIND',cleaning='NOT_INDEPENDENTLY_EXCLUDED',selection='HISTORICAL_PROTOCOL_EXPOSURE',training='no E3 training; inherited audit identity only')))
    save('provenance/E3_EVALUATION_FRAMES_FROZEN.json',targetrows);table('metrics/E3_ALL_VIEW_MEMBERSHIP.csv',members)
    panel=[]
    for sid in scenes():
        refs=[c['id']for c in D['references']if c['scene_id']==sid];hist9=[c['id']for c in D['references'][:9]if c['scene_id']==sid];hist14=[c['id']for c in D['references'][:14]if c['scene_id']==sid];o=next(x for x in organization if x['scene']==sid)
        for method,inp in [('Raw',refs),('Cleaned',refs),('SinglePrimary',[refs[0]]),('F1_incremental_original',hist9),('F1_viewpartition_original',hist14),('F2_original',hist14),('F3_BoundaryGrowth_original',refs)]:
            panel.append(dict(scene=sid,method=method,historical_declared_available_input_ids=inp,panel='ORIGINAL_HISTORY_SOURCE_SETS_DIFFER',new_run=False,
                common_source_replay='NOT_RUN; filtering historical F3 is not replay because selection used its full historical inputs'))
    table('metrics/E3_BASELINE_INPUT_SCOPES.csv',panel)
    groups=[]
    for o in organization:
        sid=o['scene'];refs=[r for r in main if r['source_id']in o['all_available_sources']];groups.append(dict(physical_group=sid.split('_')[0],video=sid.split('_')[1],scene=sid,
            all_source_ids=o['all_available_sources'],qualified_source_ids=o['reference_screened_sources'],qualification_meaning='CONDITIONAL reference-screen only, parent chain states retained; not absolute metric certification',
            source_families=sorted({r['source_family']for r in refs}),camera_contract='frozen archived K,c2w; axial Z mm; source->video Ring world identity; no cross-video transform',world_frame=sid+'_LOCAL_RING_MM',
            sources=refs,representative_proposal=o['representative_sources'],Ring_CAD=asset(CC[o['all_available_sources'][0]]['Ring_CAD']['path']),ROI_definition=roi[sid],
            raw_Cleaned_labels=[asset(CC[r]['cleaned_flags']['path'])for r in o['all_available_sources']],evaluation_frames=[r['target']for r in targetrows if r['scene']==sid],
            protected_geometry='E3_PROTECTED_GEOMETRY_COHORTS.json, deterministic original-ID predicate + digest',source_region_labels='E3_CASEBOOK_POINTS.csv; coordinate/protection proxies, no manual anatomy truth',
            original_triangle_identity_intact=True,uncertainty_status='UNCALIBRATED camera/depth/normal/reliability proxies; no confidence probability',
            experiment_status='UNQUALIFIED_STRESS_ONLY'if not o['reference_screened_sources']else'CONDITIONAL_INPUT_READY_FOR_PM_LOCAL_REPRESENTATION_REVIEW',
            needed_input_repairs='G07 camera chain qualification'if sid.startswith('G07')else'G01_004 upstream candidate cameras + physical correspondence evidence'if sid=='G01_004'else'G08 LIMITED pose/chain qualification'if sid.startswith('G08')else'parent camera/physical correspondence qualification',
            characteristic='cross-source layer separation / preserved faces; image/raster misses; no certified same-surface error truth'))
    save('provenance/E3_BENCHMARK_MANIFEST.json',dict(task=R.name,main_physical_group_denominator=4,main_video_N=5,supplemental_catalog_group_N=4,metric_photo_N=0,
        strict_pipeline_independent_evaluation_frame_N=0,source_scope='36 main HERO +4 supplemental; all retained in inventory; 17 main reference-screened conditional',
        groups=groups,observations=observations,evaluation_frames=targetrows,all_view_membership_source=asset(E1/'provenance/ALL_FRAME_HERO_MEMBERSHIP.csv'),
        source_DAG='E3_SOURCE_DAG.json',source_family_rule='shared actual HERO input RGB SHA connected components; dependence grouping, not proof of perfect correlation',
        equal_input_future_protocol=dict(status='PREREGISTERED_NOT_RUN',source_sets='separate all-screened vs representative panels; same source IDs/native arrays/Cleaned labels within each comparison',
            baseline_required=['Raw','Cleaned','SinglePrimary','F1','F2','F3','BoundaryGrowth'],replay_required=True,
            no_new_HERO=True,no_pose_fit=True,GT_sealed=True,algorithm_choices='PM pending; none selected'),
        budgets=dict(status='PROPOSED_FROZEN_FOR_PM_REVIEW_NOT_EXECUTED',CPU_threads=2,max_wall_seconds_per_method_scene=600,max_RAM_GiB=8,max_evidence_queries_per_scene=1000000,
            max_optimizer_steps=0,neural_GPU_budget=0,note='first no-training representation diagnostic budget; any E3-D optimization budget needs a new pre-output PM freeze'),
        historical_panels='E3_BASELINE_INPUT_SCOPES.csv',measurement_results=dict(target_groups=4,independent_success=0,failed_or_not_measured=4,values='NaN',history_fallback=0,
            median_absolute_relative_error='NaN',MAE='NaN',p95='NaN',maximum='NaN',common_success_paired_N=0)))
    freeze('E3_BENCHMARK_FREEZE.json',dict(scope='evaluation protocol frozen after asset diagnostics, before any future candidate output',new_algorithms_run=False))

def main():read_receipts();reuse();benchmark();print('E3_BENCHMARK_FROZEN',flush=True)
if __name__=='__main__':main()
