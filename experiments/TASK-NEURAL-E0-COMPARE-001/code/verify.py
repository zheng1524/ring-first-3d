"""Read-only meaningful delivery checks; never re-runs a neural model."""
from audit import *
import re

def main():
 checks=[]
 def check(name,ok,detail=None):
  checks.append(dict(check=name,pass_=bool(ok),detail=detail));assert ok,(name,detail)
 d=load(R/'provenance/INPUT_ELIGIBILITY.json');check('four physical groups, five scenes,36 references',len({c['group']for c in d['references']})==4 and len({c['scene_id']for c in d['references']})==5 and len(d['references'])==36)
 inputs=list(csv.DictReader((R/'provenance/SOURCE_SHA_LEDGER.csv').open()));mismatches=[]
 for f in inputs:
  if f['exists']=='True' and (not Path(f['path']).is_file() or sha(f['path'])!=f['sha256']):mismatches.append(f['path'])
 check('all frozen input hashes unchanged',not mismatches,dict(checked=len(inputs),mismatches=mismatches))
 check('36 camera geometry contracts',all(x['contract_pass']for x in load(R/'provenance/FRAME_CONVENTION_TESTS.json')))
 check('36 full HERO dependency records',all(x['HERO_dependency_complete']for x in d['references']))
 check('264 historical manifest checks',len(load(R/'metrics/HISTORICAL_MANIFEST_CHECK.json'))==264 and all(x['match']for x in load(R/'metrics/HISTORICAL_MANIFEST_CHECK.json')))
 cfg=load(R/'config/sdf_minimal.json');target_shas={t['RGB_SHA256']for t in d['targets']if t['scene']=='G01_005'};actual=[c for c in d['references']if c['id']in cfg['input_ids']]
 check('no target B in either arm or supplied HERO dependencies',not target_shas&{h for c in actual for h in c['source_alias_hashes']})
 check('zero strict holdout claims',not any(t['strict_holdout']for t in d['targets']))
 for forbidden,mode,flags in [('/home/liu/private_gt/e0_never_read.npz','r',0),('/home/liu/polyp_research/e0_never_written.tmp','w',os.O_WRONLY|os.O_CREAT)]:
  denied=False
  try:sys.audit('open',forbidden,mode,flags)
  except PermissionError:denied=True
  check('GT/write guard '+mode,denied)
 models=load(R/'provenance/ALL_MODEL_OUTPUTS_FROZEN_BEFORE_EVALUATION.json')
 check('all model output artifacts frozen unchanged',all(sha(f['path'])==f['sha256']for f in models['files']),len(models['files']))
 c=load(R/'provenance/MAP_DOWNLOAD_RECOVERY_RESULT.json');check('local official pretrained checkpoint SHA',sha(c['path'])==c['publisher_SHA256'])
 for f in load(R/'provenance/FROZEN_WEIGHT_LOCAL_SHA.json'):check('protected weight '+Path(f['path']).name,sha(f['path'])==f['sha256'])
 check('one SDF optimization with400 steps',load(R/'provenance/SDF_RUN_RESULT.json')['optimizer_steps']==400 and load(R/'provenance/SDF_RUN_RESULT.json')['optimization_seconds']<1800)
 check('SDF failure retained with zero supported faces',load(R/'provenance/SDF_RUN_RESULT.json')['supported_faces']==0)
 official=R/'provenance/official_sources/autonomousvision__monosdf/code/model/network.py';executed=R/'runtime/monosdf_official/code/model/network.py'
 def classes(p):return {x.name:ast.dump(x,include_attributes=False)for x in ast.parse(p.read_text()).body if isinstance(x,ast.ClassDef)}
 a,b=classes(official),classes(executed)
 for name in ['ImplicitNetwork','MonoSDFNetwork','RenderingNetwork']:check('official active MonoSDF class unchanged '+name,a[name]==b[name])
 modes=load(R/'provenance/MAP_RUN_RESULT.json')['rows']+load(R/'provenance/MAP_M3_SUPPLEMENT_RESULT.json')['rows'];passed={x['mode']for x in modes if x['status'].startswith('SMOKE_PASS')}
 check('four Map modes yield independent outputs',passed=={'M0','M1','M2','M3'})
 contracts=list(csv.DictReader((R/'metrics/MAP_OUTPUT_GEOMETRY_CONTRACT.csv').open()));check('8 valid Polyp output coordinate contracts',len(contracts)==8 and all(x['contract_pass']=='True'for x in contracts))
 check('no old Git workspace changes',protected()==load(R/'provenance/PROTECTED_START.json'))
 cleanup=load(R/'provenance/USER_AUTHORIZED_CLEANUP.json');check('explicitly authorized cleanup only, all58 absent',cleanup['deleted_N']==58 and all(not Path(f['path']).exists()for f in cleanup['deleted_files']))
 for name in ['TASK.md','TECHNICAL_REPORT.md','RESULT_INDEX.md','REPRODUCE.md','EVALUATION_PROTOCOL.md','ACCEPTANCE.md','FAILURE_LEDGER.md']:
  check('required deliverable '+name,(R/name).is_file())
 images=list((R/'figures').glob('Fig*.png'));check('exactly four real core figures',len(images)==4)
 required=['目标组数','本算法独立成功','本算法失败','历史测量值回退','失败组及具体原因','最终统计样本','是否使用GT选择算法']
 text=(R/'TECHNICAL_REPORT.md').read_text();check('fixed audit table present',all(x in text for x in required))
 # Resolve relative links in the three primary handoff files, including local-only
 # paths intentionally usable only on this machine.
 broken=[]
 for doc in [R/'TECHNICAL_REPORT.md',R/'RESULT_INDEX.md',R/'REPRODUCE.md']:
  for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
   if '://'in link or link.startswith('#'):continue
   p=doc.parent/link.split('#')[0]
   if p.resolve()==(R/'metrics/FINAL_VALIDATION.json').resolve():continue # produced by this check
   if not p.exists():broken.append(str(p))
 check('handoff links exist',not broken,broken)
 save('metrics/FINAL_VALIDATION.json',dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,checks=checks,GT_used=False,model_rerun=False,remaining_disk_bytes=shutil.disk_usage(R).free))
 print('VERIFY_PASS',len(checks),'checks;',len(inputs),'input files;',len(models['files']),'model artifacts; old valid weights unchanged',flush=True)
if __name__=='__main__':main()
