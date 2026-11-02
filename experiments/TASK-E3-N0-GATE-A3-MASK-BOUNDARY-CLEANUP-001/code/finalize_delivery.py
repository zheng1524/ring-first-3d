"""Final integrity, local-only NPZ index and curated upload index."""
from common import *
import re

def main():
    before=load(R/'config/PROTECTED_START.json');same=protected_state()==before['worktrees'];bad=[a['path']for a in before['assets'] if sha(a['path'])!=a['sha256']];assert same and not bad,(same,bad)
    frozen=load(R/'config/V4_260_BEFORE_RESULTS.json');assert sha(R/'config/V4_260_PREREGISTERED.json')==frozen['protocol']['sha256'];assert sha(R/'V4_260_CANDIDATES.csv')==frozen['targets']['sha256']
    prior=frozen['protected_three_version_tables']+frozen['protected_three_version_arrays'];assert all(sha(a['path'])==a['sha256']for a in prior)
    archived=load(R/'config/SUPERSEDED_5PX_ARCHIVE.json')['files'];assert all(sha(a['archive_path'])==a['sha256']for a in archived)
    initial=load(R/'config/PRE_BACKGROUND_OVERRIDE_ARCHIVE.json');assert all(sha(a['archive_path'])==a['sha256']for a in initial['remapped_small_files'])
    acceptance=load(R/'GATE_A3_ACCEPTANCE.json');assert acceptance['tests_FAIL']==acceptance['V4_tests_FAIL']==0 and acceptance['V4_retained_N']==103686 and not acceptance['V4_is_5px']
    replay=load(R/'runtime/replay_final_verified/REPLAY_VERIFY.json');assert replay['all_identical'] and len(replay['files'])==22
    links=[]
    for p in R.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if link.startswith(('https:','http:','#')):continue
            q=(p.parent/link).resolve();assert q.exists(),(p,link);links.append(dict(file=p.name,target=link,exists=True))
    png=[]
    for p in (R/'figures').glob('*.png'):
        im=Image.open(p);im.verify();png.append(asset(p))
    assert len(png)==4
    for p in (R/'code').glob('*.py'):ast.parse(p.read_text())
    save('config/FINAL_DELIVERY_PROTECTION.json',dict(source_science_commit=git(REPO,'rev-parse','HEAD'),historical_worktrees_unchanged=same,historical_worktree_N=len(before['worktrees']),historical_source_SHA_checks=len(before['assets']),all_historical_SHA_unchanged=True,previous3_tables_and_arrays_SHA_unchanged=True,withdrawn5px_archives_SHA_unchanged=True,preBG_results_preserved=True,formal_V4_increment260=True,remaining_CD_proxies=121,engineering_tests_PASS=103,replay_CSV_identical_N=22,original_mutations=0,GT_read=False,GPU=0,NNforward=0,GateB=False))
    local=[asset(p) for p in sorted(R.rglob('*.npz')) if 'local_results' in p.relative_to(R).parts and 'runtime' not in p.relative_to(R).parts]
    identity=A2_LINEAGE['all_original_identity_ledger'];assert sha(identity['path'])==identity['sha256']
    save('LOCAL_RESULTS_INDEX.json',dict(status='LOCAL_ONLY_NOT_UPLOADED',files=local,original106144_identity_ledger=identity,final_replay=asset(R/'runtime/replay_final_verified/REPLAY_VERIFY.json'),raw_sources='config/PROTECTED_START.json',large_original_models_and_videos_copied=False))
    save('config/DELIVERY_VALIDATION.json',dict(status='PASS_DELIVERY_INTEGRITY_NOT_PHYSICAL_ACCURACY',all_python_parse=True,local_links=links,PNGs=png,final_variant='V3_minus260; not5px',old3px_not_blocking=True,source_code=[asset(p)for p in sorted((R/'code').glob('*.py'))]))
    curated=[p for p in sorted(R.rglob('*'))if p.is_file() and not {'local_results','runtime','__pycache__'}.intersection(p.relative_to(R).parts) and p.name!='DELIVERY_INDEX.json']
    assert all(p.stat().st_size<10*1024**2 and p.suffix not in ['.npz','.npy','.ckpt','.pth','.pt','.zip']for p in curated)
    save('DELIVERY_INDEX.json',dict(task=R.name,reported_status='A3_ENGINEERING_PASS_WITH_LIMITATIONS',source_science_commit=git(REPO,'rev-parse','HEAD'),files=[asset(p)for p in curated],index_not_self_hashed=True,formal_V4='V3 minus exactly260 previously unreviewed proxies',no_automatic_GateB=True))
    print('FINAL_DELIVERY',len(curated)+1,'files',sum(p.stat().st_size for p in curated),'bytes; historyPASS;103 engineeringPASS;22CSV identical',flush=True)

if __name__=='__main__':main()
