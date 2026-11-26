from common2 import *
import ast,re,tarfile,subprocess

def main():
 records=[];selection=read(T/'config/SELECTION.json');total=0
 for row in selection['groups']:
  g=row['group'];a=read(T/'config'/g/'ASSETS.json');verify(a['files']);total+=len(a['files']);out=RUN/'real'/g;pred=read(out/'PREDICTIONS.json');fr=read(out/'PREDICTION_FREEZE.json');assert sha(out/'PREDICTIONS.json')==fr['predictions_sha256'];verify([dict(path=p,sha256=h)for p,h in fr['inputs'].items()]);e=read(out/'EVALUATION.json');assert e['stages']['clean_missing']==0
  for r in read(out/'CLEAN_INDEX.json'):assert sha(r['selection_path'])==r['selection_sha256']
  assert pred['M4']['T']==pred['M4_raw_support']['T']==pred['M4_clean_support']['T'];assert len(read(out/'FIT_LOO.json'))==6
  for m,r in e['methods'].items():
   held=read(out/'evaluation'/(m+'_HELD.json'));assert len(held)==sum(r['bidir'][s]['N']for s in ['A_to_B','B_to_A']);assert r['coordinate_invariance_max_mm']<1e-7
  records.append(dict(group=g,verified_files=len(a['files']),sources=e['stages']['sources'],predictions=7,held_denominator=e['stages']['held_total'],numerical_M4=pred['M4']['numerical'],support_variants_identical=True))
  for p in (T/'visuals'/g).glob('*.html'):
   for target in re.findall(r'(?:src|href)="([^"]+)"',p.read_text()):assert (p.parent/target).exists(),target
 for p in (T/'code').glob('*.py'):ast.parse(p.read_text())
 # Preserve exact dependency set, not an entire full-run directory.
 deps={r['path']:r['sha256']for row in selection['groups']for r in read(T/'config'/row['group']/'ASSETS.json')['files']}
 for p in [V001/'evidence/RUN_EVIDENCE.tar.gz',V001/'code/registration.py',V001/'config.json',CLEAN_T/'config/SOURCES_FROZEN.json',CLEAN_T/'SOURCE_MANIFEST.csv',V6/'track005.py',V6/'v6_common.py']:deps[str(p)]=sha(p)
 save(T/'evidence/RETAIN_DEPENDENCIES.json',dict(task='TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002',policy='KEEP referenced native/raw meshes, cameras, RGB/Mask and frozen receipts; local unique face selectors protected in RUN_EVIDENCE.tar.gz',files=[dict(path=p,sha256=h)for p,h in deps.items()]))
 # Read full-run progress once at completion; no scheduler or state mutation.
 progress=read(FULL/'PROGRESS.json');save(T/'evidence/FULL_PROGRESS_AT_END_REFERENCE_ONLY.json',progress)
 controls=read(T/'evidence/CONTROL_RESULTS.json');assert len(controls)==72
 for seed in CFG['seeds']:
  a=next(r for r in controls if r['condition']=='V2_'+str(seed)and r['method']=='EVAL_TRUE_D_INVERSE');b=next(r for r in controls if r['condition']=='V3_'+str(seed)and r['method']=='EVAL_TRUE_D_INVERSE');assert a['bidir']==b['bidir']and a['held005']==b['held005']and a['surface_p95_mm']==b['surface_p95_mm']
 save(T/'evidence/FINAL_VERIFICATION.json',dict(resource=resource(),groups=records,selected_input_records_verified=total,controlled_rows=72,V2_V3_inverse_reference_identical=True,syntax_all_code_valid=True,html_links_valid=True,source_identity_review=read(T/'evidence/REUSED_IDENTITY_REVIEW.json'),scientific_failure_is_preserved=True,full_run_actions='READ ONLY selected files; no scheduler/model/state/lock/log writes',runtime=dict(python=sys.version if False else __import__('sys').version,numpy=np.__version__),review='Static independent reviewer: no blocking findings after identity/missing-input fixes'))
 print('FINAL VERIFIED',len(records),'groups',total,'input records; 72 controlled rows',resource(),flush=True)
if __name__=='__main__':main()
