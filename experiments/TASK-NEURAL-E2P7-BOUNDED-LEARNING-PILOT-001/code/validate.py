"""Final integrity validation only: no GPU construction or parameter updates."""
from common import *
import re
CHECKS=[]
def rows(name):return list(csv.DictReader((R/'metrics'/name).open()))
def check(name,ok,detail=''):
    CHECKS.append(dict(check=name,pass_=bool(ok),detail=detail));print('PASS' if ok else 'FAIL',name,detail,flush=True)
def alltrue(rr,k):return all(r[k]=='True'for r in rr)
def main():
    end=protected_state();save('provenance/PROTECTED_END.json',end);check('all historical worktree states unchanged',end==load(R/'provenance/PROTECTED_START.json'))
    c=cfg();before=load(R/'provenance/BEFORE_NEW_MODEL_OUTPUTS.json');pr=next(x for x in before['config']if x['path'].endswith('/PREREGISTERED.json'))
    check('preregistration unchanged before new model output',sha(pr['path'])==pr['sha256'])
    check('bounded grant used only005 two arms100 cap',c['scene']=='G01_005'and c['references']==REFS and c['MAX_STEPS']==100 and set(c['arms'])=={'A','B'}and c['arms']==dict(A=dict(anchor=0.),B=dict(anchor=.01)))
    check('original seed physical geometry beta frozen',c['seed']==20261031 and c['initialization']['bias_network']==.33739213617088626 and abs(c['domain']['mm_per_unit']-28.3780268204276)<1e-12 and abs(c['domain']['ROI_radius_mm']-10.27908157050465)<1e-12)
    a=load(R/'provenance/BEFORE_ARM_A.json');b=load(R/'provenance/BEFORE_ARM_B.json');a_code={Path(x['path']).name:x['sha256']for x in a['code']};b_code={Path(x['path']).name:x['sha256']for x in b['code']}
    for name in ['common.py','gpu_model_adapter.py','fixed_renderer.py','evaluate.py','train_arm.py']:
        check('A/B identical and current immutable core '+name,a_code[name]==b_code[name]==sha(R/'code'/name))
    check('arms ran sequentially',a['UTC']<b['UTC'])
    for item in load(R/'provenance/REUSED_INPUTS.json')['files']:
        check('read-only source SHA '+item.get('source','')+' '+item['role'],sha(item['path'])==item['sha256']and item.get('hash_match',True))
    for item in list(csv.DictReader((R/'CODE_REUSE_E2P7.csv').open())):
        check('frozen reused source '+item['entry']+' '+Path(item['path']).name,sha(item['path'])==item['file_SHA256'])
    oldreused=list(csv.DictReader((E25/'CODE_REUSE_E2P5.csv').open()));expected=next(x['SHA256']for x in oldreused if x['path']==str(SDF/'code/model/network.py'))
    check('official audited network source unchanged',sha(SDF/'code/model/network.py')==expected and git(SDF,'rev-parse','HEAD')=='12513009cd20a08b35ddc2c55a7e42da2c7baf43')
    pixels=load(R/'provenance/SOURCE_PIXELS.json');check('six exact frozen E2.6 packets',len(pixels)==6)
    total=0;obsall=0;midpoints=[]
    for ref in REFS:
        extra=packet(ref,'extra');small=packet(ref,'small');check('disjoint train monitor '+ref,not np.intersect1d(extra['source_pixel'],small['source_pixel']).size and len(extra['source_pixel'])==64 and len(small['source_pixel'])==16)
        midpoints.extend(extra['origin'][:6]+extra['direction'][:6]*((extra['start'][:6]+extra['end'][:6])/2)[:,None]);check('extra Eikonal first6 Polyp interior '+ref,np.all(extra['sampling_class'][:6]==0))
        for split,p in [('extra',extra),('small',small)]:
            old=next(x for x in pixels if x['source']==ref and x['split']==split);total+=len(p['source_pixel']);obs=p['depth_weight']>0;obsall+=int(obs.sum())
            check('frozen pixels and packet SHA '+ref+'/'+split,np.array_equal(old['pixel'],p['source_pixel'])and sha(old['packet']['path'])==old['packet']['sha256'])
            ring=np.isfinite(p['Ring_t_mm'])&p['valid'];tt=p['target_Z'][obs]/p['cosine'][obs]
            check('no supervised HERO behind CAD or ROI '+ref+'/'+split,np.all(tt>=p['start'][obs])and np.all(tt<=p['end'][obs])and np.all(p['end'][ring]<=p['Ring_t_mm'][ring]-.05+1e-8))
            check('unknown supervision zero '+ref+'/'+split,np.all(p['mask_weight'][p['sampling_class']==4]==0)and np.all(p['depth_weight'][p['sampling_class']==4]==0))
            check('fixed HERO denominators '+ref+'/'+split,int(obs.sum())== (32 if split=='extra' else 6))
    check('fixed240 rays114 HERO total',total==240 and obsall==114)
    check('one shared Eikonal18 train points only',np.array_equal(np.asarray(midpoints),np.asarray(load(R/'config/EIKONAL_TRAIN_POINTS.json'))))
    sampler=rows('SAMPLING_COMPARISON.csv');gp=load(R/'metrics/GPU_PARITY.json')
    check('one128 vs256 comparison6 packets all converged128',len(sampler)==6 and alltrue(sampler,'converged128')and alltrue(sampler,'hit_set_equal')and load(R/'config/SELECTED_SAMPLING.json')['cells']==128)
    check('37 actual CPU GPU checks all pass',gp['pass_']and len(gp['rows'])==37 and all(x['pass_']for x in gp['rows'])and gp['optimizer_step_N']==0 and gp['parameters_unchanged'])
    check('AMP TF32 disabled',gp['AMP']is False and gp['TF32']is False and c['AMP']is False and c['TF32']is False)
    check('initial128 match E2.6 original hit identities',gp['initial128_E26_counts_match'])
    initial=load(R/'provenance/INITIAL_MODEL.json');state0=torch.load(R/'checkpoints/A/step000.pt',map_location='cpu',weights_only=True)
    def statehash(state):
        h=hashlib.sha256()
        for name,t in state.items():h.update(name.encode());h.update(t.numpy().tobytes())
        return h.hexdigest()
    canonical=torch.load(R/initial['path'],map_location='cpu',weights_only=True)
    check('canonical FP64 actual checkpoint exact E2.6 SHA',statehash(canonical)==initial['canonical_SHA256']=='7b5b64e57523d72ededf4c27f2314dd84776066f66197056c44bf014b2b3c81c'and sha(R/initial['path'])==initial['file_SHA256'])
    check('canonical ->FP32 actual initial hash',statehash(state0)==initial['FP32_SHA256']=='c02a788808d3944b35f9901a32cc05600bd1e15ff5c57afb25f2a12f2a2fbac8')
    params=[]
    for arm in ['A','B']:
        run=load(R/f'metrics/{arm}_RUN.json');check('arm '+arm+' stopped immediately after1 real step',run['optimizer_step_N']==1 and run['last_safe_step']==0 and run['status']=='TRAINING_STOPPED'and run['reason']=='PER_REFERENCE_COVERAGE_BELOW50'and not run['engineering_error'])
        check('arm '+arm+' bounded time memory serial dataset',run['elapsed_seconds']<1800 and run['peak_allocated_bytes']<5*2**30 and run['source_view_N']==3 and run['train_rays_per_step']==192 and run['monitor_never_used_for_training'])
        actual=torch.load(R/f'checkpoints/{arm}/STOP_UNSAFE_step001.pt',map_location='cpu',weights_only=True);safe=torch.load(R/run['final_checkpoint']['path'],map_location='cpu',weights_only=True)
        check('arm '+arm+' safe0 equals init actual1 differs',statehash(safe)==statehash(state0)and statehash(actual)!=statehash(state0))
        check('arm '+arm+' all37 parameter tensors actually changed',len(actual)==37 and sum(not torch.equal(actual[k],state0[k])for k in actual)==37)
        delta=sum(float(((actual[k].double()-state0[k].double())**2).sum())for k in actual)**.5;params.append(delta)
        check('arm '+arm+' actual parameter norm equals logged update',abs(delta-next(float(x['parameter_update_L2'])for x in rows('TRAINING_CURVES.csv')if x['arm']==arm and x['step']=='1'))<1e-10)
        check('arm '+arm+' scheduled25+ not fabricated',not any((R/f'checkpoints/{arm}/step{s:03d}.pt').exists()for s in [25,50,75,100]))
    for x in load(R/'provenance/CHECKPOINT_HASHES.json'):
        p=R/x['path'];state=torch.load(p,map_location='cpu',weights_only=True)
        check('checkpoint bytes/params hashes '+x['path'],sha(p)==x['file_SHA256']and statehash(state)==x['parameter_SHA256']and all(torch.is_tensor(v)for v in state.values())and p.stat().st_size<6*2**20)
    rf=rows('PER_REFERENCE_METRICS.csv');cv=rows('TRAINING_CURVES.csv');history=rows('COVERAGE_HISTORY.csv');safety=rows('SAFETY_EVERY_STEP.csv')
    check('only actual0/1 rows, both arms all6 packets',len(rf)==24 and len(cv)==4 and len(history)==24 and len(safety)==12 and {r['step']for r in rf}=={'0','1'})
    old=list(csv.DictReader((E26/'metrics/PER_REFERENCE_NEURAL_SUPERVISION.csv').open()))
    for row in rf:
        check('fixed per-source observed denominator '+row['arm']+'/'+row['source']+'/'+row['split']+'/'+row['step'],int(row['observed_N'])==(32 if row['split']=='extra' else 6)and int(row['front_hit_N'])+int(row['miss_N'])==int(row['observed_N']))
        if row['step']=='0':
            y=next(x for x in old if x['source']==row['source']and x['split']==row['split'])
            check('thin device port inherits E2.6 initial behavior '+row['arm']+'/'+row['source']+'/'+row['split'],int(row['front_hit_N'])==int(y['front_hit_N'])and all(abs(float(row[k])-float(y[oldk]))<=.002+.002*abs(float(y[oldk]))for k,oldk in [('RGB_loss','RGB_loss'),('Depth_loss','Depth_loss'),('Mask_loss','stable_Mask_loss'),('Anchor_loss','weak_anchor_loss')]))
        if row['step']=='1':check('every coverage decrease flagged '+row['arm']+'/'+row['source']+'/'+row['split'],row['status']=='POTENTIAL_FAILURE_COVERAGE_LOWER')
        if row['split']=='extra':check('actual per-term full-gradient finite '+row['arm']+'/'+row['source']+'/'+row['step'],all(row[k+'_gradient_finite']=='True'and float(row[k+'_full_gradient_norm'])>0 for k in ['rgb','depth','mask','anchor']))
    check('hard stop source actually14/32 in both arms',all(int(next(r['front_hit_N']for r in rf if r['arm']==arm and r['step']=='1'and r['split']=='extra'and r['source']==REFS[2]))==14 for arm in ['A','B']))
    check('totalLoss rises while coverage falls, no invented improvement',all(float(next(r['total_loss']for r in cv if r['arm']==arm and r['step']=='1'))>float(next(r['total_loss']for r in cv if r['arm']==arm and r['step']=='0'))for arm in ['A','B']))
    check('original component-sum Adam check remains failed',load(R/'metrics/FIRST_STEP_DIAGNOSIS.json')['all_step_formulas_match']is False and all(r['independent_first_Adam_formula_max_abs_error']>2e-7 for r in load(R/'provenance/COMPONENT_SUM_ADAM_CHECK.json')['rows']))
    exact=load(R/'metrics/EXACT_ACCUMULATION_VERIFICATION.json');check('original backward accumulation matches actual step without relaxed tolerance',exact['all_exact_checks_pass']and exact['additional_optimizer_steps']==0 and all(r['unchanged_tolerance']==2e-7 and r['exact_training_backward_accumulation_max_error']<2e-7 and r['complete_parameter_N']==670395 for r in exact['rows']))
    for key in ['Initial','A_STOP1','B_STOP1']:
        p=np.load(R/f'local_results/surfaces/{key}.npz');check('actual65cubed SDF and unclosed visible subset '+key,p['SDF_mm'].shape==(65,65,65)and p['SDF_mm'].min()<0<p['SDF_mm'].max())
        m=trimesh.load(R/f'figures/surfaces/{key}_visible.ply',process=False);check('visible exported mesh open '+key,len(m.faces)>0 and not m.is_watertight)
        for ref in REFS:
            p=np.load(R/f'local_results/dense/{key}_{ref}.npz');check('dense miss depths remain NaN '+key+'/'+ref,np.isnan(p['depth_mm'][~p['render_hit']]).all())
    surfaces=load(R/'metrics/SURFACE_DIAGNOSTICS.json');base=surfaces[0]['negative_ROI_volume_mm3']
    check('actual contraction not claimed as expansion',all(s['negative_ROI_volume_mm3']<.4*base and s['substantial_raw_component_N']==1 for s in surfaces[1:]))
    check('zero supported denominator CAD stays NOT_EVALUABLE',all(s['supported_vertex_N']==0 and s['CAD_status']=='NOT_EVALUABLE_NO_SUPPORTED_POINTS'and s['CAD_penetration_fraction']is None for s in surfaces[1:]))
    risk=rows('LOW_COVERAGE_LOW_RGB_ERROR.csv');check('12 actual lower coverage/lower RGB warp errors retained',len(risk)==12 and all(float(r['coverage'])<float(r['initial_coverage'])and float(r['RGB_MAE'])<float(r['initial_RGB_MAE'])and r['status']=='POTENTIAL_FAILURE_COVERAGE_LOWER'for r in risk))
    warps=rows('MULTIVIEW_WARPS.csv');check('all18 directed same-source diagnostics; source-only colors',len(warps)==18 and all('SOURCE_A_RGB_ONLY'in r['coloring']and r['independent_view_test']=='False'for r in warps))
    final=load(R/'metrics/FINAL_STATUS.json');comp=load(R/'metrics/A_B_COMPARISON.json')
    check('scientific failure classifications unrelaxed',final['status']=='TRAINING_STOPPED'and final['learning']=='NO_LEARNING'and final['anchor']=='ANCHOR_NOT_BENEFICIAL'and not final['scientific_success']and not comp['coverage_preserved_relative_to_initial'])
    check('scope no other videos models GT or longer runs',final['G01_004_optimizer_steps']==0 and final['MapAnything_forward_N']==0 and not final['GT_opened']and not final['restart_or_hyperparameter_search'])
    for p in (R/'code').glob('*.py'):
        tree=ast.parse(p.read_text());steps=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='step']
        check('optimizer step only in bounded trainer '+p.name,not steps or p.name=='train_arm.py')
    check('trainer one opt.step site bounded loop and parity guard',(R/'code/train_arm.py').read_text().count('opt.step()')==1 and 'range(1,101)'in(R/'code/train_arm.py').read_text()and "['pass_']"in(R/'code/train_arm.py').read_text())
    required=['TASK.md','TECHNICAL_REPORT.md','FAILURE_LEDGER.md','REPRODUCE.md','RESULT_INDEX.md','code/gpu_model_adapter.py','code/fixed_renderer.py','code/train_arm.py','code/evaluate.py','code/visualize.py','metrics/FINAL_STATUS.json','metrics/A_B_COMPARISON.json']
    check('requested deliverables exist',all((R/p).is_file()for p in required))
    text=(R/'TECHNICAL_REPORT.md').read_text();check('report306-character opener and7-row audit table',200<=len(text.split('\n\n')[1])<=350 and all(k in text for k in ['目标组数','本算法独立成功','本算法失败','历史测量值回退','失败组及具体原因','最终统计样本','是否使用GT选择算法']))
    check('report limits one scene and honest step1 endpoint','八个科研问题'in text and 'NOT_RUN'in text and '不能把完成一次Adam更新当作重建成功'in text)
    for p in R.glob('*.md'):
        links=re.findall(r'\]\(([^)]+)\)',p.read_text());bad=[x for x in links if not x.startswith(('http:','https:','#'))and not(p.parent/x.split('#')[0]).exists()]
        bad=[x for x in bad if x not in ['metrics/FINAL_INTEGRITY.json','provenance/DELIVERY_MANIFEST.json']];check('document links '+p.name,not bad,str(bad))
    figs=list((R/'figures').glob('Fig*.png'));check('four core PNGs actual requested names',set(p.name for p in figs)=={'Fig1_SDF_learning.png','Fig2_three_reference_fit.png','Fig3_visible_surface.png','Fig4_multiview_validation.png'}and all(p.stat().st_size<3*2**20 for p in figs))
    f=load(R/'provenance/FIGURE_EVIDENCE.json');check('no synthetic surface/target retexture/backfill claims',f['actual_neural_fields']and not f['analytic_spheres_used']and not f['backside_filled']and f['scheduled_25_50_100']=='NOT_RUN')
    check('no GPU initialized by final validation',not torch.cuda.is_initialized())
    changed=git(REPO,'diff','--name-only','a69a17099e4ed5ff34ed8e1be49157fbda329615','HEAD').splitlines();check('commits only independent task',all(p.startswith('experiments/'+R.name+'/')for p in changed))
    check('no full input/video/cache uploads',all(Path(p).suffix.lower()not in ['.npz','.mp4','.zip','.ckpt','.safetensors']for p in changed))
    failures=[x for x in CHECKS if not x['pass_']];table('metrics/FINAL_INTEGRITY_CHECKS.csv',CHECKS)
    save('metrics/FINAL_INTEGRITY.json',dict(status='FAIL_INTEGRITY'if failures else'PASS_INTEGRITY_WITH_TRAINING_STOPPED',check_N=len(CHECKS),passed_N=len(CHECKS)-len(failures),failed_N=len(failures),failed_checks=failures,
        scientific_status='TRAINING_STOPPED_NO_LEARNING',additional_optimizer_steps=0,GPU_initialized_in_validation=False))
    entries=[];local=[];excluded={'provenance/DELIVERY_MANIFEST.json','metrics/FINAL_INTEGRITY.json','metrics/FINAL_INTEGRITY_CHECKS.csv'}
    for p in sorted(R.rglob('*')):
        if not p.is_file():continue
        rel=str(p.relative_to(R))
        if rel in excluded or '__pycache__'in p.parts:continue
        if rel.startswith('runtime/'):
            if p.suffix!='.log'or p.name.startswith('FINAL_'):continue
            local.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)));continue
        item=dict(path=rel,bytes=p.stat().st_size,sha256=sha(p));(local if rel.startswith('local_results/')else entries).append(item)
    save('provenance/DELIVERY_MANIFEST.json',dict(task=R.name,files=entries,LOCAL_ONLY=local,scientific_status='TRAINING_STOPPED',
        exclusions='self, integrity outputs, active FINAL_* logs; avoids self-referential/active-log hashes',checkpoint_uploads='7 small state_dict files only; no original model/video archives'))
    print('FINAL_INTEGRITY',len(CHECKS)-len(failures),'/',len(CHECKS),'science TRAINING_STOPPED; no further steps',flush=True)
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
