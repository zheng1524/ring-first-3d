"""Validate audit deliverables without repeating scientific/model work."""
from common import *
from collections import Counter,deque
import re

def main():
    checks=[]
    def check(name,ok,detail):checks.append(dict(check=name,status='PASS'if ok else'FAIL',detail=clean(detail)))
    # Extend original inventory hashes with metadata/code actually used by this audit.
    existing=load(R/'provenance/INPUT_HASHES.json');indexed={r['path']:r for r in existing['files']}
    extras=[E1/'provenance/INPUT_ELIGIBILITY.json',E1/'config/CPU_CONTRACT.json',E1/'provenance/SOURCE_LEAKAGE_LEDGER.csv',E1/'provenance/ALL_FRAME_HERO_MEMBERSHIP.csv',E1/'provenance/PHOTO_QUALIFICATION.json',
        PART/'metrics/matching_comparison.json',PART/'metrics/registration_edges.json',PART/'metrics/CROSSVIDEO_GATE.json',PART/'metrics/pose_graph_status.json',E27/'TECHNICAL_REPORT.md',OLD/'ring_first_v1/config.json',
        REPO/'visualization/real_p0_renderer_provenance.json',REPO/'visualization/_phasec_c0_view_frozen.py']
    extras +=[Path(r['path'])for r in load(R/'provenance/E3_CODE_REUSE_AUDIT.json')]
    extras +=[GROW/f'local_results/scenes/{s}_Final.json'for s in scenes()]+[GROW/f'local_results/glb/{s}_Joint_sources.npz'for s in scenes()]
    extras +=[Path(r['path'])for r in load(R/'provenance/RA_DOCUMENT_ACCESS.json')]
    for p in extras:
        if str(p)not in indexed:indexed[str(p)]=asset(p,'actually used source metadata/code/historical geometry; readonly')
    mismatches=[]
    for p,r in indexed.items():
        if not Path(p).is_file()or sha(p)!=r.get('sha256'):mismatches.append(p)
    check('all_referenced_original_input_hashes_unchanged',not mismatches,dict(files=len(indexed),mismatches=mismatches))
    existing['files']=list(indexed.values());existing['E3A_final_hash_verification']='all actually used indexed inputs; legacy originals readonly';save('provenance/INPUT_HASHES.json',existing)
    before=load(R/'provenance/PROTECTED_START.json');after=protected_state();check('historical_worktrees_HEAD_status_and_existing_modifications_unchanged',before==after,dict(worktrees=len(before)));save('provenance/PROTECTED_END.json',after)
    manifest=readrows(R/'metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv');main=[r for r in manifest if r['record_kind']=='HERO_SOURCE'and r['source_id']in CC];allhero=[r for r in manifest if r['record_kind']=='HERO_SOURCE']
    check('all36_main_and4_supplemental_sources_in_full94_manifest',len(main)==36 and len(allhero)==40 and len(manifest)==94,dict(main=len(main),native=len(allhero),records=len(manifest)))
    check('original_face_identity_intact_all36',all(r['original_face_identity_intact']=='True'for r in main)and sum(int(r['original_faces'])for r in main)==1070754,dict(faces=sum(int(r['original_faces'])for r in main)))
    check('reference_vs_upstream_camera_qualification_separated',sum(r['camera_reference_screened']=='True'for r in main)==17 and sum(r['camera_reference_screened']=='True'and r['camera_parent_candidate_N']=='0'for r in main)==8,'17 screened / 8 all-parent noncandidate, not absolute certification')
    tolerance=load(E1/'config/CPU_CONTRACT.json');mxp=max(float(r['static_UV_roundtrip_max_px'])for r in main);mxu=max(float(r['static_unproject_max_mm'])for r in main)
    check('existing_E1_projection_unprojection_tolerances',mxp<=tolerance['projection_px']and mxu<=tolerance['unprojection_mm'],dict(max_pixel_error=mxp,max_mm_error=mxu,frozen_existing_tolerances=tolerance))
    dag=load(R/'provenance/E3_SOURCE_DAG.json');nodes={n['id']:n for n in dag['nodes']};indegree=Counter({n:0 for n in nodes});children={n:[]for n in nodes};bad=[]
    for e in dag['edges']:
        if e['parent']not in nodes or e['child']not in nodes:bad.append(e);continue
        indegree[e['child']]+=1;children[e['parent']].append(e['child'])
    queue=deque(n for n in nodes if indegree[n]==0);visited=0
    while queue:
        n=queue.popleft();visited+=1
        for c in children[n]:
            indegree[c]-=1
            if indegree[c]==0:queue.append(c)
    check('source_DAG_all_edges_resolved_and_acyclic',not bad and visited==len(nodes),dict(nodes=len(nodes),edges=len(dag['edges']),missing_edges=bad,visited=visited))
    parent_errors=[]
    for r in allhero:
        cid=r['source_id'];sha_set=set(json.loads(r['HERO_input_RGB_SHA256s']));dagedges={nodes[e['parent']].get('sha256')for e in dag['edges']if e['child']=='hero:'+cid and nodes[e['parent']]['kind']=='REAL_RGB'}
        if sha_set!=dagedges:parent_errors.append(dict(source=cid,manifest_parent_N=len(sha_set),DAG_parent_N=len(dagedges)))
    check('all40_HERO_actual_RGB_parent_SHA_sets_match_DAG',not parent_errors,parent_errors)
    pp=readrows(R/'metrics/E3_VIEW_COVERAGE.csv');check('252_directed_pairs_same_video_no_certification_inflation',len(pp)==252 and all(CC[p['A']]['scene_id']==CC[p['B']]['scene_id']and int(p['verified_same_physical_surface_N'])==0 for p in pp),len(pp))
    org=load(R/'provenance/SOURCE_ORGANIZATION.json');check('representative_selection_never_promotes_unqualified_reference',all(eligible(CC[s])for o in org for s in o['representative_sources']),{o['scene']:o['representative_sources']for o in org})
    roi=load(R/'config/GLOBAL_ROI_FROZEN.json');outside=[]
    for c in D['references']:
        if not eligible(c):continue
        b=roi[c['scene_id']];P=source(c['id'])['P']
        if not np.all((P>=np.array(b['minimum_mm']))&(P<=np.array(b['maximum_mm']))):outside.append(c['id'])
    check('frozen_ROI_contains_every_reference_screened_original_vertex',not outside,outside)
    qs=readrows(R/'metrics/E3_CONTRACT_QUERIES.csv');check('108_limited_original_triangle_queries',len(qs)==108 and all(q['numerical_check_pass']=='True'and q['signed_Euclidean_distance_mm']==''for q in qs),dict(query_N=len(qs),global_sign_not_assigned=True))
    case=readrows(R/'metrics/E3_CASEBOOK_POINTS.csv');check('288_real_source_region_records_no_manual_truth_fabricated',len(case)==288 and all(q['manual_anatomy_confirmed']=='False'for q in case),len(case))
    check('108_existing_historical_output_coverage_records',len(readrows(R/'metrics/E3_HISTORICAL_SOURCE_RAY_COVERAGE.csv'))==108,'no new fusion; per-source rays, original source sets differ')
    ret=readrows(R/'metrics/E3_HISTORICAL_FACE_RETENTION.csv');omitted=[r for r in ret if r['stage']=='F2'and r.get('original_faces_retained_N')==''];check('growth22_not_in_historical_F2_not_zero_retention',len(omitted)==22,len(omitted))
    bm=load(R/'provenance/E3_BENCHMARK_MANIFEST.json');frames=bm['evaluation_frames'];check('fixed_denominators_36_and9_targets_65_memberships',len(bm['observations'])==36 and len(frames)==9 and len(readrows(R/'metrics/E3_ALL_VIEW_MEMBERSHIP.csv'))==65,dict(sources=len(bm['observations']),target_N=len(frames),target_Polyp_pixel_denominator=sum(f['frozen_full_Polyp_denominator']for f in frames)))
    check('strict_independent_evaluation_not_claimed',bm['strict_pipeline_independent_evaluation_frame_N']==0 and all(f['full_pipeline_status']=='FULL_PIPELINE_INDEPENDENCE_NOT_AVAILABLE'for f in frames),0)
    ra=load(R/'provenance/RA_DOCUMENT_ACCESS.json');receipts=load(R/'provenance/RA_READING_RECEIPTS.json');check('two_RA_documents_actual_read_receipts_match_SHA',len(ra)==2 and all(r['sha256']==receipts[r['name']]['sha256']and r['read_complete']for r in ra),[(r['name'],r['sha256'])for r in ra])
    required=['TASK.md','TECHNICAL_REPORT.md','FAILURE_LEDGER.md','RESULT_INDEX.md','REPRODUCE.md']+['docs/'+n for n in ['E3_CODE_REUSE_AUDIT.md','E3_SOURCE_SELECTION_PROPOSAL.md','E3_CONFLICT_CASEBOOK.md','E3_LOCAL_FIELD_CONTRACT.md','E3_GLOBAL_FIELD_PROBLEM_DEFINITION.md','E3_EVALUATION_PROTOCOL.md','E3_HYPOTHESIS_PREREGISTRATION.md']]
    check('all_required_reports_exist',all((R/p).is_file()for p in required),required)
    figfacts=[]
    for p in sorted((R/'figures').glob('*.png')):
        im=Image.open(p);im.verify();figfacts.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size))
    check('four_real_project_PNGs_decode',len(figfacts)==4,figfacts)
    # No writing compiler cache, no model runtime imports/calls, no field classes.
    violations=[]
    for p in (R/'code').rglob('*.py'):
        tree=ast.parse(p.read_text());compile(tree,str(p),'exec')
        for n in ast.walk(tree):
            if isinstance(n,ast.ClassDef):violations.append((str(p),'new class',n.name))
            if isinstance(n,ast.Import):
                for a in n.names:
                    if a.name.startswith(('torch','tensorflow','mast3r','mapanything','model.network')):violations.append((str(p),'neural import',a.name))
            if isinstance(n,ast.ImportFrom)and(n.module or'').startswith(('torch','tensorflow','mast3r','mapanything','model.network')):violations.append((str(p),'neural import',n.module))
            if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in ['step','backward','global_optimization','solvePnP','marching_cubes']:violations.append((str(p),'prohibited operation',n.func.attr))
    check('audit_code_parses_no_model_training_fitting_or_field_implementation',not violations,violations)
    logs=[]
    for p in sorted((R/'runtime').glob('*.log')):
        txt=p.read_text(errors='replace');last=txt.strip().splitlines()[-1]if txt.strip()else'EMPTY_NO_PROGRAM_OUTPUT'
        logs.append(dict(file=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size,exception_recorded='Traceback (most recent call last)'in txt,last_line=last,
            retained_local=True,final_scientific_thresholds_changed_for_failure=False))
    save('provenance/EXECUTION_LOG_INDEX.json',logs)
    # Link validation ignores external URLs and fenced pseudo-code, checks real relative artifacts.
    missinglinks=[]
    for p in (R).rglob('*.md'):
        if 'runtime'in p.parts:continue
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://'in target or target.startswith('#'):continue
            target=target.split('#')[0]
            if not (p.parent/target).exists():missinglinks.append((str(p.relative_to(R)),target))
    check('relative_report_links_resolve',not missinglinks,missinglinks)
    execution=dict(model_forward_N=0,new_HERO_inference_N=0,optimizer_step_N=0,GPU_use_N=0,new_fusion_or_global_fit_N=0,
        geometry_deformation_N=0,GT_or_Oracle_read=False,history_measurement_fallback_N=0,scope='E3-A targeted source audit only')
    save('provenance/EXECUTION_BOUNDARY.json',execution)
    output=dict(status='PASS_DELIVERY_INTEGRITY_ONLY'if all(c['status']=='PASS'for c in checks)else'FAIL',checks=checks,
        scientifically_not_certified=['absolute metric camera correctness','same physical surface conflict truth','strict full-pipeline heldout accuracy','true thin-stalk anatomy','hidden anatomy','new algorithm efficacy'],execution_boundary=execution)
    save('metrics/DELIVERY_VALIDATION.json',output);table('metrics/DELIVERY_VALIDATION.csv',checks)
    # No self hash / actively running log cycle.
    artifacts=[asset(p,'final E3-A deliverable')for p in sorted(R.rglob('*'))if p.is_file()and not any(x in p.parts for x in ['runtime','local_results','__pycache__'])and p.name not in ['DELIVERABLE_HASHES.json','DELIVERY_VALIDATION.json','DELIVERY_VALIDATION.csv','RESULT_INDEX.md','EXECUTION_LOG_INDEX.json']]
    save('provenance/DELIVERABLE_HASHES.json',dict(files=artifacts,exclusions='self, active logs/index, validation files and generated result index avoid hash cycles'))
    print('E3_DELIVERY_VALIDATION',output['status'],sum(c['status']=='PASS'for c in checks),'/',len(checks),flush=True)
    for c in checks:
        if c['status']=='FAIL':print('FAILED_CHECK',c,flush=True)
    if output['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
