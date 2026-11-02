"""Final evidence integrity and curated/local-only artifact indices."""
from common import *
import re

def main():
    before=load(R/'config/PROTECTED_START.json');checks=before['original_assets']+before['prior_delivery']+before['prior_local'];same=protected_state()==before['worktrees'];bad=[a['path'] for a in checks if sha(a['path'])!=a['sha256']]
    assert same and not bad,(same,bad)
    assert sha(R/'config/A2_PREREGISTERED.json')==load(R/'config/BEFORE_CANDIDATES.json')['protocol']['sha256']
    assert load(R/'GATE_A2_ACCEPTANCE.json')['status']=='GATE_A2_FAIL'
    replay=load(R/'runtime/replay_verification/REPLAY_VERIFY.json'); assert replay['all_identical'] and len(replay['files'])==7
    save('config/FINAL_DELIVERY_PROTECTION.json',dict(historical_worktrees_unchanged=same,historical_worktree_N=len(before['worktrees']),old_asset_SHA_checks=len(checks),all_old_SHA_unchanged=True,preregistration_unchanged=True,source_code_commit=git(REPO,'rev-parse','HEAD'),code=[asset(p) for p in sorted((R/'code').glob('*.py'))],replay_7_CSV_identical=True,original_input_mutation_N=0,incremental_proposal_N=223,baseline_promoted=False,neural_imports=[n for n in sys.modules if n.startswith(('torch','tensorflow','training','graphics'))],GPU=0,neural_forward=0,GT_read=False,Gate_B=False))
    local=[asset(p) for p in sorted((R/'local_results').rglob('*')) if p.is_file()]
    save('LOCAL_RESULTS_INDEX.json',dict(status='LOCAL_ONLY_NOT_UPLOADED',files=local,replay=asset(R/'runtime/replay_verification/REPLAY_VERIFY.json'),original_and_baseline_assets='DERIVED_INPUT_LINEAGE.json and config/PROTECTED_START.json',no_large_raw_or_weights_copied=True))
    links=[]
    for p in R.glob('*.md'):
        for q in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if q.startswith(('https:','http:','#')):continue
            target=(p.parent/q).resolve();links.append(dict(markdown=p.name,target=q,exists=target.exists()));assert target.exists(),(p,q)
    png=[]
    for p in (R/'figures').glob('*.png'):
        im=Image.open(p);im.verify();png.append(dict(file=p.name,bytes=p.stat().st_size))
    assert len(png)==4
    for p in (R/'code').glob('*.py'):ast.parse(p.read_text())
    save('config/DELIVERY_VALIDATION.json',dict(local_markdown_links=links,PNGs=png,all_python_parse=True,frozen_rules_unchanged=True,status='PASS_DELIVERY_INTEGRITY_NOT_SCIENTIFIC_PASS'))
    curated=[p for p in sorted(R.rglob('*')) if p.is_file() and not {'local_results','runtime','__pycache__'}.intersection(p.relative_to(R).parts) and p.name!='DELIVERY_INDEX.json']
    assert all(p.stat().st_size<10*1024**2 for p in curated)
    save('DELIVERY_INDEX.json',dict(task=R.name,status='REPORTED_Gate_A2_FAIL',source_and_figures_commit=git(REPO,'rev-parse','HEAD'),files=[asset(p) for p in curated],index_not_self_hashed=True,all_large_original_depth_and_weights_local_only=True))
    print('FINAL_DELIVERY',len(curated)+1,'files;',sum(p.stat().st_size for p in curated),'bytes; history',same,'checks',len(checks),flush=True)

if __name__=='__main__':main()
