"""Cohort authorization, A-priority resource checks, and existing-stage orchestration."""
import os
from pathlib import Path
import subprocess
import time


def authorized_cases(cohort):
    from .run import CASES
    from ring_first_3d.v6_raw.route import GROUPS
    if cohort=='pilot':return list(CASES)
    if cohort=='expanded':return [g+'_'+v for g in GROUPS for v in ['004','005']]
    raise ValueError('UNKNOWN_COHORT')


def inference_limit(cohort):
    if cohort=='pilot':return 8
    if cohort=='expanded':return 40
    raise ValueError('UNKNOWN_COHORT')


def active_priority_jobs(proc_root=Path('/proc'),own_pid=None):
    own_pid=os.getpid() if own_pid is None else own_pid
    found=[]
    for p in Path(proc_root).iterdir():
        if not p.name.isdigit() or int(p.name)==own_pid:continue
        try:args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
        except (OSError,PermissionError):continue
        if 'ring_first_3d.v6_raw.full_run' in args and any(x in args for x in ['run','worker']):
            found.append(dict(pid=int(p.name),command=' '.join(args).strip()))
    return found


def verify_s_cache(case):
    from .run import BASE,read,sha
    root=BASE/case/'S';r=read(root/'receipt.json')
    assert r['status'] in ['COMPLETED','NOT_EVALUABLE'],'PRIOR_S_FAILED_NEEDS_INSPECTION'
    for p,h in r['input_sha256'].items():assert sha(p)==h,'S_INPUT_DRIFT '+p
    for p,h in r['outputs_sha256'].items():assert sha(p)==h,'S_OUTPUT_DRIFT '+p
    return r


def batch(phase,cases=None):
    from .run import BASE,WT,PY,read,save,verify_common,sha
    cases=cases or authorized_cases('expanded')
    logroot=BASE/'logs_expanded';logroot.mkdir(parents=True,exist_ok=True)
    ledger=BASE/('EXPANSION_'+phase.upper()+'_STATUS.json')
    state=read(ledger) if ledger.exists() else dict(phase=phase,cases={},started_epoch=time.time())
    stages=['prepare','R','S','evaluate','poses','ring'] if phase=='cpu' else ['hero']
    for case in cases:
        print('EXPANSION_CASE',phase,case,flush=True)
        state['cases'][case]=dict(status='RUNNING',stages=[]);save(ledger,state)
        for stage in stages:
            root=BASE/case;reuse=False
            if stage=='S' and (root/'S/receipt.json').exists():verify_s_cache(case);reuse=True
            if stage=='evaluate' and (root/'CAMERA_RESULTS.json').exists():
                verify_common(case)
                for arm in ['R','S']:
                    r=read(root/arm/'receipt.json')
                    if arm=='R':assert sha(root/arm/'cameras.npz')==r['camera_sha256']
                    else:verify_s_cache(case)
                reuse=True
            if reuse:code=0
            else:
                cmd=[PY,str(WT/'tools/ring_sift_comparison.py'),'--cohort','expanded','--case',case,'--stage',stage]
                log=logroot/(case+'_'+stage+'.log')
                with log.open('a') as f:code=subprocess.call(cmd,cwd=WT,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
            state['cases'][case]['stages'].append(dict(stage=stage,returncode=code,reused=reuse))
            if code:
                state['cases'][case]['status']='FAILED_STAGE';state['cases'][case]['failed_stage']=stage;break
            save(ledger,state)
        else:state['cases'][case]['status']='COMPLETED'
        if phase=='hero':
            state['cases'][case]['arm_statuses']={a:read(BASE/case/a/'hero/RESULT.json')['status'] if (BASE/case/a/'hero/RESULT.json').exists() else 'NOT_EXECUTED' for a in ['R','S']}
            if any(s=='NOT_EXECUTED_GPU_BUSY' for s in state['cases'][case]['arm_statuses'].values()):state['cases'][case]['status']='QUEUED_A_PRIORITY'
        save(ledger,state)
    state['finished_epoch']=time.time();save(ledger,state)
    print('EXPANSION_BATCH_COMPLETE',phase,{k:v['status'] for k,v in state['cases'].items()},flush=True)
    return state
