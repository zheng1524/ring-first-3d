"""Read-only science-output integrity checks; NO neural construction or rerun."""
from common import *
from stable_losses import packet
import re

CHECKS=[]
def rows(name):return list(csv.DictReader((R/name).open()))
def check(name,ok,detail=''):
    CHECKS.append(dict(check=name,pass_=bool(ok),detail=detail));print('PASS' if ok else 'FAIL',name,detail,flush=True)
def alltrue(rr,key):return all(r[key]=='True' for r in rr)
def main():
    start=load(R/'provenance/PROTECTED_START.json');end=protected_state();save('provenance/PROTECTED_END.json',end)
    check('protected worktree heads/status/user modifications unchanged',start==end,len(end))
    refs=[r for rr in selected().values() for r in rr];check('six authorized source identities only',refs==['G01_004_ref03','G01_004_ref08','G01_004_ref13','G01_005_raw00057','G01_005_raw00459','G01_005_raw00745'])
    cf=cfg();frozen=load(R/'provenance/BEFORE_CALIBRATION_AND_LOSS_TESTS.json')
    prereg=next(x for x in frozen['config'] if x['path'].endswith('/PREREGISTERED.json'))
    check('preregistration hash unchanged since before new predictions',sha(prereg['path'])==prereg['sha256'])
    check('single frozen calibration and 50 percent gate',cf['shell_point_N']==128 and cf['shell_radius_fraction']==.5 and cf['minimum_HERO_front_hit_fraction']==.5 and cf['seed']==20261031)
    check('no update GPU GT Map grant or execution',cf['model_update_N']==cf['optimizer_step_N']==cf['MapAnything_forward_N']==0 and cf['GPU']=='NOT_AUTHORIZED' and cf['GT'] is False)
    check('official frozen revision retained',git(SDF,'rev-parse','HEAD')=='12513009cd20a08b35ddc2c55a7e42da2c7baf43')
    prior=rows(str(E25/'CODE_REUSE_E2P5.csv'))
    for rel in ['code/model/network.py','code/model/density.py','code/confs/dtu_mlp_3views.conf']:
        p=SDF/rel;expected=next(x['SHA256'] for x in prior if x['path']==str(p));check('official audited local source unchanged: '+rel,sha(p)==expected)
    oldmanifest=load(E25/'provenance/DELIVERY_MANIFEST.json');oldfiles={x['path']:x['sha256'] for x in oldmanifest['files']}
    for rel in ['code/common.py','code/official_sdf_cpu_adapter.py']:
        check('E2.5 source immutable: '+rel,sha(E25/rel)==oldfiles[rel])
    for r in rows('CODE_REUSE_E2P6.csv'):
        check('read-only reuse SHA '+r['name']+' '+Path(r['path']).name,sha(r['path'])==r['file_SHA256'])
    used=load(R/'provenance/REUSED_INPUTS.json')['files']
    for r in used:
        check('reused source SHA '+r.get('source','metadata')+' '+r['role'],sha(r['path'])==r['sha256'] and r.get('hash_match',True))
    probes=load(R/'provenance/SOURCE_PROBES_FROZEN.json');check('twelve frozen packets',len(probes)==12)
    observedtotal=0;raytotal=0
    for ref in refs:
        small=packet(ref,'small');extra=packet(ref,'extra');old=load(E25/f'provenance/{ref}_CPU_PIXEL_SELECTION.json')['pixel']
        check('same old16 source pixels '+ref,np.array_equal(small['source_pixel'],old) and len(small['source_pixel'])==16)
        check('fixed extra64 excludes all old16 '+ref,len(extra['source_pixel'])==64 and not np.intersect1d(old,extra['source_pixel']).size)
        for split,b in [('small',small),('extra',extra)]:
            saved=next(x for x in probes if x['source']==ref and x['split']==split);a=saved['packet'];check('packet SHA frozen before predictions '+ref+'/'+split,sha(a['path'])==a['sha256'] and np.array_equal(saved['pixel'],b['source_pixel']))
            obs=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0);t=b['target_Z'][obs]/b['cosine'][obs];ring=np.isfinite(b['Ring_t_mm'])&b['valid']
            check('HERO inside certified finite prefix '+ref+'/'+split,bool(np.all((t>=b['start'][obs])&(t<=b['end'][obs]))))
            check('finite prefix ends before first CAD '+ref+'/'+split,bool(np.all(b['end'][ring]<=b['Ring_t_mm'][ring]-.05+1e-8)))
            check('world/net metric round trip '+ref+'/'+split,bool(np.max(abs(((b['origin']-domains()[saved['scene']]['world_origin_mm'])/domains()[saved['scene']]['mm_per_unit'])*domains()[saved['scene']]['mm_per_unit']+domains()[saved['scene']]['world_origin_mm']-b['origin']))<1e-12))
            observedtotal+=int(obs.sum());raytotal+=len(b['source_pixel'])
    check('all fixed observed and ray denominators',observedtotal==227 and raytotal==480,f'{observedtotal} HERO / {raytotal} rays')
    init=rows('INITIALIZATION_VALIDATION.csv');gate=load(R/'metrics/INITIALIZATION_GATE.json');cal=load(R/'config/SHELL_CALIBRATION_FROZEN.json')
    check('calibration failure kept and search stopped',gate['passed'] is False and gate['one_rule'] and gate['additional_rule_search_allowed'] is False and gate['status']=='FAIL_STOP_INITIALIZATION_SEARCH')
    p1freeze=load(R/'provenance/P1_BEFORE_OFFICIAL_SHELL_QUERY.json');p2freeze=load(R/'provenance/P2_FULL_PARAMETER_TESTS_BEFORE_RUN.json')
    check('prediction-independent probes frozen before neural tests',frozen['UTC']<p1freeze['UTC']<p2freeze['UTC'])
    for sc,c in cal.items():
        z=np.load(R/f'local_results/initialization/{sc}_zero_slice.npz');s=c['signs']
        check('one rule signs and physical beta '+sc,c['search_N']==1 and c['seed']==20261031 and abs(c['beta_mm']-.08)<1e-6 and s['center_SDF_mm']<0 and all(s[k]>=.95 for k in ['inner_negative_fraction','ROI_boundary_positive_fraction','outside_ROI_positive_fraction']) and abs(s['shell_median_mm'])<1e-5)
        check('actual shell trace agrees '+sc,len(z['shell_SDF_mm'])==128 and abs(float(np.median(z['shell_SDF_mm']))-s['shell_median_mm'])<1e-12 and z['after_SDF_mm'].min()<0<z['after_SDF_mm'].max())
    for r in init:
        p=np.load(R/f"local_results/initialization/{r['source']}_{r['split']}.npz");obs=p['observed'];cross=p['raw_front_cross'];hit=p['render_hit'];N=int(obs.sum());H=int((hit&obs).sum())
        f=p['raw_sdf'];fs=p['start_sdf'];recomputed=((f[:,:-1]>0)&(f[:,1:]<=0)).any(1)|((fs>=0)&(f[:,0]<0));recomputed&=np.isfinite(fs)
        check('actual positive-to-negative fronts and frozen counts '+r['source']+'/'+r['split'],N==int(r['observed_HERO_N']) and H==int(r['front_hit_N']) and np.array_equal(cross,recomputed) and np.array_equal(hit,cross&(p['opacity']>=1e-4)))
    failures=[r for r in init if r['HERO_hit_gate']=='False'];check('only fixed ref13 small rate fails; retained',len(failures)==1 and failures[0]['source']=='G01_004_ref13' and failures[0]['split']=='small' and int(failures[0]['front_hit_N'])==2)
    stable=rows('STABLE_MASK_GRADIENT_TESTS.csv');check('60 real-neural Mask cases finite',len(stable)==60 and alltrue(stable,'stable_loss_finite') and alltrue(stable,'all_parameter_gradients_finite'))
    check('all full parameters tested, not scalar shift',all(int(x['full_parameter_N'])==670395 and int(x['parameter_tensor_N'])==37 and x['only_scalar_output_derivative']=='False' and x['model_parameters_updated']=='False' for x in stable))
    check('all positive/negative controls true raw signs',alltrue(stable,'field_sign_control_valid'))
    badold=[x for x in stable if x['old_loss_finite']=='False'];check('13 old FP32 nonfinite failures preserved',len(badold)==13 and all(x['precision']=='FP32' and not x['old_loss'] for x in badold))
    neg=[x for x in stable if x['case']=='ALL_NEGATIVE_FIELD'];check('negative saturation not labelled geometry recovery',len(neg)==12 and all(x['useful_geometry_gradient']=='False' and float(x['stable_geometry_gradient_norm'])<cf['useful_geometry_gradient_norm_min'] for x in neg))
    pos=[x for x in stable if x['case'] in ['ALL_POSITIVE_FIELD','EMPTY_POSITIVE_RAYS']];check('stable Mask positive/empty real geometry gradients',len(pos)==24 and alltrue(pos,'useful_geometry_gradient'))
    fp=rows('metrics/FP32_FP64_CONSISTENCY.csv');mp=rows('metrics/MATH_TARGET_EQUIVALENCE.csv');pg=rows('metrics/PROBE_GEOMETRY_PRECISION.csv')
    check('30 full-gradient precision cases pass',len(fp)==30 and alltrue(fp,'loss_consistency_pass') and alltrue(fp,'full_gradient_consistency_pass'))
    check('48 high-precision unchanged BCE target checks pass',len(mp)==48 and alltrue(mp,'same_finite_interval_target') and alltrue(mp,'pass_') and max(float(x['abs_error']) for x in mp)<1e-6)
    check('12 geometry-only precision probes pass',len(pg)==12 and alltrue(pg,'geometry_precision_gate') and all(float(x['geometry_gradient_cosine_FP32_FP64'])>=.995 and float(x['geometry_norm_relative_difference'])<=.02 for x in pg))
    a=rows('metrics/WEAK_HERO_ANCHOR_GRADIENTS.csv');point=rows('metrics/WEAK_HERO_POINT_DIRECTIONS.csv');ag=load(R/'metrics/WEAK_ANCHOR_GATE.json')
    check('24 true neural weak-anchor geometry gradients',len(a)==24 and alltrue(a,'all_parameter_gradients_finite') and all(float(x['geometry_gradient_norm'])>1e-10 and float(x['trunk_gradient_norm'])>1e-10 and float(x['beta_gradient_norm'])==0 and float(x['source_component_weight'])==1/3 for x in a))
    check('96 full-parameter point directions toward zero',len(point)==96 and alltrue(point,'first_order_toward_zero') and all(float(x['SDF_mm'])*float(x['directional_df_along_negative_full_parameter_anchor_gradient'])<0 and x['actual_model_parameter_step_N']=='0' for x in point))
    check('weak anchor candidate remains non-hit-gated and not native correction',alltrue(a,'visible_HERO_only') and alltrue(a,'predicted_hit_not_used_for_anchor') and alltrue(a,'candidate_only') and all(x['raw_depth_modified']=='False' for x in a))
    check('no claim of observed surface recovery or free-space evidence',ag['candidate_first_order_gradient_gate'] and not ag['observed_zero_crossing_recovery_verified'] and not ag['mainline_adoption'] and not ag['additional_free_space_constraint_added'] and ag['no_ROI_entry_outside_assumption'])
    n=rows('metrics/PER_REFERENCE_NEURAL_SUPERVISION.csv');ng=load(R/'THREE_REFERENCE_NEURAL_GATE.json')
    check('12 reference/split triples actual finite geometry gradients',len(n)==12 and alltrue(n,'all_three_actual_gradient_gate') and all(all(float(x[k])>1e-10 for k in ['Mask_geometry_gradient','RGB_geometry_gradient','Depth_geometry_gradient']) for x in n))
    check('actual finite prefix Ring checks all pass',alltrue(n,'finite_prefix_only') and alltrue(n,'before_first_Ring'))
    check('shared networks isolated by video',all(len({x['shared_network_identity'] for x in n if x['scene']==sc})==1 for sc in selected()) and len({x['shared_network_identity'] for x in n})==2)
    check('strict final gate not changed to pass',ng['status']=='FAIL_FIXED_SOURCE_GATE' and ng['Q1_strict_pass'] is False and ng['threshold']==.5 and ng['small_and_disjoint_extra_both_required'] and not ng['additional_search_performed'])
    for r in n:
        p=np.load(R/f"local_results/neural/{r['source']}_{r['split']}.npz");obs=p['observed'];hit=p['render_hit']
        check('renderer hit/miss depth NaN preserved '+r['source']+'/'+r['split'],int((obs&hit).sum())==int(r['front_hit_N']) and int((obs&~hit).sum())==int(r['miss_N']) and np.isnan(p['depth_mm'][~hit]).all())
    for name,key in [('STABLE_TEST_MODEL_STATES.json','parameters_unchanged'),('WEAK_ANCHOR_MODEL_STATES.json','unchanged'),('P5_MODEL_STATES.json','unchanged'),('ZERO_LEVEL_CONTROL_STATES.json','unchanged')]:
        states=load(R/'provenance'/name);check('parameters immutable '+name,all(s[key] for s in states))
        if name=='STABLE_TEST_MODEL_STATES.json':check('before-after actual parameter hashes equal',all(s['parameter_SHA_before']==s['parameter_SHA_after'] for s in states))
        if name=='P5_MODEL_STATES.json':check('P5 canonical models exactly frozen calibrated SHA',all(s['parameter_SHA256']==cal[s['scene']]['model_parameter_SHA256'] for s in states if s['precision']=='FP64'))
    c=rows('COVERAGE_DEGENERACY_VALIDATION.csv');cg=load(R/'metrics/COVERAGE_GATE.json');hist=rows('metrics/HISTORICAL_FIXED_COVERAGE.csv')
    check('48 coverage controls retain observed denominator',len(c)==48 and all(sum(y['observed_N'] for y in json.loads(x['fixed_per_reference_observations']))==int(x['observed_HERO_N']) for x in c))
    check('all lower coverage rejected, risk remains all variants',all(x['accepted_as_improvement']=='False' for x in c if x['coverage_non_decrease_gate']=='False') and cg['risk_rows_by_variant']==dict(CURRENT=7,STABLE_MASK=7,STABLE_MASK_PLUS_WEAK_ANCHOR=7) and not cg['any_loss_variant_structurally_immune'])
    check('coverage counts never used as a differentiable loss',all(x['discrete_hit_count_used_as_training_gradient']=='False' and x['continuous_model_prediction']=='False' for x in c))
    check('all-miss regression values remain not evaluable',all(not x['Depth_loss'] and not x['RGB_loss'] and not x['total_loss'] and int(x['front_hit_N'])==0 for x in c if x['condition']=='ALL_HITS_REMOVED'))
    check('all historical A and B controls retained, A3 drops B0',len(hist)==12 and cg['historical_A_coverage_drops']==3 and cg['historical_B_coverage_drops']==0)
    z=rows('metrics/ZERO_LEVEL_VS_OPACITY.csv');check('36 raw-zero versus opacity controls',len(z)==36 and alltrue(z,'high_opacity_is_NOT_zero_crossing') and all(x['ROI_entry_outside_assumed']=='False' for x in z))
    nz=[x for x in z if x['control']=='NEGATIVE'];normal=[x for x in z if x['control']=='NORMAL'];check('negative opaque field has no fronts on all227 observations',sum(int(x['observed_N']) for x in nz)==227 and sum(int(x['high_opacity_N']) for x in nz)==227 and sum(int(x['front_cross_N']) for x in nz)==0)
    check('normal positive-tail high-opacity misses retained',sum(int(x['positive_tail_high_opacity_without_zero_N']) for x in normal)==4)
    trace=load(R/'provenance/START_SDF_TRACE_CORRECTION.json');check('trace correction no gate/scientific metric changes',not trace['scientific_metrics_changed'] and not trace['gate_changed'] and len(trace['files'])==12 and all(x['opacity_and_front_hit_unchanged'] and sha(R/f"local_results/initialization/{x['source']}_{x['split']}.npz")==x['new_SHA256'] for x in trace['files']))
    rc=rows('metrics/RING_OCCLUSION_COUNTS.csv');check('all qualified HERO exclude behind-CAD samples',len(rc)==12 and all(int(x['qualified_HERO_behind_CAD_N'])==0 for x in rc))
    for p in sorted((R/'code').glob('*.py')):
        tree=ast.parse(p.read_text());bad=[]
        for node in ast.walk(tree):
            if not isinstance(node,ast.Call):continue
            name=ast.unparse(node.func)
            if name.endswith('.step') or name.startswith(('torch.optim.','torch.cuda.')):bad.append(name)
            if isinstance(node.func,ast.Attribute) and node.func.attr in ['cuda','to'] and any(isinstance(x,ast.Constant) and isinstance(x.value,str) and x.value.startswith('cuda') for x in node.args):bad.append(name)
        check('no optimizer or GPU call in local AST '+p.name,not bad,','.join(bad))
    check('CPU-only inherited adapter retains GPU denial','def forbid_gpu' in (E25/'code/official_sdf_cpu_adapter.py').read_text() and 'torch.Tensor.cuda=forbid_gpu' in (E25/'code/official_sdf_cpu_adapter.py').read_text())
    required=['TECHNICAL_REPORT.md','FAILURE_LEDGER.md','INITIALIZATION_VALIDATION.csv','STABLE_MASK_GRADIENT_TESTS.csv','COVERAGE_DEGENERACY_VALIDATION.csv','THREE_REFERENCE_NEURAL_GATE.json','GPU_MVP_READINESS.md']
    check('all seven requested deliverables exist',all((R/n).is_file() and (R/n).stat().st_size>100 for n in required))
    text=(R/'TECHNICAL_REPORT.md').read_text();opening=text.split('\n\n')[1];check('200-350 character opener',200<=len(opening)<=350,len(opening))
    check('fixed seven-row measurement audit table',all(s in text for s in ['目标组数','本算法独立成功','本算法失败','历史测量值回退','失败组及具体原因','最终统计样本','是否使用GT选择算法']))
    check('no-readiness and no-measurement claims retained','NOT_READY' in (R/'GPU_MVP_READINESS.md').read_text() and '0/1' in text and 'NaN' in text and '严格全流程留出仍为0' in text)
    for p in R.glob('*.md'):
        links=re.findall(r'\]\(([^)]+)\)',p.read_text());bad=[x for x in links if not x.startswith(('http:','https:','#')) and not (p.parent/x.split('#')[0]).exists()]
        # Manifest and final validation products are written below this check.
        bad=[x for x in bad if x not in ['provenance/DELIVERY_MANIFEST.json','metrics/FINAL_INTEGRITY.json','metrics/FINAL_INTEGRITY_CHECKS.csv']]
        check('document links exist '+p.name,not bad,str(bad))
    figures=sorted((R/'figures').glob('Fig*.png'));check('four actual evidence PNGs under2MiB each',len(figures)==4 and all(p.stat().st_size<2**21 and min(Image.open(p).size)>700 for p in figures))
    check('figure evidence labels untrained true raw project data',load(R/'provenance/FIGURE_EVIDENCE.json')['untrained'] and 'UNTRAINED' in (R/'code/figures.py').read_text())
    for name in ['STABLE_ATTEMPT001.log','REPORT_ATTEMPT001.log']:
        check('failed execution retained '+name,(R/'runtime'/name).is_file() and 'Traceback' in (R/'runtime'/name).read_text())
    for name,marker in [('PREREGISTER.log','E2P6_FROZEN_ONE_RULE'),('CALIBRATION_ATTEMPT001.log','ONE_RULE_INITIALIZATION_COMPLETE False'),('STABLE_FINAL.log','STABLE_MASK_CPU_COMPLETE'),('WEAK_ANCHOR.log','WEAK_ANCHOR_CANDIDATE_COMPLETE'),('NEURAL_GATE.log','THREE_REFERENCE_FINAL_GATE False'),('COVERAGE.log','COVERAGE_VALIDATION_COMPLETE'),('ZERO_LEVEL_CONTROLS.log','ZERO_LEVEL_OPACITY_CONTROL_COMPLETE'),('FIGURES.log','FOUR_REAL_EVIDENCE_FIGURES_COMPLETE'),('REPORT.log','REPORTS_COMPLETE')]:
        check('closed stage log '+name,marker in (R/'runtime'/name).read_text())
    changed=git(REPO,'diff','--name-only','1eb9cc7fd49b70cf8370582dded7decb1d1cd4be','HEAD').splitlines()
    check('committed changes only independent task directory',all(p.startswith('experiments/'+R.name+'/') for p in changed))
    check('no raw archives videos checkpoints uploaded',all(Path(p).suffix.lower() not in ['.npz','.pth','.pt','.ckpt','.safetensors','.mp4','.zip'] for p in changed))
    failures=[x for x in CHECKS if not x['pass_']]
    table('metrics/FINAL_INTEGRITY_CHECKS.csv',CHECKS)
    save('metrics/FINAL_INTEGRITY.json',dict(status='FAIL_INTEGRITY' if failures else 'PASS_INTEGRITY_WITH_RESEARCH_GATES_FAILED',check_N=len(CHECKS),passed_N=len(CHECKS)-len(failures),failed_N=len(failures),
        failed_checks=failures,scientific_three_reference_gate='FAIL',GPU_MVP='NOT_READY',GPU='NOT_AUTHORIZED',optimizer_step_N=0,
        neural_recomputation_in_this_validation=False,old_audits_rerun=False,excluded_from_manifest=['provenance/DELIVERY_MANIFEST.json','metrics/FINAL_INTEGRITY.json','metrics/FINAL_INTEGRITY_CHECKS.csv','runtime/FINAL_VALIDATION.log','runtime/FINAL_GIT_SYNC.json']))
    exclude={'provenance/DELIVERY_MANIFEST.json','metrics/FINAL_INTEGRITY.json','metrics/FINAL_INTEGRITY_CHECKS.csv'};files=[];local=[]
    for p in sorted(R.rglob('*')):
        if not p.is_file():continue
        rel=str(p.relative_to(R))
        if '__pycache__' in p.parts or rel in exclude:continue
        if rel.startswith('runtime/'):
            if p.suffix!='.log' or p.name.startswith('FINAL_'):continue
            local.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)));continue
        entry=dict(path=rel,bytes=p.stat().st_size,sha256=sha(p))
        (local if rel.startswith('local_results/') else files).append(entry)
    save('provenance/DELIVERY_MANIFEST.json',dict(task=R.name,files=files,LOCAL_ONLY=local,scientific_status='FAIL_FIXED_SOURCE_GATE',GPU_MVP='NOT_READY',GPU='NOT_AUTHORIZED',
        exclusions='self, integrity outputs and active FINAL_* logs intentionally excluded to avoid self/active-log hash cycles'))
    print('FINAL_INTEGRITY',len(CHECKS)-len(failures),'/',len(CHECKS),'scientific gates remain FAIL; GPU NOT_AUTHORIZED',flush=True)
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
